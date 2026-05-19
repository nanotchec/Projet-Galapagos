# Projet Galapagos

## Etat actuel du projet

- Derniere version validee : V2.3.1.
- Candidate : V2.4.3, durcissement semantique des claims et runtime tests du validateur OHLCV.
- Le projet est actuellement data/research/offline only.
- Aucun trading reel n'est autorise.
- Aucun paper live n'est autorise.
- Aucun ordre n'est autorise.
- Aucun modele ML n'est valide.
- Les anciennes parties paper trading V1 sont legacy et ne sont pas autorisees dans la roadmap actuelle.

Projet Galapagos est une V1 verticale d'agent autonome de trading en paper trading sur BTC.
Le systeme collecte ou simule les donnees marche, prepare des indicateurs, construit un contexte,
demande une decision a un provider LLM abstrait, applique un moteur de risque deterministe, puis
journalise la decision et l'execution simulee.
La V1.4 ajoute la validation contextuelle des decisions LLM, des rapports readiness donnees,
un diagnostic derivees Binance Futures, un snapshot marche enrichi et un forward paper test local.

## Avertissement

Cette V1 est strictement paper trading. Elle ne peut pas passer d'ordre reel, ne demande aucune cle
privee d'exchange et la methode `create_order` du broker leve une exception.

## Installation

```bash
uv venv
uv pip install -e ".[dev]"
```

Sans `uv` :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Commandes

```bash
python scripts/run_cycle.py --profile 30m
python scripts/run_cycle.py --profile 4h
python scripts/run_cycle.py --profile 30m --mock-decision HOLD
python scripts/run_cycle.py --profile 30m --real-data
python scripts/run_scheduler.py --once --mock-decision SHORT
python scripts/run_experiment.py --config configs/experiments/btc_30m_vs_4h.yaml --once
python scripts/run_daily_plan.py
python scripts/generate_report.py --profile 30m
python scripts/analyze_llm_decisions.py
python scripts/check_derivatives_data.py --symbol BTC/USDT:USDT
python scripts/check_data_readiness.py --profile 30m --real-data
python scripts/run_forward_paper_test.py --profiles 30m,4h --iterations 3 --sleep-seconds 10 --real-data
python scripts/inspect_database.py
streamlit run dashboard/streamlit_app.py
pytest
```

## Structure

- `configs/` : profils, risque, sources, LLM.
- `src/galapagos/data/` : collecteurs Kraken/Binance Futures, normalisation, qualite.
- `src/galapagos/indicators/` : indicateurs techniques, volatilite, regime.
- `src/galapagos/strategies/` : familles de scenarios V1.
- `src/galapagos/agent/` : prompt, schema Pydantic, providers LLM.
- `src/galapagos/risk/` : risk engine et kill switch.
- `src/galapagos/execution/` : paper broker, frais, slippage.
- `src/galapagos/journal/` : SQLite.
- `src/galapagos/reports/` : rapports Markdown/JSON.
- `dashboard/` : Streamlit.
- `tests/` : suite pytest.

## Limites V1

Le provider `openai-codex` est configure comme interface OpenClaw-like. Il n'est pas appelable en
mode `chatgpt_codex` tant qu'un bridge Codex/ChatGPT n'est pas expose au processus Python local.
Le `MockLLMProvider` sert au developpement et aux tests. Les donnees derivees Binance Futures sont
exposees avec statut `unavailable` si elles ne sont pas accessibles.

Regle de sortie conservatrice : si stop-loss et take-profit sont touches dans la meme candle OHLCV,
Galapagos considere que le stop-loss est touche en premier, car l'ordre intrabar reel est inconnu.
