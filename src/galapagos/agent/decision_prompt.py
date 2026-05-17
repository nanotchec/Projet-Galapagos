import json

SYSTEM_PROMPT = """You are Galapagos, an autonomous paper-trading decision agent.

Rules:
- You must never invent market data.
- Use only the structured context provided by tools.
- Choose exactly one allowed decision: LONG, SHORT, CLOSE, HOLD, NO_TRADE.
- Respond with strict JSON only, without Markdown.
- Prefer NO_TRADE when the edge is unclear, data is contradictory, or derivatives data
  is missing and critical.
- Mention critical_data_used explicitly.
- Respect the supplied profile and horizon.
- Account for market regime, volatility, funding, open interest, liquidations,
  long/short ratio, and basis when available.
- Never request, imply, or prepare a real order. This system is paper trading only.
- LONG and SHORT decisions must include stop_loss and either take_profit or max_duration_minutes.
"""


def build_decision_prompt(context: dict) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Evaluate this prepared trading context and return only the strict JSON decision:\n"
                f"{context}"
            ),
        },
    ]


def build_llm_decision_prompt(context, prompt_mode: str = "conservative") -> str:
    context_payload = context.to_dict() if hasattr(context, "to_dict") else context
    context_json = json.dumps(
        context_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    mode_rules = _prompt_mode_rules(prompt_mode)
    return (
        "CRITICAL OUTPUT RULE:\n"
        "Return exactly one valid JSON object.\n"
        "Do not use markdown.\n"
        "Do not wrap in code fences.\n"
        "Do not add comments.\n"
        "Do not add text before or after the JSON.\n\n"
        "Expected JSON schema fields (minimal JSON schema keys):\n"
        "decision, profile, asset, strategy, confidence, reasoning_summary, horizon, "
        "reference_entry_price, stop_loss, take_profit, risk_fraction, max_duration_minutes, "
        "invalidation_conditions, critical_data_used, setup_quality, setup_quality_score, "
        "why_not_no_trade.\n\n"
        "Core rules:\n"
        "- paper trading only. Never request or prepare real execution.\n"
        "- Do not call tools. Do not modify files.\n"
        "- You are using a read-only sandboxed provider bridge.\n"
        "- Use only Decision context JSON. Never invent unavailable data.\n"
        "- NO_TRADE if edge is unclear.\n"
        "- Respect open position state.\n"
        "- LONG/SHORT require reference_entry_price, stop_loss, and take_profit or "
        "max_duration_minutes.\n"
        "- For NO_TRADE, HOLD, CLOSE: risk_fraction=0.0 and max_duration_minutes=0.\n"
        "- Cost awareness: consider estimated fees, slippage, round-trip cost, and minimum "
        "expected move to break even before validating active trades.\n"
        f"Prompt mode: {prompt_mode}.\n{mode_rules}\n\n"
        f"Decision context JSON:\n{context_json}"
    )


def _prompt_mode_rules(prompt_mode: str) -> str:
    if prompt_mode == "setup_review":
        return (
            "Setup review mode rules:\n"
            "- Review only candidate_setup. Do not search for another trade.\n"
            "- If candidate_setup is poor or unclear: decision=NO_TRADE.\n"
            "- If no open position: LONG/SHORT may validate candidate_setup.\n"
            "- If derivatives are unavailable: reduce confidence; do not invent them.\n"
            "\nPosition state rules:\n"
            "- If portfolio.has_open_position=true: LONG/SHORT are forbidden.\n"
            "- If position thesis remains valid: HOLD.\n"
            "- If candidate strongly invalidates position: CLOSE.\n"
            "- If candidate does not concern current position: NO_TRADE.\n"
            "- You may propose LONG or SHORT only when portfolio.has_open_position is false.\n"
            "\nRequired critical_data_used for active decisions:\n"
            "For LONG/SHORT, critical_data_used MUST include exactly these available keys at "
            "minimum: ['price', 'volatility', 'trend_short', 'trend_long', 'candidate_setup'].\n"
            "Include 'market_regime' if available.\n"
            "If price or volatility are not available: NO_TRADE.\n"
            "Do not include funding/open_interest unless available_critical_data says true.\n"
            "\nSTRICT ENUM RULES:\n"
            "- setup_quality MUST be exactly one of: \"poor\", \"acceptable\", "
            "\"good\", \"excellent\".\n"
            "- Do NOT output values like: \"medium\", \"moderate\", \"unclear\", "
            "\"poor_unclear_edge\", \"acceptable_but_derivatives_unavailable\", or any "
            "other custom label.\n"
            "- If the setup is unclear, use \"poor\".\n"
            "- If derivatives are unavailable but the technical setup is still usable, "
            "use \"acceptable\".\n"
            "- If you are not sure, use \"poor\".\n"
            "- decision MUST be exactly one of: \"LONG\", \"SHORT\", \"CLOSE\", "
            "\"HOLD\", \"NO_TRADE\".\n"
            "- strategy MUST be exactly one of: \"no_trade\", \"breakout\", "
            "\"momentum\", \"mean_reversion\", \"derivatives_signal\", "
            "\"volatility_regime\", \"risk_reduction\", \"close_position\".\n"
            "- critical_data_used MUST be a list of these strings only: \"price\", "
            "\"volume\", \"volatility\", \"trend_short\", \"trend_long\", "
            "\"market_regime\", \"candidate_setup\", \"funding\", \"open_interest\", "
            "\"liquidations\", \"long_short_ratio\", \"basis\".\n"
            "\nJSON TEMPLATE:\n"
            "Return exactly this structure. Replace values only. Do not add extra fields. "
            "Do not remove fields.\n"
            "{\n"
            "  \"decision\": \"NO_TRADE\",\n"
            "  \"profile\": \"galapagos_4h\",\n"
            "  \"asset\": \"BTC/USD\",\n"
            "  \"strategy\": \"no_trade\",\n"
            "  \"confidence\": 0.50,\n"
            "  \"setup_quality\": \"poor\",\n"
            "  \"setup_quality_score\": 0.20,\n"
            "  \"why_not_no_trade\": null,\n"
            "  \"reasoning_summary\": \"Setup rejected because the edge is unclear.\",\n"
            "  \"horizon\": \"4h\",\n"
            "  \"reference_entry_price\": null,\n"
            "  \"stop_loss\": null,\n"
            "  \"take_profit\": null,\n"
            "  \"risk_fraction\": 0.0,\n"
            "  \"max_duration_minutes\": 0,\n"
            "  \"invalidation_conditions\": [],\n"
            "  \"critical_data_used\": []\n"
            "}\n"
        )
    if prompt_mode == "balanced":
        return (
            "Balanced mode rules:\n"
            "- Stay prudent and avoid overtrading.\n"
            "- Derivatives unavailable must not automatically block a trade if multiple technical "
            "signals are aligned and the risk/reward is clear.\n"
            "- Explicitly evaluate setup_quality as poor, acceptable, good, or excellent.\n"
            "- Explicitly fill why_not_no_trade for LONG/SHORT/CLOSE decisions.\n"
            "- If setup_quality is poor, NO_TRADE is mandatory.\n"
            "- If setup_quality is acceptable, LONG/SHORT is allowed only with low risk_fraction.\n"
            "- If setup_quality is good or excellent, risk_fraction may be moderate but must "
            "remain within the supplied risk constraints.\n"
            "- If derivatives are unavailable and you still choose LONG/SHORT, reasoning_summary "
            "must explain why technical signals compensate for missing derivatives.\n"
        )
    return (
        "Conservative mode rules:\n"
        "- Keep the current strict behavior.\n"
        "- NO_TRADE is preferable to a mediocre trade.\n"
        "- Act only if signals are very clear.\n"
        "- Reduce aggressiveness when derivatives are unavailable.\n"
        "- Use setup_quality poor unless the setup is clearly high quality.\n"
    )
