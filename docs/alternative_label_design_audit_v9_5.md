# Alternative Label Design Audit V9.5

## Resume executif

V9.5 audite les labels actuels apres la decision V9.4 : `backtest_not_justified_refine_labels`.

Decision V9.5 : `label_redesign_candidate_volatility_normalized`.

Justification : Le seuil fixe actuel semble non scale entre timeframes; la normalisation par volatilite est le candidat le plus defensif.

V9.5 ne lance aucun backtest, ne cree aucune strategie, ne produit aucun signal actionnable et ne modifie pas les labels existants.

## Labels actuels

- Target actuel : `up_down_flat_h1`.
- Horizons V5.2 : `[1, 3, 5]`.
- Seuil V5.2 : `0.0005`.
- Lecture full dataset locale : `True`.
- Lecture labels full locale : `True`.

- `1m` : majority `FLAT` rate `0.768511138943`, entropy `1.012070838247`, label_change_rate `0.31524216335`.
- `5m` : majority `FLAT` rate `0.475680601435`, entropy `1.522535622606`, label_change_rate `0.580548093444`.
- `15m` : majority `UP` rate `0.357937050975`, entropy `1.580179239382`, label_change_rate `0.644219529579`.
- `1h` : majority `UP` rate `0.428702430078`, entropy `1.47792582421`, label_change_rate `0.644273759028`.

## Diagnostic du probleme

- Labels trop bruites : `True`.
- Seuils probablement trop faibles ou non scales : `True`.
- Horizon h1 possiblement trop court : `True`.
- Desequilibre de classes : `True`.
- Probleme de definition FLAT : `True`.
- Instabilite timeframes/regimes : `True` / `True`.
- Cas trop proches des labels melanges : `21`.

## Catalogue de designs alternatifs

- `fixed_stricter_thresholds` : review - Le seuil actuel est 0.0005; la dominance FLAT 1m suggere qu'un seuil fixe seul ne suffit pas.
- `volatility_normalized_thresholds` : accept_for_future_experiment - Candidat prioritaire car le seuil fixe actuel semble non scale entre timeframes.
- `rolling_quantile_or_tertile_labels` : review_for_future_experiment - Utile si le redesign volatility-normalized ne stabilise pas les classes.
- `alternative_horizon` : review_for_future_experiment - Le taux de transition eleve suggere de tester un horizon un peu plus long, sans le valider ici.
- `wider_flat_class` : reject_as_primary - Non prioritaire car la classe FLAT est deja trop dominante en 1m.
- `binary_directional_only` : review_only - A evaluer seulement apres un redesign de seuils causaux.
- `causal_multi_horizon_labels` : review_for_future_experiment - Prometteur en recherche, mais pas le premier candidat conservateur.

## Decision V9.5

La famille recommandee pour experimentation future est : `volatility_normalized_thresholds`.

Prochaine etape : `V9.6 - Refined Label Factory Candidate`.

## Interdits maintenus

V9.5 ne valide aucune strategie, ne produit aucun backtest, aucun signal actionnable, aucun ordre, aucun paper live et aucun trading reel. Aucun modele persistant, aucune API privee et aucune cle API ne sont utilises.
