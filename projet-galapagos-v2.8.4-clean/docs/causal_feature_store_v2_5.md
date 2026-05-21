# Galapagos V2.5.2 — Causal OHLCV Feature Store Preview (Correctif V2.5)

Ce document décrit l'architecture technique, les garanties causales, le schéma physique strict et les limitations de la version **V2.5.2 — Causal OHLCV Feature Store Preview** (mise à jour corrective de la V2.5).

> [!NOTE]
> La version V2.5.2 est une mise à jour corrective ciblant le runtime du validateur V2.4 et le timeout du smoke test de la V2.5, sans aucune modification des indicateurs mathématiques calculés.

## 1. Contexte et Objectifs

La version V2.5 (corrigée en V2.5.2) introduit le premier Feature Store Preview de Galapagos. 
Cette couche s'appuie directement sur les données OHLCV resamplées et validées de la V2.4 pour calculer des indicateurs et descripteurs physiques déterministes.
Ce Feature Store est STRICTEMENT destiné à l'analyse et à la recherche historique hors-ligne (Data/Research Only).

## 2. Garanties de Causalité et Sécurité

Afin d'éviter tout biais de look-ahead (surapprentissage ou fuite d'informations du futur), le Feature Store V2.5.2 met en place des garde-fous physiques stricts :
- **Non-anticipation** : Toutes les features à l'index $t$ sont calculées en utilisant uniquement les données OHLCV historiques $s \le t$. Aucun décalage vers le futur (shift positif) n'est autorisé.
- **Warmup de 30 lignes** : Les features glissantes nécessitant jusqu'à 30 valeurs (SMA 30, Volatilité 30) marquent explicitement les 30 premières lignes d'une journée comme `warmup_row = true`.
- **Alignement temporel de décision** : La colonne de décision `decision_ts` est rigoureusement alignée sur le timestamp de disponibilité des données `available_ts`, garantissant qu'aucune décision ne peut être prise virtuellement avant la réception physique de la donnée.
- **ZÉRO trading / ML / Labels** : Cette version n'embarque aucun algorithme de ML, aucun label de prédiction, aucun signal de trading, aucun moteur de backtest et n'autorise aucune exécution d'ordres réels ou simulés (ZÉRO trading réel, paper live ou ordre).

## 3. Schéma Strict de Features (FEATURE_COLUMNS_V2_5)

Le schéma physique est matérialisé en Parquet et contient exactement les colonnes ordonnées suivantes :
1. **Metadata** : `source`, `venue`, `market_type`, `symbol`, `timeframe`, `event_ts`, `close_ts`, `available_ts`, `decision_ts`, `feature_available_ts`, `ingested_at_ts`, `feature_run_id`, `source_ohlcv_sha256`, `feature_schema_version`.
2. **Prix & Returns passés** : `close_lag_1`, `return_1`, `log_return_1`, `return_3`, `log_return_3`, `return_5`, `log_return_5`.
3. **Volatilité passée** : `rolling_vol_5`, `rolling_vol_15`, `rolling_vol_30`.
4. **Structure du candle** : `candle_range`, `candle_body`, `upper_wick`, `lower_wick`, `close_position_in_range`.
5. **Volume** : `volume_lag_1`, `volume_return_1`, `rolling_volume_mean_5`, `rolling_volume_mean_15`, `rolling_volume_zscore_15`.
6. **Tendance / Distance** : `sma_5`, `sma_15`, `sma_30`, `close_to_sma_5`, `close_to_sma_15`, `close_to_sma_30`.
7. **Temporel** : `hour_utc`, `day_of_week_utc`, `is_weekend_utc`.
8. **Qualité** : `warmup_row`, `feature_null_count`, `feature_error_count`.

## 4. Clause de Sécurité Réglementaire

Le projet Galapagos V2.5.2 respecte les clauses réglementaires suivantes :
- V2.5.2 ne valide aucune stratégie.
- V2.5.2 ne produit aucun label.
- V2.5.2 ne produit aucun modèle ML.
- V2.5.2 ne produit aucun backtest.
- V2.5.2 ne produit aucun signal de trading.
- V2.5.2 ne produit aucun ordre.
- V2.5.2 n’autorise aucun paper live.
- V2.5.2 n’autorise aucun trading réel.
- La version candidate V2.5.2 reste en statut `pending_external_audit` avant toute validation externe finale.
