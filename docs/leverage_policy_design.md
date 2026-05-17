# Design de politique de levier

Le levier reste interdit dans Galapagos V1.10.2.

## Pourquoi le levier est interdit maintenant

Les runs recents montrent :

- performance instable entre fenetres ;
- couts importants ;
- dependance probable au regime de marche ;
- hypothese long-only non validee par holdout.

Ajouter du levier avant de prouver un edge net sans levier amplifierait surtout les erreurs, les
frais, le slippage et le drawdown.

## Conditions minimales avant d'envisager le levier

- Edge net positif sans levier.
- Calibration, validation et holdout positifs ou au minimum robustes.
- Drawdown controle.
- Stops fiables.
- Frais et slippage integres dans toutes les simulations.
- Ledger officiel complet.
- Max leverage faible.

## Proposition future

- `leverage_allowed=false` par defaut.
- `max_leverage=1.0` en V1.
- Experimentations paper uniquement a `1.2x` puis `1.5x` si les conditions sont remplies.
- Aucun ordre reel.

## Limite V1.10.2

Aucun levier n'est implemente. Ce document sert seulement de garde-fou pour une future discussion.
## V1.11 - politique levier

Le levier reste interdit pour l'instant. Conceptuellement, `max_leverage=1.0`
tant que Galapagos n'a pas prouve d'edge net hors calibration.

Conditions minimales avant tout test levier :
- edge net positif sans levier ;
- calibration, validation et holdout positifs ;
- drawdown controle ;
- couts et slippage stresses ;
- stops fiables ;
- decisions stables ;
- paper uniquement ;
- stress test documente.

Un futur test pourrait envisager 1.2x ou 1.5x en paper uniquement, jamais avant
holdout valide. V1.11 n'implemente aucun levier.
