# Galapagos — rapport de reprise pour handoff
## 1. Version courante détectée
- Version courante/candidate detectee : `V9.0_to_V9.3.1`.
- Derniere version validee : `V8.9.1`.
- Statut : `pending_external_audit`.
- Branche Git : `main`.
- Git status initial : `## main...origin/main [ahead 2]`.
- Dernier commit local : `56b0f33d`.
- Derniere archive audit-lite : `projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip`.

## 2. Résumé exécutif
Le repo est dans un etat de reprise exploitable. `V8.9.1` est la derniere version validee par audit externe selon l'etat projet. La candidate courante `V9.0_to_V9.3.1` est une correction de packaging audit-lite groupe, pas une evolution metier : les resultats V9.0/V9.1/V9.2/V9.3 sont conserves et restent `pending_external_audit`.

Les commandes safe relancees pendant ce handoff passent : collect-only, audit ZIP et smoke ZIP V9.0-to-V9.3.1. Aucun trading, ordre, endpoint prive ou secret n'a ete utilise. La prochaine action recommandee est l'audit externe strict du ZIP V9.0-to-V9.3.1, pas une nouvelle version fonctionnelle.

## 3. Chronologie des versions importantes
### V1.x
- Objectif : Socle agent, paper broker, risk engine, journaux, backtests historiques et nombreux audits de securite/recherche.
- Statut repo : `present`.
- Artefacts presents : `reports/REPORT_INDEX.md`, `src/galapagos/execution/paper_broker.py`, `src/galapagos/risk/risk_engine.py`.
- Tests associes : `tests/test_no_real_trading.py`.
- Limites/reserves : Historique tres volumineux; plusieurs rapports backtest anciens sont references mais non actifs dans le scope courant.

### V1.8C.1
- Objectif : Ajout/diagnostic provider Codex CLI local et analyses de decisions; pas d ordre reel.
- Statut repo : `present`.
- Artefacts presents : `reports/diagnostics/codex_cli_decisions_v1_8C_1.json`, `reports/diagnostics/codex_cli_decisions_v1_8C_1.md`, `src/galapagos/reports/codex_cli_report.py`.
- Tests associes : `tests/test_llm_provider_and_parser_v13.py`.
- Limites/reserves : Traces surtout diagnostiques; versions V1.8C multiples presentes.

### V2.3
- Objectif : Ingestion OHLCV publique Binance BTCUSDT de base.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/public_market_ingestion_v2_3_manifest.json`, `docs/public_market_ingestion_v2_3.md`.
- Tests associes : `tests/data/test_public_market_ingestion_v2_3.py`.
- Limites/reserves : Ancien socle public read-only.

### V5.x / V5.6.1
- Objectif : Fenetre OHLCV historique maximale, labels V5.2, dataset/ML/robustesse et gate V5.6.1.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/max_history_public_market_data_v5_0_manifest.json`, `reports/manifests/max_history_label_factory_v5_2_manifest.json`, `reports/research_decisions/v5_6_research_decision_gate.json`, `reports/audit_lite/v5_6_1_full_local_validation_attestation.json`.
- Tests associes : `tests/validation/test_max_history_label_factory_v5_2_validator.py`.
- Limites/reserves : V5.0/V5.2 restent des sources d entree majeures pour V8/V9.

### V6.x
- Objectif : Feature set OHLCV avance, dataset, ML offline, robustesse et decision gate.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/advanced_ohlcv_feature_store_v6_0_manifest.json`, `reports/manifests/advanced_ohlcv_offline_ml_research_v6_2_manifest.json`, `reports/research_decisions/v6_4_research_decision_gate.json`.
- Tests associes : `tests/validation/test_research_decision_gate_v6_4.py`.
- Limites/reserves : Reference descriptive; non directement comparable aux fenetres trades.

### V7.x
- Objectif : Introduction trades publics aggTrades 30/90 jours, features OHLCV+trades, dataset, ML et robustesse 90 jours.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/public_trades_90d_window_v7_7_manifest.json`, `reports/manifests/ohlcv_trades_90d_feature_store_v7_8_manifest.json`, `reports/manifests/ohlcv_trades_90d_offline_supervised_dataset_v7_9_manifest.json`.
- Tests associes : `tests/data/test_public_trades_90d_window_v7_7.py`.
- Limites/reserves : A conduit a la decision d etendre les aggTrades a un an.

