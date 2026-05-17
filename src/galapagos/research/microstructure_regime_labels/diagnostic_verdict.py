from __future__ import annotations

from .recommendation_engine import generate_recommendation

def determine_verdict(*args, **kwargs):
    return generate_recommendation(*args, **kwargs)
