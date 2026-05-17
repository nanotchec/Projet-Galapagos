# Intrabar execution simulation design

Objectif futur : simuler des signaux 4h avec des sorties TP/SL sur donnees 1m ou
5m.

Principes :
- Signal timeframe : 4h.
- Execution simulation timeframe : 1m ou 5m.
- Les donnees intrabar doivent commencer apres `available_ts` du signal.
- Si TP et SL sont touches dans la meme bougie intrabar et que l'ordre exact est
  inconnu, le mode conservateur choisit le resultat defavorable.
- Slippage, spread et fees doivent etre modelises explicitement.
- En cas de donnees intrabar manquantes, fallback conservateur ou trade non
  evaluable.

V1.11 ajoute seulement les stubs research. Aucun telechargement massif n'est
effectue.

## V1.17 Precision
Si le rapport `data_gap_analysis` de la V1.17 conclut que l'intrabar est une priorite (`INTRABAR_DATA_PRIORITY`), cela indique que le slippage ou le bruit intra-bougie 4h detruit l'edge (souvent diagnostique par le `cost_failure.py`). L'etape suivante de recherche consistera alors a telecharger et simuler explicitement l'intrabar, **avant** de reactiver le LLM reviewer.

## V1.18 Implementation Foundation
La V1.18 realise cette etape en introduisant :
- Un package de recherche dedie : `src/galapagos/research/intrabar/`.
- Un orchestrateur de fondation : `scripts/run_intrabar_foundation.py`.
- Des verifications de disponibilite publique (Binance/Bybit).
- Un simulateur de sortie TP/SL conservateur base sur l'intrabar.

Cette fondation permet de quantifier si l'echec de 2026 est du a une mauvaise execution intra-bougie ou a un mauvais signal de base.
Le LLM reviewer reste desactive.
