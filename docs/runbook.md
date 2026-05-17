# Runbook

## Installer

```bash
uv venv
uv pip install -e ".[dev]"
```

## Lancer un cycle 30m

```bash
python scripts/run_cycle.py --profile 30m
```

## Lancer un cycle 4h

```bash
python scripts/run_cycle.py --profile 4h
```

## Utiliser les donnees reelles Kraken/Binance si accessibles

```bash
python scripts/run_cycle.py --profile 30m --real-data
```

## Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

## Rapports

```bash
python scripts/generate_report.py --profile 30m
python scripts/generate_report.py --summary
python scripts/run_daily_plan.py
python scripts/compare_profiles.py
python scripts/analyze_llm_decisions.py
python scripts/check_derivatives_data.py --symbol BTC/USDT:USDT
python scripts/check_data_readiness.py --profile 30m --real-data
python scripts/check_data_readiness.py --profile 4h --real-data
```

## Scheduler local

```bash
python scripts/run_scheduler.py --once
python scripts/run_scheduler.py --iterations 3 --sleep-seconds 5
python scripts/run_scheduler.py --profiles 30m,4h
python scripts/run_scheduler.py --real-data
python scripts/run_scheduler.py --once --mock-decision SHORT
python scripts/run_scheduler.py --once --mock-decision CLOSE
python scripts/run_cycle.py --profile 30m --mock-decision HOLD
python scripts/run_cycle.py --profile 30m --openai-codex
python scripts/run_forward_paper_test.py --profiles 30m,4h --iterations 3 --sleep-seconds 10 --real-data
python scripts/run_forward_paper_test.py --profiles 30m,4h --duration-minutes 60 --real-data
```

## Backtests / replay historique

```bash
python scripts/download_historical_ohlcv.py --profile 30m --days 30
python scripts/download_historical_ohlcv.py --profile 4h --days 180
python scripts/run_backtest.py --config configs/backtests/btc_30m_vs_4h_replay.yaml
python scripts/run_backtest.py --profile 30m --policy simple_momentum --days 30
python scripts/run_backtest.py --profile 4h --policy simple_momentum --days 180
```

## LLM offline pipeline

```bash
python scripts/run_llm_offline_suite.py --config configs/backtests/btc_llm_offline_vs_baselines.yaml
python scripts/analyze_llm_offline_decisions.py
```

Cette suite teste le chemin DecisionContext -> prompt -> raw JSON -> parser -> validation
contextuelle -> risk engine -> paper broker sans provider LLM reel. Elle ne prouve pas qu'un vrai
LLM sera profitable.

## Connexion openai-codex / GPT-5.5 low reasoning

Codex comme agent de developpement et le runtime LLM de Galapagos sont deux choses differentes.
Galapagos est un processus Python local : pour appeler `openai-codex`, il lui faut un bridge/gateway
HTTP compatible ou un provider expose explicitement au processus Python.

Configuration cible dans `configs/llm.yaml` :

- `provider: openai-codex`
- `model: gpt-5.5`
- `reasoning_effort: low`
- `temperature: 0.0`
- `endpoint_type: responses`
- `allow_network_calls: false` par defaut
- `base_url: null` tant qu'aucun bridge n'est fourni
- `auth_mode: chatgpt_codex` par defaut

Tant qu'aucun bridge local n'est disponible, le diagnostic doit indiquer `unavailable`. Ne pas
inventer d'URL ou de commande magique.

Commandes de diagnostic :

```bash
python scripts/test_llm_provider.py --provider mock
python scripts/test_llm_provider.py --provider openai-codex
python scripts/test_llm_provider.py --provider openai-codex --allow-network
python scripts/test_llm_provider.py --provider openai-codex --model gpt-5.5 --reasoning-effort low --allow-network
```

Pour activer un vrai appel plus tard, l'utilisateur devra fournir au minimum :

- `base_url` d'une gateway compatible ;
- `auth_mode` adapte (`local_gateway` ou `api_key`) ;
- eventuellement `api_key_env` si une cle est utilisee ;
- `allow_network_calls: true`.

Pour diagnostic, copier dans le prochain rapport :

- la sortie de `scripts/test_llm_provider.py --provider openai-codex` ;
- le statut `provider_status` ;
- la valeur non sensible de `base_url_configured` ;
- les erreurs sans secret.

## Experiences

```bash
python scripts/run_experiment.py --config configs/experiments/btc_30m_vs_4h.yaml --once
python scripts/run_experiment.py --config configs/experiments/btc_30m_vs_4h.yaml --iterations 3 --sleep-seconds 5
```

## Tests

```bash
pytest
uv run --extra dev ruff check .
```

## CodexCLIProvider

V1.8C ajoute un provider local `codex_cli` qui appelle Codex CLI via `subprocess`, sans cle API
classique et sans lire les tokens internes. Il utilise le compte ChatGPT/Codex deja connecte au
CLI.

Diagnostic sans appel reel :

```bash
python scripts/test_llm_provider.py --provider codex_cli
```

Diagnostic avec appel Codex CLI explicite :

```bash
python scripts/test_llm_provider.py --provider codex_cli --allow-codex-cli --model gpt-5.5 --reasoning-effort low
```

Sample backtest limite V1.8C :

```bash
python scripts/run_llm_sample_backtest.py --profile 4h --bars 5 --provider codex_cli --allow-codex-cli --max-llm-calls 5
python scripts/analyze_codex_cli_decisions.py
```

Contraintes : `--sandbox read-only`, timeout obligatoire, `--output-last-message`, JSON strict,
fallback `NO_TRADE`. Les tests automatiques ne doivent pas appeler le vrai CLI sans flag explicite.
Le CLI peut effectuer son propre appel reseau authentifie quand `--allow-codex-cli` est utilise.
Ce test valide l'integration, pas une profitabilite.

