from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from galapagos.agent.llm_providers import OpenAICodexProvider
from galapagos.analysis.profile_comparison import build_profile_comparison
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.utils.paths import project_path


def _latest_report(pattern: str) -> str | None:
    reports = sorted(Path(project_path("reports/diagnostics")).glob(pattern))
    return str(reports[-1]) if reports else None


st.set_page_config(page_title="Projet Galapagos", layout="wide")
st.title("Projet Galapagos - Supervision V1.4")

profile = st.sidebar.selectbox("Profil", ["galapagos_30m", "galapagos_4h"])
database_path = st.sidebar.text_input("SQLite", str(project_path("data/paper/galapagos.sqlite")))
store = SQLiteStore(database_path)

decisions = [
    dict(row) for row in store.query("SELECT * FROM agent_decisions ORDER BY id DESC LIMIT 100")
]
trades = [
    dict(row) for row in store.query("SELECT * FROM paper_trades ORDER BY id DESC LIMIT 100")
]
positions = [
    json.loads(row["payload_json"])
    for row in store.query("SELECT payload_json FROM positions")
]
events = [dict(row) for row in store.query("SELECT * FROM system_events ORDER BY id DESC LIMIT 50")]
performance = [
    {**json.loads(row["payload_json"]), "timestamp_utc": row["timestamp_utc"]}
    for row in store.query("SELECT * FROM performance_snapshots ORDER BY id DESC LIMIT 200")
]
accounts = [dict(row) for row in store.query("SELECT * FROM paper_account ORDER BY profile")]
snapshots = [
    json.loads(row["payload_json"])
    for row in store.query("SELECT payload_json FROM market_snapshots ORDER BY id DESC LIMIT 20")
]

