# Canonical Source Path Reconstruction - V1.35.1

This document summarizes the findings of the V1.35.1 diagnostic regarding the hardened reconstruction of the V1.32.4 selection path.

## Hardening measures
V1.35.1 introduces significant integrity improvements over V1.35:
1. **Removal of Fallback**: The artificial selection rule `predicted_probability > 0.65` has been removed.
2. **EV Proxy Rebuilder**: A dedicated rebuilder was implemented to reconstruct the actual `ev_calibrated_proxy` and `cost_proxy` columns on the prediction dataset.
3. **Strict Replay**: Counts are only calculated if the real EV-net selection logic can be executed.

## Findings
The results confirm whether the 12,691 trades reported in V1.32.4 can be reproduced using the *actual* EV-net filter rather than an approximation.

## Conclusion
The non-reproducibility driver analysis identifies why the exact count remains elusive even with a reconstructed EV proxy.

## Recommendation
Refer to `v1_35_1_recommendation.json` for specific next steps.
