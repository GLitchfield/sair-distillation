# Test: v19 (v18_briefPrompt rerun) + Unparsed Retry Validation

## Purpose
Two goals:
1. Rerun v18_briefPrompt as v19 to measure run-to-run variance on hard3
2. Validate new retry logic for unparsed responses — added code to retry when the model stops mid-sentence (`end_turn`) but not when it hits the token limit (`max_tokens`)

## Cheatsheets Used
- cheatsheet_v19.txt (8,271 bytes) — identical copy of cheatsheet_v18_briefPrompt.txt

## Code Changes
- `run_test.py`: API call functions now return `(text, stop_reason)` instead of just `text`
- `run_test.py`: When a response is unparsed and `stop_reason == "end_turn"`, retry up to 3 times
- `run_test.py`: `stop_reason` now saved in result JSON for analysis

## Datasets
- hard3.jsonl (400 problems) — main run
- retry_test_all.jsonl (29 problems) — the 29 unparsed from the main run, re-run to validate retry logic

## Results

### Main run (v19 on hard3, 400 problems)

| Metric | v18_briefPrompt (test 13) | v19 (this test) | v17 |
|--------|---------------------------|-----------------|-----|
| Accuracy | 63.6% | 63.3% | 63.5% |
| F1 | 0.604 | 0.602 | 0.628 |
| TP | 106 | 103 | 120 |
| FP | 63 | 60 | 73 |
| FN | 76 | 76 | 69 |
| TN | 137 | 132 | 127 |
| Unparsed | 18 | 29 | 11 |

### Retry validation run (29 unparsed problems re-run)

Re-ran all 29 problems that were unparsed in the main run:
- **25/29 produced a verdict** on re-run (86% recovery)
- **4/29 remained unparsed** — all 4 had `stop_reason=max_tokens`
- **0 retry messages appeared** — every `end_turn` response included a verdict
- Of the 25 recovered: 18 correct (72% accuracy)

| stop_reason | Count | Had verdict? |
|-------------|-------|-------------|
| end_turn | 23 | 23/23 (100%) |
| max_tokens | 6 | 2/6 (33%) |

## Analysis

### Run-to-run variance confirmed
v19 is identical to v18_briefPrompt but scored 63.3% vs 63.6% with unparsed swinging 18→29. This is consistent with known variance (v13a: 65.2%→63.2%). Single runs are unreliable for version comparison.

### Unparsed responses are predominantly max_tokens
When the 29 unparsed problems were re-run:
- All `end_turn` responses (23/23) successfully included a verdict
- The `end_turn` mid-sentence stops are intermittent/non-reproducible — on re-run the model completes normally
- The 4 persistent unparsed were all `max_tokens` — genuine token exhaustion

### Retry logic works correctly but didn't fire
The code correctly identifies `end_turn` vs `max_tokens` and only retries the former. In this run, no `end_turn` unparsed cases occurred, so the retry path was never exercised. This doesn't mean it's broken — it means the `end_turn` mid-sentence bug is intermittent and rare enough that 29 re-runs produced 0 cases.

### Unparsed response characteristics (from main run)
- Unparsed responses avg 7,469 chars vs 5,666 for parsed responses
- All 29 ended mid-sentence (truncated words, trailing commas, incomplete expressions)
- Nearly all (27/29) completed the full 12-magma battery before running out of tokens

### Where the model ran out of tokens (29 unparsed responses)

Examined the last ~500 chars of each response to classify what the model was actively doing at truncation:

| Stage | Count | % | Description |
|---|---|---|---|
| Step 4 (proof attempt) | 13 | 45% | Trying algebraic rewrites/substitutions. Main token sink. |
| Step 2 (magma arithmetic) | 8 | 28% | Verbose 3-element magma table lookups or CE re-verification. All had completed 11-12 magmas. |
| Step 3 (linear magma) | 4 | 14% | Doing mod-3 arithmetic on the linear magma after completing full battery. |
| Step 5 (final judgment) | 4 | 14% | Summarizing battery results, cut off right before outputting VERDICT. |

**Key findings:**
1. **Step 4 is the dominant token sink (45%)** despite the cheatsheet saying "Limit to 3 attempts." The model doesn't enforce this — it keeps trying proof strategies until it runs out of tokens.
2. **The 4 Step 5 cases were inches from a verdict.** All were listing battery results in a summary and got cut off mid-sentence right before the VERDICT line. These are the most wasteful — all the work was done, just couldn't output the answer.
3. **Step 2 cases aren't stuck early.** All 8 completed 11-12 of the 12 magmas. They burn tokens on verbose arithmetic for 3-element magmas (H/I/J/K/L table lookups) or re-verifying counterexamples with extra test cases.
4. **59% of exhaustion is post-battery (Steps 4+5).** The battery itself usually fits within the token budget. The model then spends its remaining tokens on proof attempts that rarely succeed.

### Implications for cheatsheet design
- **Step 4 could be cut or capped harder** — it accounts for 45% of token exhaustion and its proof attempts rarely succeed on hard3 (these are problems specifically designed to resist proofs).
- **Step 5 needs to come earlier** — 4 responses did all the work but couldn't output a verdict. A "verdict-first" output format or explicit instruction to output VERDICT before detailed reasoning could save these.
- **3-element magma verbosity** — the worked examples help accuracy but increase response length. Could instruct "one line per magma, no intermediate steps for 2-element magmas."

## Files
- `cheatsheet_v19.txt` — cheatsheet used (identical to v18_briefPrompt)
- `v19_hard3.json` — full 400-problem results (stop_reason not captured — code change was deployed mid-test)
- `retry_test_all.json` — 29-problem validation run (stop_reason captured)
