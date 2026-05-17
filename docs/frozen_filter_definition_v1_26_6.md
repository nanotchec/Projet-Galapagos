# Frozen Filter Definition - Galapagos V1.26.6 (Reference)

## Définition de Référence
Cette définition est la seule source de vérité pour la validation "Frozen" du protocole Galapagos.

- **Filtre** : `low_frequency_strict_score`.
- **Logic** : `highest_score_per_period`.
- **Score Column** : `predicted_probability` (Confirmé par audit strict).
- **Temporal Rule** : `7D`.
- **Policy** : `horizon_only`.
- **Reference Protocol** : V1.26.6.
- **Extraction Status** : SOURCE_MATCHED_CODE_AND_REPORTS_STRICT.

## Archive Integrity Note
Les versions antérieures (V1.26.2/V1.26.3) contenaient des mutations accidentelles ou des imprécisions documentaires. Elles sont formellement remplacées (`superseded`) par cette version V1.26.6.

## Paramètres Techniques
- **Threshold** : `null`.
- **Max Trades per Period** : 1.
- **Tie-Break** : `pandas_current_order_after_score_sort` (Non-déterministe explicite).
- **Security Audit** : Aucune colonne future utilisée.

## Exact Reconstructability
La reconstruction exacte du filtre original ( Discovery V1.24) est garantie par le recoupement strict entre le code source et les rapports de sweep historiques.