## Anti-overfit evaluation protocol

V1.9 ajoute un harnais d'evaluation anti-overfit pour eviter d'optimiser le prompt GPT-5.5 sur un
mini-run de 20 candidats. Le protocole separe les donnees 4h en fenetres temporelles distinctes :

- `calibration` : debug seulement, autorise pour inspection.
- `validation_1` et `validation_2` : evaluation intermediaire.
- `holdout` : test final intouchable. Ne pas modifier le prompt apres avoir lu ce resultat, sauf a
  creer un nouveau holdout.

Dry-run sans appel Codex CLI :

```bash
python scripts/run_anti_overfit_evaluation.py --config configs/evaluation/btc_4h_anti_overfit_v1_9.yaml --mode dry-run
```

Validation avec appels Codex CLI explicites, a lancer seulement apres validation manuelle :

```bash
python scripts/run_anti_overfit_evaluation.py --config configs/evaluation/btc_4h_anti_overfit_v1_9.yaml --mode calibration --allow-codex-cli
python scripts/run_anti_overfit_evaluation.py --config configs/evaluation/btc_4h_anti_overfit_v1_9.yaml --mode validation --allow-codex-cli
```

Holdout, a lancer une seule fois quand le prompt est fige :

```bash
python scripts/run_anti_overfit_evaluation.py --config configs/evaluation/btc_4h_anti_overfit_v1_9.yaml --mode holdout --allow-codex-cli
```

Le dry-run selectionne les fenetres et les candidats sans interroger GPT-5.5. Les rapports sont
ecrits dans `reports/evaluation/<evaluation_run_id>/`. Le mode holdout cree un fichier
`HOLDOUT_USED.txt` avec les hash de configuration/prompt et l'avertissement `Do not tune on this
result.`

Un resultat positif isole sur une fenetre ne prouve rien. Il faut regarder la stabilite entre
calibration, validations et holdout, les frais, le slippage, le drawdown et la dispersion du PnL.

## Etat paper

Le cash et les positions ouvertes sont conserves dans `data/paper/galapagos.sqlite`. Pour inspecter
l'etat courant :

```bash
python scripts/inspect_database.py
```

## Creer un zip propre

Depuis le dossier parent `projets` :

```bash
COPYFILE_DISABLE=1 zip -r projet-galapagos-v1.4-clean.zip projet-galapagos \
  -x "projet-galapagos/.DS_Store" \
  -x "projet-galapagos/.venv/*" \
  -x "projet-galapagos/**/__pycache__/*" \
  -x "projet-galapagos/**/*.pyc" \
  -x "projet-galapagos/**/.DS_Store" \
  -x "__MACOSX/*" \
  -x "projet-galapagos/data/paper/*.sqlite" \
  -x "projet-galapagos/data/**/*.db" \
  -x "projet-galapagos/reports/daily/*" \
  -x "projet-galapagos/reports/trades/*" \
  -x "projet-galapagos/reports/diagnostics/*"
```

Verifier que la sortie est vide :

```bash
zipinfo -1 projet-galapagos-v1.4-clean.zip | grep -E "\.venv|__pycache__|\.DS_Store|__MACOSX|\.sqlite|\.db"
```

## Decision cache V1.10.5

V1.10.5 active un cache decisionnel pour les evaluations Codex GPT. Le but n'est pas d'ameliorer
la strategie, mais de stabiliser les comparaisons : une variante deterministe doit pouvoir etre
rejouee sur les memes decisions GPT au lieu de rappeler Codex CLI et subir une nouvelle variance.

Cle de cache :

- `context_hash` ;
- `prompt_hash` ;
- `model` ;
- `reasoning_effort` ;
- `prompt_mode` ;
- `constraints_config_hash` ;
- `schema_version`.

Les entrees sont stockees dans `data/decision_cache/codex_cli/`, exclu du zip et du suivi Git. Elles
contiennent la reponse brute, la decision parse, les diagnostics parser/provider, la duree et les
previews stdout/stderr tronquees. Aucun secret n'est stocke.

Construire le cache sans holdout :

```bash
python scripts/build_decision_cache.py --config configs/evaluation/btc_4h_long_only_force_close_v1_10_1.yaml --windows calibration,validation_1,validation_2 --allow-codex-cli --max-calls 60
```

Rejouer sans rappeler GPT :

```bash
python scripts/replay_cached_decisions.py --config configs/evaluation/btc_4h_long_only_force_close_v1_10_1.yaml --windows calibration,validation_1,validation_2 --use-decision-cache --cache-readonly
```

Le holdout reste bloque par defaut. Ne prechauffer le holdout qu'avec une version figee, un flag
explicite, et un protocole qui interdit toute retouche apres lecture du resultat.
## V1.11 - protocole research offline

V1.11 ajoute un Signal Quality Lab. Il ne faut pas appeler Codex CLI, ne pas
executer le holdout et ne pas optimiser le prompt.

Commandes principales :

```bash
python scripts/run_v1_11_research_suite.py --profile 4h --windows calibration,validation_1,validation_2 --dry-run
python scripts/run_v1_11_research_suite.py --profile 4h --windows calibration,validation_1,validation_2
python scripts/check_derivatives_readiness.py --symbol BTCUSDT --dry-run
```

Le batch/resume futur s'appuie sur des checkpoints et sur le decision cache :
- ecrire chaque decision GPT dans le cache des obtention ;
- sauvegarder completed/pending/failures ;
- arreter proprement si quota atteint ;
- reprendre uniquement les pending ;
- garder `max_concurrency=1` par defaut.

Le holdout reste verrouille. Un resultat positif isole sur calibration ou
validation ne prouve pas une profitabilite.
