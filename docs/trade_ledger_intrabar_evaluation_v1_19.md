# Trade Ledger Intrabar Evaluation - V1.19

La version V1.19 introduit une interface formelle de "Trade Ledger" pour transformer les prédictions ML Galapagos en candidats de trades structurés et documentés.

## Objectifs de Recherche
1. **Sémantique Rigoureuse** : Passer de timestamps de signaux à des objets `TradeCandidate` complets (side, entry, SL, TP, holding time).
2. **Évaluation Multi-Politique** : Comparer des stratégies déterministes (`fixed_percent`, `atr_proxy`, `horizon_only`) pour comprendre la dynamique des sorties.
3. **Audit de Bruit** : Utiliser le 5m pour identifier si les échecs récents sont dus à une mauvaise gestion des sorties ou à une absence d'edge du signal.

## Architecture Trade Ledger
Le package `galapagos.research.trade_ledger` assure :
- **Schema** : Validation stricte des candidats via Pydantic.
- **Signal Loader** : Chargement, audit et déduplication des prédictions ML.
- **Policies** : Définition de règles de sortie déterministes (non optimisées).
- **Ledger Builder** : Construction des candidats avec logique d'entrée réaliste (Next Candle Open).
- **Evaluator** : Simulation intrabar 5m intégrée avec calcul MAE/MFE et coûts.

## Politiques Évaluées
- **Fixed Percent** : SL 1.5%, TP 3%, Horizon 6 bars.
- **ATR Proxy** : SL 1.5 * ATR (proxy), TP 2.0 * SL, Horizon 6 bars.
- **Horizon Only** : Pas de SL/TP, sortie forcée après 6 bars.

## Sécurité et Limites
- **Research Only** : Aucun de ces candidats n'est envoyé à un broker.
- **No Optimization** : Les paramètres des politiques ne sont pas optimisés pour éviter le sur-apprentissage.
- **Intrabar Sample** : L'évaluation reste limitée par l'historique intrabar disponible localement (échantillon de 30 jours).

## Verdicts V1.19
- `TRADE_LEDGER_READY` : L'interface de génération de candidats est opérationnelle.
- `REAL_SIGNAL_INTRABAR_EVAL_READY` : Les signaux ML réels sont simulés avec succès en intrabar.
- `ALL_POLICIES_NEGATIVE_AFTER_COSTS` : Indique que même avec des sorties structurées, l'edge reste insuffisant face aux coûts.

Le système V1.19 ne peut toujours pas passer d'ordre réel.

## V1.24 Signal Selection
La V1.24 reutilise le trade ledger intrabar comme source de resultats par candidat/policy.
Elle ne modifie pas la construction des entries, des exits ou du modele de cout.
Les subsets de candidats sont formes avant evaluation statistique et compares aux baselines random same-count.