### V8.2
- Objectif : Ingestion Binance public archive aggTrades BTCUSDT spot sur 366 jours.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/public_trades_1y_window_v8_2_manifest.json`, `reports/audit_lite/v8_2_full_local_validation_attestation.json`.
- Tests associes : `tests/data/test_public_trades_1y_window_v8_2.py`, `tests/validation/test_public_trades_1y_window_v8_2_validator.py`.
- Limites/reserves : Data-only; aucun feature/label/ML/backtest.

### V8.3
- Objectif : Feature store causale OHLCV V5.0 + aggTrades V8.2 sur un an.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json`, `reports/features/ohlcv_trades_1y_feature_store_v8_3.json`.
- Tests associes : `tests/features/test_ohlcv_trades_1y_features_v8_3.py`.
- Limites/reserves : Features uniquement; aucun label/ML/backtest.

### V8.4
- Objectif : Dataset supervise offline multi-source OHLCV+trades avec labels V5.2 filtres.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/ohlcv_trades_1y_offline_supervised_dataset_v8_4_manifest.json`, `reports/datasets/ohlcv_trades_1y_offline_supervised_dataset_v8_4.json`.
- Tests associes : `tests/datasets/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py`.
- Limites/reserves : Dataset offline; pas de modele ni backtest.

### V8.5
- Objectif : Baselines ML offline static split sur dataset V8.4.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json`, `reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json`.
- Tests associes : `tests/ml/test_ohlcv_trades_1y_offline_ml_research_v8_5.py`.
- Limites/reserves : Metriques descriptives seulement; pas de modele persistant.

