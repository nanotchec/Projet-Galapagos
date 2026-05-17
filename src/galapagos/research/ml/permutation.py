"""Permutation testing for ML evaluation."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.base import clone
from sklearn.metrics import accuracy_score


def run_permutation_test(
    model: Any,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    n_permutations: int = 200,
    seed: int = 42,
) -> dict[str, Any]:
    """Test if model beats chance by permuting training labels."""
    if len(x_train) == 0 or len(x_test) == 0:
        return {"status": "insufficient_data"}
        
    rng = np.random.RandomState(seed)
    
    # Base score
    try:
        model.fit(x_train, y_train)
        real_pred = model.predict(x_test)
        real_score = accuracy_score(y_test, real_pred)
    except Exception as e:  # noqa: BLE001
        return {"status": "fit_error", "error": str(e)}
        
    perm_scores = []
    
    # We clone the model to avoid state bleed
    for _ in range(n_permutations):
        try:
            m_clone = clone(model)
        except Exception:  # noqa: BLE001
            m_clone = model  # fallback if not sklearn clonable
            
        y_train_perm = rng.permutation(y_train)
        try:
            m_clone.fit(x_train, y_train_perm)
            p_pred = m_clone.predict(x_test)
            p_score = accuracy_score(y_test, p_pred)
            perm_scores.append(p_score)
        except Exception:  # noqa: BLE001
            pass
            
    if not perm_scores:
        return {"status": "permutation_failed"}
        
    p_value = float(np.mean([s >= real_score for s in perm_scores]))
    
    return {
        "status": "computed",
        "n_permutations": len(perm_scores),
        "real_score": float(real_score),
        "permutation_mean": float(np.mean(perm_scores)),
        "permutation_std": float(np.std(perm_scores)),
        "p_value_approx": p_value,
        "percentile": float(np.mean([s <= real_score for s in perm_scores]) * 100),
        "verdict": "ML_FAILS_PERMUTATION_TEST" if p_value > 0.05 else "ML_PASSES_PERMUTATION_TEST",
    }
