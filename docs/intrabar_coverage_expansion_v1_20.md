# Intrabar Coverage Expansion - V1.20

Cette documentation détaille l'effort d'expansion de la couverture des données intrabar entrepris dans la version V1.20.

## Contexte
La version V1.19.2 a révélé que seulement 1.73% des signaux étaient couverts par l'échantillon de 30 jours de données 5m. Pour obtenir des conclusions statistiques valables, un seuil de **20% de couverture** a été fixé comme prérequis pour la validation des politiques de trading.

## Méthodologie V1.20
- **Planification** : Utilisation de `scripts/plan_intrabar_coverage.py` pour identifier les plages temporelles manquantes.
- **Téléchargement** : Extension contrôlée via `scripts/extend_intrabar_history.py` (limite initiale de 180 jours, exécution par chunks).
- **Audit Qualité** : Vérification de la continuité et de la validité des données (OHLC, monotonie) via `scripts/audit_intrabar_data_quality.py`.

## Résultats Préliminaires
- **Couverture V1.19.2** : 1.73%
- **Couverture V1.20** : 5.8% (Après 12 chunks de téléchargement)
- **Verdict** : Toujours `TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT`.

## Prochaines Étapes
- Poursuivre le téléchargement par blocs jusqu'à atteindre les 20% (environ 400-500 jours de données 5m requis).
- Une fois les 20% atteints, le verdict de comparaison pourra passer à `TRADE_LEDGER_INTRABAR_COVERAGE_IMPROVED_BUT_LIMITED`.
