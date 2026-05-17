# Paper-Forward Validation Harness (V1.27)

Ce document décrit le fonctionnement du harnais de validation out-of-sample (OOS) mis en place dans la version V1.27.

## Objectif
Le harnais Paper-Forward a pour but d'appliquer strictement le protocole pré-enregistré (V1.26.2) sur les données générées après la phase de découverte (post-mai 2026).

## Composants
1. **Protocol Loader** : Charge le protocole V1.26.2 et vérifie que tous les verrous de sécurité sont actifs.
2. **Data Availability Check** : Détecte automatiquement la présence de nouvelles données en comparant les timestamps des parquets avec la date de référence (2026-05-06).
3. **Frozen Filter** : Implémente la logique de filtrage `low_frequency_strict_score` de manière immuable.
4. **Validation Engine** : Exécute le backtest sur les nouvelles données et calcule les métriques.
5. **Criteria Evaluator** : Compare les métriques observées avec les seuils de succès pré-enregistrés.

## Règles de Sécurité
- **Seuil de Conclusion** : Un minimum de **60 trades sélectionnés** est requis pour qu'une validation soit considérée comme concluante.
- **Interdiction de Modification** : Le harnais refuse de s'exécuter si une colonne interdite (ex: `forward_return`) est détectée dans les candidats.
- **Reviewer LLM** : Reste strictement désactivé jusqu'à ce que la validation humaine soit complète.

## Utilisation
```bash
python scripts/run_paper_forward_validation.py \
  --protocol reports/research/preregistered_signal_validation_protocol_v1_26_2.json \
  --success-criteria reports/research/preregistered_success_criteria_v1_26_2.json \
  --predictions data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet \
  --dataset data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet \
  --intrabar data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet
```

## Verdicts
- `PAPER_FORWARD_HARNESS_READY_NO_NEW_DATA` : Le système est prêt mais attend de nouvelles données.
- `PAPER_FORWARD_VALIDATION_INCONCLUSIVE_NEEDS_MORE_DATA` : Des données sont détectées mais l'échantillon est insuffisant.
- `PAPER_FORWARD_VALIDATION_PASSED_PRELIMINARY` : Les critères sont respectés sur l'échantillon actuel (Sample >= 60).

## Mise à jour V1.27.4 (Harnais avec Protocole de Référence)
La version V1.27.4 connecte officiellement le harnais technique au protocole de référence :
- **Protocole exclusif** : V1.26.6 est le seul protocole autorisé pour la validation `paper-forward`. Les versions antérieures (V1.26.2/V1.26.3/V1.26.4) sont obsolètes et proscrites.
- **Filtre** : Le filtre est totalement reconstructible (`highest_score_per_period` sur 7D).
- **Rigueur Statistique** : La validation de la stratégie nécessite explicitement au moins 60 trades sélectionnés.
- **Statut** : En attente de nouvelles données futures pour conclure la validation (`PAPER_FORWARD_HARNESS_READY_NO_NEW_DATA`).
- **Sécurité** : Aucun ordre réel n'est passé.
