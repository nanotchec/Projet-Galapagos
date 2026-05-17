# Galapagos V1.24.1 - Audit de fuite et walk-forward

V1.24.1 corrige un risque méthodologique identifié dans V1.24 : le proxy
`gross_expected_move_pct` pouvait dépendre de colonnes `forward_return_*`, donc de
rendements futurs déjà réalisés. Ces colonnes restent utiles pour diagnostiquer les
résultats, mais elles ne doivent jamais piloter une règle de sélection causale.

La version sépare désormais :

- `causal_expected_move_pct` : estimation pré-trade construite sans forward returns.
- `diagnostic_forward_move_pct` : champ diagnostic utilisant les forward returns, exclu
  des règles candidates.
- `gross_expected_move_pct` : alias conservé pour compatibilité, mais désormais égal au
  champ causal.

Les règles de sélection déclarent explicitement :

- leurs colonnes utilisées ;
- leur famille ;
- leur statut `causal`.

Le meilleur filtre observé est sélectionné uniquement parmi les règles causales. Le
filtre `low_frequency_strict_score` reste causal car il utilise seulement le timestamp et
la probabilité prédite.

V1.24.1 ajoute aussi une validation walk-forward par fenêtres temporelles :

- 2024 H1 ;
- 2024 H2 ;
- 2025 H1 ;
- 2025 H2 ;
- 2026 YTD.

Cette étape ne valide pas une stratégie. Elle vérifie seulement si le signal observé en
V1.24 survit à un découpage temporel plus strict. Le reviewer LLM reste désactivé, le
holdout reste verrouillé, et aucun ordre réel n'est possible.
