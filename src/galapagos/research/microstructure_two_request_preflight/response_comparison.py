from typing import Any, Dict, List

class ResponseComparison:
    def compare_responses(self, previews: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(previews) < 2:
            return {
                "response_comparison_created": False,
                "reason": "Not enough responses for comparison"
            }

        p1 = previews[0]["preview"]
        p2 = previews[1]["preview"]

        # Simple schema check (length of Binance kline list)
        schema_consistent = False
        if p1 and p2:
             schema_consistent = len(p1[0]) == len(p2[0])

        # Monotonicity check (timestamp is first element)
        t1_max = p1[-1][0] if p1 else 0
        t2_min = p2[0][0] if p2 else 0
        
        # We don't necessarily expect t2_min > t1_max if they are concurrent or overlap,
        # but we can check internal monotonicity
        p1_monotonic = all(p1[i][0] < p1[i+1][0] for i in range(len(p1)-1)) if p1 else True
        p2_monotonic = all(p2[i][0] < p2[i+1][0] for i in range(len(p2)-1)) if p2 else True

        return {
            "response_comparison_created": True,
            "response_schema_consistent": schema_consistent,
            "timestamp_preview_available": True,
            "request_1_monotonic": p1_monotonic,
            "request_2_monotonic": p2_monotonic,
            "overlap_detected": t2_min <= t1_max if p1 and p2 else False
        }