filtered_decisions = [row for row in decisions if row["profile"] == profile]
filtered_trades = [row for row in trades if row.get("profile") == profile]
filtered_positions = [row for row in positions if row.get("profile") == profile]
risk_rejects = [row for row in filtered_decisions if row.get("final_action") == "NO_TRADE"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Statut systeme", "OK" if not any(e["level"] == "ERROR" for e in events) else "ERROR")
col2.metric("Dernieres decisions", len(filtered_decisions))
col3.metric("Positions ouvertes", len(filtered_positions))
col4.metric("Risk rejects / NO_TRADE", len(risk_rejects))

fallback_count = sum(
    1
    for row in decisions
    if row.get("decision_validity") in {"parser_fallback", "provider_failure_fallback"}
)
fallback_text = (
    f"Taux fallback LLM: {fallback_count / len(decisions):.2%}"
    if decisions
    else "Taux fallback LLM: n/a"
)
st.caption(fallback_text)

st.subheader("Dernier cycle par profil")
latest_rows = []
for item in ["galapagos_30m", "galapagos_4h"]:
    rows = [row for row in decisions if row["profile"] == item]
    latest_rows.append(rows[0] if rows else {"profile": item, "timestamp_utc": None})
st.dataframe(pd.DataFrame(latest_rows), use_container_width=True)

st.subheader("Positions ouvertes")
st.dataframe(pd.DataFrame(filtered_positions), use_container_width=True)

st.subheader("Derniers trades fermes")
closed_trades = [trade for trade in filtered_trades if trade.get("status") == "CLOSED"]
st.dataframe(pd.DataFrame(closed_trades), use_container_width=True)

st.subheader("Decisions recentes")
st.dataframe(pd.DataFrame(filtered_decisions), use_container_width=True)

st.subheader("Risk rejects recents")
st.dataframe(pd.DataFrame(risk_rejects), use_container_width=True)

st.subheader("Comparaison 30m vs 4h")
comparison = build_profile_comparison(store)
st.dataframe(pd.DataFrame(comparison["rows"]), use_container_width=True)

st.subheader("Cash / equity par profil")
st.dataframe(pd.DataFrame(accounts), use_container_width=True)

st.subheader("Cash / equity")
if performance:
    perf_df = pd.DataFrame(performance)
    if "equity" in perf_df:
        st.plotly_chart(
            px.line(perf_df.sort_values("timestamp_utc"), x="timestamp_utc", y="equity"),
            use_container_width=True,
        )
else:
    st.info("Aucun snapshot de performance disponible.")

st.subheader("Statut donnees")
data_status = []
for snapshot in snapshots:
    derivatives = snapshot.get("derivatives", {})
    data_status.append(
        {
            "timestamp_utc": snapshot.get("timestamp_utc"),
            "profile": snapshot.get("profile"),
            "market_source": snapshot.get("market", {}).get("source"),
            "kraken": "available" if snapshot.get("market") else "missing",
            "binance_futures": derivatives.get("provider"),
            "funding": derivatives.get("funding", {}).get("status"),
            "open_interest": derivatives.get("open_interest", {}).get("status"),
        }
    )
st.dataframe(pd.DataFrame(data_status), use_container_width=True)

st.subheader("Readiness et derivees")
latest_snapshot = snapshots[0] if snapshots else {}
st.json(
    {
        "data_readiness_last_snapshot": {
            "data_mode": latest_snapshot.get("data_mode"),
            "freshness_seconds": latest_snapshot.get("data_freshness_seconds"),
            "unavailable_features": latest_snapshot.get("unavailable_features"),
            "derivatives": latest_snapshot.get("derivatives_availability_summary"),
        },
        "latest_derivatives_quality_report": _latest_report("derivatives_quality_*.md"),
        "latest_data_readiness_report": _latest_report("data_readiness_*.md"),
    }
)

st.subheader("Statut provider LLM")
st.json({"openai_codex": OpenAICodexProvider().status, "fallback_for_tests": "mock"})

st.subheader("Decisions LLM recentes")
st.dataframe(
    pd.DataFrame(
        [
            {
                "timestamp_utc": row.get("timestamp_utc"),
                "profile": row.get("profile"),
                "validity": row.get("decision_validity"),
                "final_action": row.get("final_action"),
                "reasoning_summary": row.get("reasoning_summary"),
            }
            for row in decisions[:25]
        ]
    ),
    use_container_width=True,
)

st.subheader("Backtests")
backtest_reports = sorted(Path(project_path("reports/backtests")).glob("backtest_*.json"))
if backtest_reports:
    latest_backtest = backtest_reports[-1]
    st.caption("Dernier rapport: " + str(latest_backtest))
    try:
        payload = json.loads(latest_backtest.read_text(encoding="utf-8"))
        st.dataframe(pd.DataFrame(payload.get("metrics", {})).T, use_container_width=True)
        st.json(payload.get("comparison", {}))
    except json.JSONDecodeError:
        st.warning("Rapport backtest JSON illisible.")
else:
    st.info("Aucun backtest genere. Ces rapports testent la mecanique, pas la profitabilite.")

st.subheader("LLM Offline")
llm_suite = Path(project_path("reports/backtests/llm_offline_suite_v1_7.json"))
llm_decisions = Path(project_path("reports/diagnostics/llm_offline_decisions_v1_7.json"))
if llm_suite.exists():
    payload = json.loads(llm_suite.read_text(encoding="utf-8"))
    st.caption("Derniere suite LLM offline: " + str(llm_suite))
    st.dataframe(pd.DataFrame(payload.get("policy_comparison", [])), use_container_width=True)
    rankings = payload.get("answers", {}).get("rankings", {})
    st.json({"best_composite_prudent_score": rankings.get("best_composite_prudent_score")})
else:
    st.info("Aucune suite LLM offline disponible.")
if llm_decisions.exists():
    st.caption("Dernier rapport decisions LLM offline: " + str(llm_decisions))
    decision_payload = json.loads(llm_decisions.read_text(encoding="utf-8"))
    st.json(decision_payload.get("decision_distribution_by_policy", {}))
st.warning(
    "Les policies LLM offline simulent le pipeline decisionnel; "
    "elles ne sont pas un vrai LLM."
)
