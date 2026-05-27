# V9.12 - Label Redesign Candidate: Horizon Extension + Event-Based Diagnostic

## Resume executif
- Decision V9.12 : `label_redesign_candidate_horizon_event_created_requires_review`.
- Candidat recommande : `up_down_flat_volnorm_h4` avec horizon `h4` et multiplicateur `1.25`.
- V9.12 ne cherche pas a prouver un edge et ne lance aucun ML, walk-forward ou backtest.
- Aucun trading, paper live, ordre, strategie ou signal actionnable.

## Donnees et designs testes
- Donnees full disponibles : `True`.
- Horizons testes : `h2`, `h4`, `h8`.
- Diagnostic event-based : classes `EVENT_UP`, `EVENT_DOWN`, `NO_EVENT`, `AMBIGUOUS`, sans entree/sortie/position/PnL.

## Distributions principales du candidat recommande
- `1m` : majoritaire `UP` a `0.4730`, entropie `1.3219`, distribution `{'DOWN': {'count': 235410, 'rate': 0.4469187834605308}, 'FLAT': {'count': 42189, 'rate': 0.08009454379769905}, 'UP': {'count': 249141, 'rate': 0.47298667274177014}}`.
- `5m` : majoritaire `UP` a `0.4160`, entropie `1.5139`, distribution `{'DOWN': {'count': 41202, 'rate': 0.3912820512820513}, 'FLAT': {'count': 20293, 'rate': 0.19271604938271605}, 'UP': {'count': 43805, 'rate': 0.4160018993352327}}`.
- `15m` : majoritaire `UP` a `0.3441`, entropie `1.5843`, distribution `{'DOWN': {'count': 11193, 'rate': 0.3192527096406161}, 'FLAT': {'count': 11803, 'rate': 0.33665145464917284}, 'UP': {'count': 12064, 'rate': 0.3440958357102111}}`.
- `1h` : majoritaire `FLAT` a `0.5951`, entropie `1.3779`, distribution `{'DOWN': {'count': 1673, 'rate': 0.19185779816513762}, 'FLAT': {'count': 5189, 'rate': 0.5950688073394496}, 'UP': {'count': 1858, 'rate': 0.21307339449541285}}`.

## Comparaison avec V9.6
- `1m` : V9.6 `up_down_flat_volnorm_h1` majoritaire `FLAT` a `0.4680234544005465`, V9.12 `up_down_flat_volnorm_h4` majoritaire `UP` a `0.47298667274177014`.
- `5m` : V9.6 `up_down_flat_volnorm_h1` majoritaire `FLAT` a `0.43417055852982495`, V9.12 `up_down_flat_volnorm_h4` majoritaire `UP` a `0.4160018993352327`.
- `15m` : V9.6 `up_down_flat_volnorm_h1` majoritaire `FLAT` a `0.44186908427414756`, V9.12 `up_down_flat_volnorm_h4` majoritaire `UP` a `0.3440958357102111`.
- `1h` : V9.6 `up_down_flat_volnorm_h1` majoritaire `FLAT` a `0.49988537368179736`, V9.12 `up_down_flat_volnorm_h4` majoritaire `FLAT` a `0.5950688073394496`.

## Candidats refuses ou a revoir
- `horizon_extension` `h2` : `requires_review` - review_lower_priority_than_h4_k1_25.
- `horizon_extension` `h2` : `requires_review` - review_lower_priority_than_h4_k1_25.
- `horizon_extension` `h2` : `refused` - refused_majority_class_over_70_percent.
- `horizon_extension` `h4` : `requires_review` - requires_review_flat_class_too_sparse_on_at_least_one_timeframe.
- `horizon_extension` `h4` : `requires_review` - review_lower_priority_than_h4_k1_25.
- `horizon_extension` `h8` : `requires_review` - requires_review_flat_class_too_sparse_on_at_least_one_timeframe.
- `horizon_extension` `h8` : `requires_review` - review_lower_priority_than_h4_k1_25.
- `horizon_extension` `h8` : `requires_review` - review_lower_priority_than_h4_k1_25.
- `event_based_diagnostic` `h8` : `requires_review` - event-based remains diagnostic only; AMBIGUOUS dominates at least one short timeframe.

## Recommandation suivante
- V9.13 - Dataset/ML diagnostic with the h4 horizon-extension label candidate, uniquement si l'audit externe valide V9.12; aucun backtest.

## Interdits maintenus
- Aucun backtest.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun ordre.
- Aucun paper live.
- Aucun trading reel.
- Aucun modele persistant.
- Aucune API privee et aucune cle API.
- Aucun sidecar SHA256, aucune empreinte ZIP et aucun champ zip_sha256.
