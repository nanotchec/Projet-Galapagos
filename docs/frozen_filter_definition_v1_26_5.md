# Frozen Filter Definition - Galapagos V1.26.5 (Hardened Audit)

## Audit de Source Strict
La définition du filtre "Frozen" a été auditée avec un niveau de rigueur accru (27 points de contrôle).

- **Filtre identifié** : `low_frequency_strict_score`.
- **Famille de règle** : `frequency` (Confirmé par Sweep V1.24.1).
- **Causalité** : `True` (Confirmé par Sweep V1.24.1 et Code).
- **Colonnes utilisées** : `timestamp`, `predicted_probability` (Confirmé).
- **Selected Count (Ref)** : 122 (Cohérent avec Robust Summary V1.25.1).
- **Extraction Status** : SOURCE_MATCHED_CODE_AND_REPORTS_STRICT.

## Paramètres du Filtre Verrouillés
- **Policy** : `horizon_only`.
- **Temporal Rule** : `7D` (Fenêtre hebdomadaire).
- **Logic** : `highest_score_per_period`.
- **Max Trades per Period** : 1.
- **Tie-Break** : `pandas_current_order_after_score_sort` (Historical Warning).

## Sécurité et Non-Optimisation
Le filtre a été audité pour garantir l'absence de toute métrique future ou de PnL réalisé dans sa logique de sélection :
- `uses_future_returns` : **False**.
- `uses_realized_pnl` : **False**.
- `uses_mfe_mae` : **False**.
- `uses_exit_reason` : **False**.

## Avertissement sur le Tie-Break
L'implémentation historique ne définit pas de clé de tri secondaire explicite. Le protocole accepte cette limitation pour des raisons de fidélité historique mais impose un avertissement (`TIE_BREAK_WARNING`) pour toute validation future.
