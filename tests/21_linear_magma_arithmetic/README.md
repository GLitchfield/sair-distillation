# Test: Linear Magma Arithmetic Isolation

## Purpose
Test whether Haiku can reliably evaluate equations in new linear magmas before adding them to the cheatsheet. The linear magma scan found two promising new magmas:
- (2,2) mod 3: x*y = 2x+2y mod 3 = -(x+y) mod 3, catches 13 new hard3 FALSE problems
- (3,3) mod 5: x*y = 3x+3y mod 5, catches 13 new hard3 FALSE problems

If Haiku can't do the arithmetic reliably, adding these magmas to the battery won't help.

## Method
Give Haiku an isolated prompt: the magma operation table, one equation, and ask "does this hold for ALL assignments?" Compare to known ground truth from polynomial coefficient computation.

10 test cases: 4 each for the new magmas (2 should-hold, 2 should-fail), plus 2 easy controls.

## Results
*(to be filled after run completes)*
