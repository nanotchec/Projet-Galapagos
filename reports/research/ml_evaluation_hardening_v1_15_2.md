# ML Evaluation Hardening V1.15.2

Final Verdict: ML_REGIME_DEPENDENT_WEAK_EDGE.
Leakage Audit: ML_LEAKAGE_AUDIT_PASSED.
LLM reviewer ready: False.

## Window Breakdown
| Window | Permutation p-value | Perm Passed | Top Bucket Net Return | Beats Alpha |
| :--- | :--- | :--- | :--- | :--- |
| train_2022_2023 | 0.04 | True | 0.0108 | True |
| train_2022_2024 | 0.95 | False | 0.0025 | True |
| train_2022_2025 | 0.99 | False | -0.0243 | False |

Si LLM reviewer ready est faux, le signal n'est pas robuste sur plusieurs fenetres.