### V8.7
- Objectif : Validation walk-forward offline stricte sur V8.4.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/strict_walk_forward_validation_v8_7_manifest.json`, `reports/ml/strict_walk_forward_validation_v8_7.json`, `reports/audit_lite/v8_7_full_local_validation_attestation.json`.
- Tests associes : `tests/ml/test_strict_walk_forward_validation_v8_7.py`.
- Limites/reserves : 5 folds/timeframe; edge non valide trading.

### V8.8
- Objectif : Decision gate research apres V8.7.
- Statut repo : `present`.
- Artefacts presents : `reports/research_decisions/v8_8_research_decision_gate.json`, `reports/research_decisions/v8_8_research_decision_gate.md`.
- Tests associes : `tests/validation/test_research_decision_gate_v8_8.py`.
- Limites/reserves : Decision: pas de backtest; recommander feature audit/selection.

### V8.9
- Objectif : Audit/sélection des features OHLCV+trades.
- Statut repo : `present`.
- Artefacts presents : `reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json`, `reports/features/ohlcv_trades_feature_selection_v8_9.json`, `reports/audit_lite/v8_9_full_local_validation_attestation.json`.
- Tests associes : `tests/features/test_ohlcv_trades_feature_audit_v8_9.py`.
- Limites/reserves : Selection proposee: 18 features; audit-lite initial insuffisamment autoporteur.

### V8.9.1
- Objectif : Correction packaging audit-lite V8.9 autoporteur.
- Statut repo : `validated_by_external_audit_from_context_and_repo_artifacts`.
- Artefacts presents : `reports/audit_lite/zip_audit_v8_9_1.json`, `reports/audit_lite/zip_smoke_v8_9_1.json`, `projet-galapagos-v8.9.1-audit-lite.zip`.
- Tests associes : `non identifies ou indirects`.
- Limites/reserves : Validee par audit externe selon contexte; aucune modification fonctionnelle V8.9.

### V9.0
- Objectif : Feature store raffinee depuis V8.3 + selection V8.9.
- Statut repo : `produced_locally_pending_group_external_audit`.
- Artefacts presents : `reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json`, `reports/features/refined_ohlcv_trades_feature_store_v9_0.json`.
- Tests associes : `tests/features/test_refined_ohlcv_trades_features_v9_0.py`.
- Limites/reserves : Produite localement; incluse dans candidate groupee.

### V9.1
- Objectif : Dataset supervise offline raffine avec labels V5.2.
- Statut repo : `produced_locally_pending_group_external_audit`.
- Artefacts presents : `reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json`, `reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.json`.
- Tests associes : `tests/datasets/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py`.
- Limites/reserves : Produite localement; full data non inclus dans audit-lite.

### V9.2
- Objectif : ML offline raffine static split.
- Statut repo : `produced_locally_pending_group_external_audit`.
- Artefacts presents : `reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json`, `reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json`.
- Tests associes : `tests/ml/test_refined_ohlcv_trades_offline_ml_research_v9_2.py`.
- Limites/reserves : Scores research_*; pas de modele persistant.

### V9.3
- Objectif : Strict walk-forward raffine.
- Statut repo : `produced_locally_pending_group_external_audit`.
- Artefacts presents : `reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json`, `reports/ml/refined_strict_walk_forward_validation_v9_3.json`.
- Tests associes : `tests/ml/test_refined_strict_walk_forward_validation_v9_3.py`.
- Limites/reserves : Claims false; no backtest/no signal.

### V9.3.1
- Objectif : Pas de version fonctionnelle autonome; suffixe de correction packaging groupee V9.0-to-V9.3.1.
- Statut repo : `grouped_packaging_candidate_pending_external_audit`.
- Artefacts presents : `projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip`, `scripts/release_audit_lite_zip_v9_0_to_v9_3_1.py`, `reports/audit_lite/zip_smoke_v9_0_to_v9_3_1.json`.
- Tests associes : `tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py`.
- Limites/reserves : Candidate actuelle pending_external_audit; correction packaging uniquement.

## 4. État exact V8.9.1
- ZIP V8.9.1 : `projet-galapagos-v8.9.1-audit-lite.zip` exists=True.
- Audit V8.9.1 : passed=`True`.
- Smoke V8.9.1 : passed=`True`.
- Nature : correction packaging audit-lite uniquement pour rendre le ZIP V8.9 autoporteur.
- Reserve : les resultats fonctionnels V8.9 ne sont pas modifies; V8.9.1 sert de dernier point valide avant V9.

## 5. État exact V9.0/V9.1/V9.2/V9.3/V9.3.1 si présent
- V9.0 selected_features_count : `18`.
- V9.1 dataset rows : `{'1m': 527040, '5m': 105408, '15m': 35136, '1h': 8784}`.
- V9.2 score rows : `{'1m': 2107920, '5m': 421392, '15m': 140304, '1h': 34896}`.
- V9.3 score rows : `{'1m': 8805440, '5m': 1759808, '15m': 585536, '1h': 145184}`.
- V9.3 folds_count : `{'1m': 5, '5m': 5, '15m': 5, '1h': 5}`.
- V9.3 claims false : `{'robust_edge_claimed': False, 'strategy_validated': False, 'backtest_performed': False, 'actionable_signal_produced': False, 'walk_forward_validated_for_trading': False}`.
- V9.0-to-V9.3.1 ZIP audit : passed=`True`.
- V9.0-to-V9.3.1 ZIP smoke : passed=`True`.
- ZIP bytes : `2318053`; sha256 : `9bed32a8da8d4b57ca2995f8e16755823c012b181221504c3588ec8bef66430e`.
- V9.3.1 n'est pas une couche metier autonome; c'est le suffixe de correction packaging groupee `V9.0_to_V9.3.1`.

## 6. Architecture actuelle du repo
- `ingestion_data` : chemins ['src/galapagos/data', 'src/galapagos/data/public_market', 'src/galapagos/data/public_trades'], fichiers Python detectes `104`.
- `features` : chemins ['src/galapagos/features'], fichiers Python detectes `42`.
- `labels` : chemins ['src/galapagos/labels'], fichiers Python detectes `19`.
- `datasets` : chemins ['src/galapagos/datasets'], fichiers Python detectes `43`.
- `ml_offline` : chemins ['src/galapagos/ml'], fichiers Python detectes `68`.
- `walk_forward` : chemins ['src/galapagos/ml/strict_walk_forward.py', 'src/galapagos/ml/refined_strict_walk_forward.py'], fichiers Python detectes `2`.
- `backtests` : chemins ['src/galapagos/backtest', 'configs/backtests'], fichiers Python detectes `7`.
- `risk_execution` : chemins ['src/galapagos/risk', 'src/galapagos/execution'], fichiers Python detectes `11`.
- `portfolio_journal_storage` : chemins ['src/galapagos/journal/sqlite_store.py', 'src/galapagos/execution/position_manager.py'], fichiers Python detectes `2`.
- `dashboard` : chemins ['dashboard/streamlit_app.py'], fichiers Python detectes `1`.
- `configs` : chemins ['configs'], fichiers Python detectes `0`.
- `release_audit_smoke` : chemins [], fichiers Python detectes `0`.

## 7. État data / ingestion
- Ingestion publique Binance OHLCV et aggTrades presente via `src/galapagos/data` et manifests V2.3/V5.0/V8.2.
- La fenetre trades courante est `2023-03-25` -> `2024-03-24`, 366 jours, source Binance public archive spot BTCUSDT aggTrades.
- Les scripts de collecte full ne sont pas relances dans ce handoff.

## 8. État features
- Features OHLCV historiques : V2/V3/V4/V5/V6.
- Features OHLCV+trades : V7/V8.3.
- Feature audit V8.9 : 18 selected, 27 dropped, 29 review selon contexte et artefacts.
- V9.0 produit la feature store raffinee a partir des 18 selected_features.

## 9. État labels
- Labels forward V5.2 presents via `reports/manifests/max_history_label_factory_v5_2_manifest.json`.
- V9.1 reutilise les labels V5.2 filtres sur la fenetre V9.0/V8.2.
- Aucun redesign de label n'a ete lance apres V8.9.1.

## 10. État datasets
- Dataset V8.4 full present selon manifest; dataset raffine V9.1 present avec rows `{'1m': 527040, '5m': 105408, '15m': 35136, '1h': 8784}`.
- Les splits train/validation/test restent temporels, sans shuffle, avec walk_forward_group.
- Aucun nouveau dataset n'a ete cree dans la mission de handoff.

## 11. État ML offline
- ML offline V8.5 et V9.2 present, modeles autorises : majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2.
- Les sorties sont nommees `research_*`; aucun modele persistant pickle/joblib/onnx detecte.
- Les metriques restent descriptives et non actionnables.

## 12. État walk-forward
- V8.7 strict walk-forward et V9.3 refined strict walk-forward presents.
- Politique V9.3 : calendar_month, initial_train_months=6, validation=1, test=1, step=1, purge_bars=5, embargo_bars=5, expanding_train=true, shuffle=false.
- Folds V9.3 : `{'1m': 5, '5m': 5, '15m': 5, '1h': 5}`.

## 13. État backtests / baselines
- Le repo contient des modules/configs historiques de backtest et des rapports anciens references, mais le scope courant V8.9.1 -> V9.0_to_V9.3.1 interdit tout backtest.
- `reports/backtests` et `reports/strategies` ne sont pas presents dans le workspace courant selon le scan safe.
- Les baselines ML offline existent; elles ne sont pas des strategies.

## 14. État risk / execution / paper trading
- `PaperBroker.create_order()` leve `RealTradingDisabledError`.
- `RiskEngine` impose `paper_trading_only` via profile_config et applique kill-switch / limites de risque.
- Il existe des modules `execution` et `strategies` historiques, mais aucun ordre reel n'est possible via `create_order`.
- Reserve : le RiskEngine est une couche separable; une orchestration incorrecte pourrait l'ignorer, mais resterait dans le broker papier faute de broker reel.

## 15. Garde-fous no-real-trading
- `git_branch` : `main`.
- `git_status_initial` : `## main...origin/main [ahead 2]`.
- `env_sensitive_filenames` : `['.env.example present', 'temp_smoke .env.example historical copies present', 'no root .env listed by safe filename scan']`.
- `paper_broker_real_order_guard` : `src/galapagos/execution/paper_broker.py::PaperBroker.create_order raises RealTradingDisabledError`.
- `no_real_trading_test` : `tests/test_no_real_trading.py covers create_order and static dangerous patterns`.
- `current_scope_safety_flags` : `{'trading_enabled': False, 'orders_enabled': False, 'backtest_enabled': False, 'paper_live_enabled': False}`.
- `persistent_model_files` : `none found by safe filename scan excluding .venv/temp_smoke`.
- `root_orders_execution_models_dirs` : `{'orders': False, 'execution': False, 'models': False, 'reports/backtests': False, 'reports/strategies': False}`.
- `risk_engine` : `RiskEngine requires profile_config.paper_trading_only and kill-switch checks; direct paper broker calls remain paper-only but can bypass risk evaluation if called manually`.

