# Projet Galapagos

## Etat actuel du projet

- Derniere version validee : V6.2.
- Candidate : V6.3, audit de robustesse advanced OHLCV et falsification walk-forward.
- Fenetre historique validee : `2023-03-25` -> `2026-05-23`, `1156` jours.
- V6.3 utilise uniquement les artefacts valides V6.1/V6.2 et la reference V5.4 si disponible.
- V6.3 produit uniquement des diagnostics descriptifs, falsifiables et non actionnables.
- Aucun backtest n'est produit.
- Aucune strategie n'est produite.
- Aucun signal de trading n'est produit.
- Aucun ordre n'est produit.
- Aucun paper live n'est autorise.
- Aucun trading reel n'est autorise.
- Aucun modele persistant n'est produit.
- V6.3 reste `pending_external_audit` et n'est pas validee avant audit externe.
- Les anciennes parties paper trading V1 sont legacy et ne sont pas autorisees dans la roadmap research actuelle.

La roadmap active du projet Galapagos est actuellement une chaine research offline max historical sur BTCUSDT.
Les anciens modules V1 de paper trading restent legacy et ne sont pas autorises par les versions V5/V6 courantes.

## Avertissement

La roadmap active est strictement research offline. Elle ne peut pas passer d'ordre reel,
ne demande aucune cle privee d'exchange et ne produit aucun signal de trading.

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
python scripts/run_advanced_ohlcv_ml_robustness_v6_3.py
python scripts/validate_advanced_ohlcv_ml_robustness_v6_3.py
python -m pytest -q tests/ml/test_advanced_ohlcv_ml_robustness_v6_3.py
python -m pytest -q tests/validation/test_advanced_ohlcv_ml_robustness_v6_3_validator.py
python scripts/release_audit_lite_zip_v6_3.py
python scripts/audit_audit_lite_zip_v6_3.py --zip projet-galapagos-v6.3-audit-lite.zip
python scripts/smoke_audit_lite_zip_v6_3.py --zip projet-galapagos-v6.3-audit-lite.zip
python -m pytest --collect-only -q
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
