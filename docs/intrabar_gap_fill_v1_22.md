# Intrabar Gap Fill - Galapagos V1.22

## Objectif
L'objectif de la version V1.22 était de combler les lacunes de données intrabar (5m) pour le dataset BTC/USDT afin de permettre une évaluation continue (continuous evaluation) et haute fidélité des politiques de trading.

## Gap Comblé
Un gap massif de **202 jours** (entre le 19 avril 2025 et le 7 novembre 2025) a été identifié et comblé par téléchargement de 29 chunks de données via l'API Binance. 
Un gap préfixe de **126 jours** (Janvier à Mai 2024) a également été comblé pour assurer une couverture de 100% des signaux disponibles.

## Spécifications Techniques
- **Fichier Standard** : `data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet`
- **Continuité** : Données continues du **2024-01-01** au **2026-05-06**.
- **Qualité** : `gaps_count = 0`, `status = INTRABAR_DATA_QUALITY_OK`.

## Évaluation Scientifique
Grâce à ce comblement, la comparaison des politiques est passée de `preliminary_gap_aware` à `preliminary_continuous`.
Les résultats confirment que toutes les politiques testées (`fixed_percent`, `atr_proxy`, `horizon_only`) restent non rentables après déduction des frais de transaction réels (verdict : `ALL_POLICIES_NEGATIVE_AFTER_COSTS_CONTINUOUS`).

## Sécurité et Conformité
- **Reviewer LLM** : Désactivé.
- **Holdout** : Non exécuté sur ce dataset.
- **Exécution Réelle** : Aucun ordre réel passé. Le système ne peut toujours pas passer d'ordre réel.
