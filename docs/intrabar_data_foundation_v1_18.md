# Intrabar Data Foundation - V1.18

La version V1.18 introduit une fondation de donnees intrabar (5m/1m) strictement reservee a la recherche.

## Objectifs
- **Diagnostic de sortie** : Analyser si les sorties TP/SL sur 4h sont realistes ou si le bruit intra-bougie detruit l'edge.
- **Calcul MAE/MFE** : Obtenir des mesures precises d'excursion (Maximum Adverse/Favorable Excursion) pour calibrer les stops.
- **Modelisation des couts** : Evaluer l'impact du spread et de la volatilite intra-bougie sur la profitabilite reelle.

## Architecture
Le package `galapagos.research.intrabar` comprend :
- `availability.py` : Verification de la disponibilite publique (Binance/Bybit).
- `downloader.py` : Telechargement controle avec limites de securite (30 jours pour 5m, 7 jours pour 1m).
- `alignment.py` : Alignement temporel entre les bougies 4h (parent) et les bougies intrabar (children).
- `execution_simulator.py` : Simulateur de sortie TP/SL avec gestion de l'ambiguite intra-bougie.
- `mae_mfe.py` : Calculateur d'excursion.
- `cost_model.py` : Modele de stress des couts base sur la volatilite intrabar.

## Securite et Limites
- **Research Only** : L'intrabar n'est jamais utilise pour la prise de decision en temps reel.
- **Capped Downloads** : Les telechargements sont limites dans le temps pour eviter une utilisation excessive du reseau.
- **No Persistence in Zip** : Les donnees parquet intrabar volumineuses sont exclues des zips de release pour rester "clean". Seuls les rapports de synthese sont conserves.
- **Conservative Fallback** : En cas de doute intra-bougie (TP et SL touches dans la meme minute), le simulateur choisit systematiquement le pire scenario.

## Verdicts V1.18
- `INTRABAR_FOUNDATION_READY` : Fondation logicielle validee.
- `INTRABAR_5M_PUBLIC_AVAILABLE` : Donnees Binance/Bybit accessibles sans authentification.
- `INTRABAR_SIMULATION_EXECUTED` : Les premiers tests de simulation confirment la faisabilite technique.