## 16. Tests et validateurs lancés
- `git branch --show-current` -> `PASS` (main).
- `git status --short --branch` -> `PASS` (## main...origin/main [ahead 2]).
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `PASS` (5192 tests collected in 2.54s; real 3.09s).
- `python scripts/audit_audit_lite_zip_v9_0_to_v9_3_1.py --zip projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip` -> `PASS` (passed=true, errors=[]; real 0.69s).
- `python scripts/smoke_audit_lite_zip_v9_0_to_v9_3_1.py --zip projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip` -> `PASS` (passed=true, errors=[]; real 4.91s).
- Les validateurs full V9.0/V9.1/V9.2/V9.3 n'ont pas ete relances pendant ce handoff pour eviter des lectures full longues; l'attestation full locale groupee existe.

## 17. Résultats des commandes
- Collect-only : `5192 tests collected`.
- Audit audit-lite V9.0-to-V9.3.1 : `PASS`.
- Smoke audit-lite V9.0-to-V9.3.1 : `PASS`.
- Git : `## main...origin/main [ahead 2]`.

## 18. Fichiers importants à lire par ChatGPT
- `reports/PROJECT_STATE.json` exists=True bytes=41538.
- `reports/current/latest_summary.md` exists=True bytes=619.
- `reports/current/latest_metrics.json` exists=True bytes=1051.
- `projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip` exists=True bytes=2318053.
- `reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json` exists=True bytes=14789.
- `reports/audit_lite/zip_audit_v9_0_to_v9_3_1.json` exists=True bytes=150.
- `reports/audit_lite/zip_smoke_v9_0_to_v9_3_1.json` exists=True bytes=150.
- `reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json` exists=True bytes=14479.
- `reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json` exists=True bytes=20239.
- `reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json` exists=True bytes=190027.
- `reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json` exists=True bytes=458212.
- `reports/features/ohlcv_trades_feature_selection_v8_9.json` exists=True bytes=21753.

## 19. Points validés
- V8.9.1 est la derniere version validee selon PROJECT_STATE et le contexte utilisateur.
- La candidate courante est V9.0_to_V9.3.1 pending_external_audit.
- Le ZIP audit-lite le plus recent existe et inclut la correction _bootstrap.py.
- Audit ZIP V9.0-to-V9.3.1 PASS.
- Smoke ZIP V9.0-to-V9.3.1 PASS.
- pytest collect-only PASS avec 5192 tests collectes.
- selected_features_count = 18.
- Dataset row counts V9.1 = 527040/105408/35136/8784.
- Score row counts V9.2 et V9.3 presents dans latest_metrics.
- folds_count = 5 par timeframe.
- Claims V9.3 false: robust_edge_claimed, strategy_validated, backtest_performed, actionable_signal_produced, walk_forward_validated_for_trading.
- Flags courants no trading/no orders/no backtest/no strategy false cote enablement.

## 20. Points faibles / réserves
- V9.0_to_V9.3.1 reste pending_external_audit; ne pas passer a une nouvelle version fonctionnelle avant audit externe strict.
- Les validateurs full V9.0/V9.1/V9.2/V9.3 n ont pas ete relances pendant ce handoff pour eviter lectures longues des Parquet complets; ils sont couverts par l attestation full locale existante.
- Le repo contient des modules historiques backtest/strategies/configs; ils ne sont pas actifs dans le scope courant mais doivent rester exclus des claims V9.x.
- Des dossiers temporaires/historiques comme temp_smoke et des __pycache__ existent dans le workspace; les ZIP audit-lite les excluent.
- Le RiskEngine existe, mais une utilisation directe du PaperBroker pourrait contourner l evaluation de risque; cela reste paper-only car create_order reel est bloque.

## 21. Décision recommandée
Soumettre projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip a l audit externe strict; ne pas creer V9.4 avant PASS externe.

## 22. Prochaine version recommandée
V9.0-to-V9.3.2 uniquement si nouvel audit externe trouve encore une reserve packaging; sinon V9.4 Research Decision Gate refined apres validation externe.

## 23. Prompt proposé pour la prochaine mission
```text
Tu es l'agent auditeur du Projet Galapagos. Lis reports/galapagos_resume_for_handoff.md et reports/galapagos_resume_for_handoff.json, puis audite strictement la candidate V9.0_to_V9.3.1 sans trading, sans ordre, sans cle API et sans backtest. Commence par verifier git status, le ZIP projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip, les scripts audit/smoke, les manifests V9.0/V9.1/V9.2/V9.3, les samples audit-lite, les claims false et les flags no-trading/no-backtest/no-orders. Si une reserve existe, proposer uniquement une sous-version corrective V9.0-to-V9.3.2; sinon recommander la prochaine etape research sans claim trading.
```
