# Intrabar Coverage Expansion - V1.21

Cette version a atteint l'objectif de 20% de couverture intrabar, permettant une comparaison préliminaire des politiques de trading sur un échantillon plus robuste.

## Objectifs
- **Cible** : >= 20% de couverture (evaluated ratio).
- **Standardisation** : Utilisation de `history_5m_v1_21.parquet`.
- **Analyse** : Comparer les résultats avec la V1.20.1.

## Résultats
- **Couverture Atteinte** : **60.18%** (2573 / 4275 candidats).
- **Historique** : 2024-05-06 -> 2026-05-06 (environ 2 ans).
- **Verdict de Comparaison** : `ALL_POLICIES_NEGATIVE_AFTER_COSTS`.
- **Validité** : `preliminary`.

## Observations
Malgré une couverture étendue à plus de 60%, toutes les politiques testées (`fixed_percent`, `atr_proxy`, `horizon_only`) restent négatives après prise en compte des coûts (0.1% spread + commission). 

La politique `horizon_only` (sortie après 4h) présente le meilleur win rate (~51%) mais reste déficitaire.

## Prochaines Étapes
- Étendre la couverture à 80% ou 100% pour couvrir le début de 2024.
- Commencer à tester des politiques plus complexes ou des signaux filtrés.
- Ne pas activer le reviewer LLM tant que le PnL après coûts est négatif.
