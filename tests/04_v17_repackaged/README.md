# Test: v17 -- Repackaged v13a with Prompting Guide Improvements

## Purpose

Take v13a's proven content (best performer on hard3) and repackage it with validated prompting guide improvements from v15/v16 testing. Specifically: full output format examples, flat step structure, Jinja2 template format, and format reminder. Crucially, NO new heuristic rules were added -- this is purely a presentation/format change.

## Cheatsheets Used

- **cheatsheet_v17.txt** -- 6,922 bytes, Jinja2 format. Included in this folder.

### Key Design Decisions

- Magma letters were renamed A-L sequentially (previously had gaps/non-sequential naming)
- Uses Jinja2 template syntax ({{ equation1 }}, {{ equation2 }})
- Flat step numbering (no sub-steps)
- Full worked examples for both TRUE and FALSE cases
- Format reminder at end of prompt
- Under 10KB limit
- v13a's core magma battery and decision logic preserved exactly

## Datasets

- **hard3_400**: 400 problems from the hard3 dataset

## Results

### Hard3 400

| Version | Accuracy | F1 Score | Unparsed |
|---------|----------|----------|----------|
| v17 | **63.5%** | 0.628 | 11 |
| v13a rerun | 63.2% | 0.693 | -- |
| v13a original | 65.2% | -- | -- |

- v17: 63.5% accuracy, F1=0.628, with 11 unparsed responses (token exhaustion during Step 4 proof attempts)
- v13a rerun: 63.2% accuracy, F1=0.693, but with a very different error profile from the original run (118 FPs vs 65 originally)

### Reproducibility Finding

v13a's original 65.2% was **not reproducible**. The rerun scored 63.2% with a substantially different error distribution:
- Original: 65 FPs
- Rerun: 118 FPs
- This demonstrates high run-to-run variance in Haiku's behavior

## Conclusions

1. **v17 roughly matches v13a rerun on accuracy** (63.5% vs 63.2%). The repackaging neither helped nor hurt significantly.
2. **The prompting guide format improvements are cosmetic** for hard3 performance -- they help compliance and readability but do not change the fundamental accuracy.
3. **v13a's original 65.2% was not reproducible** -- run-to-run variance is substantial (2+ percentage points). This means small differences between versions may be noise.
4. **Token exhaustion is a concern**: 11 unparsed responses in v17 from Haiku running out of tokens during Step 4 proof attempts. This suggests the full worked examples may encourage Haiku to be too verbose.
5. **The core insight**: the cheatsheet's magma battery and decision logic matter far more than the presentation format. v13a and v17 have essentially the same content and get essentially the same results.
