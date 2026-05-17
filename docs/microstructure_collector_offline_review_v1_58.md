# Documentation V1.58 - Human Offline Collector Contract Review Gate

## 1. Contexte
Cette version clôture la phase de conception et de validation théorique du contrat collecteur pour les données microstructure. Elle fait suite à la V1.57.2 qui avait confirmé la couverture des champs requis.

## 2. Résultats de la Revue
La revue offline a porté sur les points suivants :
- **Déclassement Bybit** : L'utilisation du `turnover` comme proxy pour le `number_of_trades` (absent de Bybit V5) est validée comme acceptable pour la phase de recherche.
- **Asymétrie des Champs** : Les différences structurelles entre Binance et Bybit sont documentées et traitées dans l'adapter layer.
- **Causalité** : La politique de timestamps (`ingest_ts >= closing_time`) est confirmée pour garantir l'absence de lookahead.

## 3. Registre des Risques
Les risques identifiés (divergence de schéma, overconfidence sur fixtures) sont mitigés par :
- Une normalisation stricte.
- Un plan d'extension des fixtures prévu.
- Un verrouillage automatique du réseau (NetworkGuard).

## 4. Verdict et Prochaines Étapes
**Verdict : MICROSTRUCTURE_OFFLINE_REVIEW_GATE_PASSED**

Le système est autorisé à passer à la phase de **controlled_preflight_planning** (V1.59+).
**ATTENTION : Aucune collecte réelle n'est approuvée à ce stade.**

## 5. Garanties de Sécurité (V1.58)
- **Infrastructure Only** : OUI
- **Réseau désactivé** : OUI
- **Appels API** : 0
- **Ordres réels** : IMPOSSIBLE
