# Microstructure Data Enrichment Specification (V1.52)

## Contexte
Cette version V1.52 est une spécification technique d'infrastructure visant à définir le plan de collecte et les critères de qualité nécessaires pour enrichir les données microstructure, et ainsi débloquer l'analyse pour l'année 2026.

## Objectifs
- **Identifier** les manques (gaps) affectant l'année 2026.
- **Définir** un ensemble de champs OHLCV et microstructure robustes.
- **Définir** les sources candidates, les politiques de causalité, et les priorités de collecte.
- **Établir** des critères de validation (Data Contract) avant l'ingestion effective.

## Résultats de l'Inventaire
- L'historique 2026 présente un ratio de blocage de 1.0 (100% bloqué).
- Raison : Périodes totalement dépourvues de données microstructure (5m).

## Plan d'Action d'Enrichissement
1. **Priorité** : Backfill des périodes `2026-01-01` à `2026-12-31`.
2. **Sources acceptées** : Binance Public Historical Data, Kraken REST API.
3. **Exigences Causales** : 
   - Strict alignement de `available_ts` >= heure de clôture de la fenêtre de 5m.
   - Aucun lookahead depuis des labels 4h futurs.
4. **Champs Requis** : `open_5m`, `high_5m`, `low_5m`, `close_5m`, `volume_5m`, `quote_asset_volume_5m`, `number_of_trades_5m`, `taker_buy_base_asset_volume_5m`, `taker_buy_quote_asset_volume_5m`.

## Critères de Validation (Data Contract)
- Taux de couverture minimum : **98%**
- Ratio maximal de données manquantes (missingness) : **2%**
- Alignement temporel : 99ème percentile de précision <= 100ms.

---
**RESEARCH_ONLY / INFRASTRUCTURE_ONLY** :
- Aucun téléchargement de données externes n'a été effectué.
- Aucun appel API n'a été effectué.
- Aucune stratégie n'a été validée, et le système reste inapte à passer des ordres réels.
