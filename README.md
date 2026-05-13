# Resolution-Proof-KRP-Seminar
A proof generator for propositional formulas using Resolution Calculus as a part of coursework for KRP seminar, spring 2026
# Requirements
We need to install sympy in order to be able to use it. The code was tested on sympy 1.14.0 & python 3.12.13. We can install sympy by:
```pip install sympy```

# How to use it
- The program takes two inputs, premise(formulas separated by commas) and a conclusion(single formula). We need to use | for disjunctions, & for conjunctions, ~ for negations, and >> for implications for any formula in either of the inputs.
- Variable names can only begin with letters but can contain underscores and numerals but no spaces in between
- Conclusion Cannot be Empty
# Usage Example
Example input: Premise: A >> B, A >> C, A >> D Conclusion: A>> D
Example Output for Proof:
-- Proof --
-   Premise : (~D)
-   Premise : (~C v D)
-   Resolving  (~D)  and  (~C v D)  on  D  to get  (~C)
-   Premise : (~A v C)
-   Premise : (A)
-   Resolving  (~A v C)  and  (A)  on  A  to get  (C)
-   Resolving  (~C)  and  (C)  on  C  to get  []
