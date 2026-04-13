# Test: Vacuous FP Fix — Targeted A/B Test

## Purpose
Test whether adding explicit instruction against "vacuous truth" reasoning reduces false positives. 21 FPs in test 16 came from the model concluding "no battery magma satisfies EQ1 → vacuously true." This is wrong because EQ1 may have models outside our battery.

## Method
- Select 5 problems that consistently trigger the vacuous FP pattern (wrong in both test 15 and test 16)
- Run 20 iterations on each with the baseline cheatsheet (v19)
- Create a modified cheatsheet with an anti-vacuous instruction
- Run 20 iterations on each with the modified cheatsheet
- Compare accuracy and stability

## Test Problems
All are FALSE (EQ1 does NOT imply EQ2):
- hard3_0071: EQ1=x = y*(y*(y*(x*y))), EQ2=x = ((y*y)*x)*(z*z)
- hard3_0153: EQ1=x = x*(((y*z)*x)*y), EQ2=x*(y*x) = x*(z*z)
- hard3_0190: EQ1=x = (y*x)*((x*x)*y), EQ2=x*(y*z) = (x*z)*y
- hard3_0242: EQ1=x = ((y*z)*x)*(x*w), EQ2=x = ((x*x)*y)*(y*y)
- hard3_0270: EQ1=x = (y*((z*x)*x))*x, EQ2=x = ((x*(x*x))*y)*x

## Results
*(to be filled after runs complete)*
