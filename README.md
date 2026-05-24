# Projet Galapagos

## Etat actuel du projet

- Derniere version validee : V4.7.
- Candidate : V4.8, decision gate research 1 an et prochaine roadmap.
- Le projet est actuellement data/research/offline only.
- Aucun trading reel n'est autorise.
- Aucun paper live n'est autorise.
- Aucun ordre n'est autorise.
- V2.9.1 etend uniquement les donnees marche publiques BTCUSDT sur 7 jours.
- V3.0 construit uniquement des features OHLCV causales multi-day dans `data/research/v3_0/features/ohlcv`.
- V3.1 construit uniquement des labels forward multi-day dans `data/research/v3_1/labels/forward_returns`.
- V3.2 assemble uniquement un dataset supervise offline multi-day dans `data/research/v3_2/datasets/offline_supervised`.
- V3.3 produit uniquement des baselines ML offline et des scores `research_*`.
- V3.4 audite uniquement la robustesse descriptive et la falsification des baselines ML V3.3.
- V3.5 etend uniquement les donnees marche publiques BTCUSDT sur 90 jours dans `data/research/v3_5/silver/ohlcv`.
- V3.6 construit uniquement des features OHLCV causales 90 jours dans `data/research/v3_6/features/ohlcv`.
- V3.7 construit uniquement des labels forward 90 jours separes dans `data/research/v3_7/labels/forward_returns`.
- V3.8 assemble uniquement un dataset supervise offline 90 jours dans `data/research/v3_8/datasets/offline_supervised`.
- V3.9 entraine uniquement des baselines ML offline simples et produit des scores de recherche `research_*` dans `data/research/v3_9/ml/offline_research`.
- V4.0 audite uniquement la robustesse descriptive et la falsification des resultats ML offline V3.9.
- V4.0 ne produit aucun modele persistant, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.0.1 corrige uniquement le packaging audit-lite V4.0 pour inclure les packages source features et labels requis par l'audit.
- V4.0.2 corrige uniquement le packaging audit-lite V4.0 pour exclure explicitement `__pycache__`, `*.pyc` et `*.pyo`.
- V4.1 produit uniquement un rapport de decision research et recommande l'extension a 1 an avant toute suite.
- V4.1 est validee par audit externe.
- V4.2 etend uniquement les donnees marche publiques BTCUSDT sur la fenetre `2024-01-01` a `2024-12-31` dans `data/research/v4_2/silver/ohlcv`.
- V4.2 produit les row counts attendus `1m=527040`, `5m=105408`, `15m=35136`, `1h=8784`.
- V4.2 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.2 est validee par audit externe.
- V4.3 construit uniquement des features OHLCV causales 1 an dans `data/research/v4_3/features/ohlcv`.
- V4.3 respecte `FEATURE_COLUMNS_V4_3` avec les row counts `1m=527040`, `5m=105408`, `15m=35136`, `1h=8784`.
- V4.3 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.3 est validee par audit externe.
- V4.4 construit uniquement des labels forward 1 an separes dans `data/research/v4_4/labels/forward_returns`.
- V4.4 respecte `LABEL_COLUMNS_V4_4` avec les row counts `1m=527040`, `5m=105408`, `15m=35136`, `1h=8784`.
- V4.4 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.4 est validee par audit externe.
- V4.5 assemble uniquement un dataset supervise offline 1 an dans `data/research/v4_5/datasets/offline_supervised`.
- V4.5 respecte `DATASET_COLUMNS_V4_5` avec les row counts `1m=527040`, `5m=105408`, `15m=35136`, `1h=8784`.
- V4.5 ne produit aucun ML, aucun modele ML, aucun score ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.5 est validee par audit externe.
- V4.6 entraine uniquement des baselines ML offline simples dans `data/research/v4_6/ml/offline_research`.
- V4.6 produit uniquement des scores de recherche `research_*` et des metriques descriptives.
- V4.6 ne produit aucun modele persistant, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.6 est validee par audit externe.
- V4.7 audite uniquement la robustesse descriptive et la falsification des resultats ML offline V4.6.
- V4.7 ne produit aucun modele persistant, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.7 est validee par audit externe.
- V4.8 produit uniquement un rapport de decision research et recommande l'extension a l'historique max OHLCV avec validation walk-forward offline secondaire.
- V4.8 ne produit aucune nouvelle donnee, aucun modele, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
- V4.8 reste `pending_external_audit` et n'est pas validee avant audit externe.
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
