from __future__ import annotations

QUESTIONS = [
    "l'agent perd-il surtout en range ?",
    "l'agent perd-il surtout en trend ?",
    "le profil 30m sur-trade-t-il ?",
    "le profil 4h rate-t-il trop d'opportunites ?",
    "quelle strategie perd le plus ?",
    "les frais detruisent-ils l'edge ?",
    "les stops sont-ils trop serres ?",
    "les take profits sont-ils trop proches ?",
    "les donnees derivees aident-elles ou bruitent-elles ?",
    "les decisions LLM refusees par risk_engine sont-elles frequentes ?",
]


def run_loss_autopsy(trades: list[dict], decisions: list[dict]) -> dict:
    losing = [trade for trade in trades if float(trade.get("pnl") or 0.0) < 0]
    rejected = [decision for decision in decisions if decision.get("final_action") == "NO_TRADE"]
    return {
        "questions": QUESTIONS,
        "losing_trade_count": len(losing),
        "rejected_decision_count": len(rejected),
        "notes": (
            "V1 exposes the diagnostics structure; deeper attribution needs more closed trades."
        ),
    }
