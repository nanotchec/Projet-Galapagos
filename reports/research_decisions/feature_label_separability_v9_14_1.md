# V9.14.1 - Data Source Inventory & Branch Decision Correction

## Resume executif
- Version source : `V9.14`.
- Correction : `data_source_inventory_and_branch_decision_correction`.
- Ancienne decision V9.14 : `feature_first_before_more_labels`.
- Decision corrigee V9.14.1 : `data_extension_first_before_more_labels`.
- Justification : Les features OHLCV+aggTrades restent peu separables et le repo contient des sources derivatives partielles non utilisees par V9, notamment funding/open interest.
- V9.14.1 ne relance aucun ML lourd, aucun walk-forward et aucun backtest.
- Aucun trading, aucun paper live, aucun ordre, aucune strategie, aucun signal actionnable.

## Inventaire data-extension
- `ohlcv` : present=`True`, utilise_V9=`True`, priorite=`not_recommended_now`. Source deja integree dans la chaine V9 validee; elle ne repond pas seule au besoin de data-extension.
- `public_trades_aggTrades` : present=`True`, utilise_V9=`True`, priorite=`not_recommended_now`. Source deja utilisee par les features refined V9.0; un raffinement feature reste possible mais ce n'est pas une nouvelle source.
- `order_book_l2` : present=`False`, utilise_V9=`False`, priorite=`missing_or_unknown`. Potentiellement utile, mais aucune presence locale ne doit etre supposee sans fichier ou rapport probant.
- `funding_rates` : present=`True`, utilise_V9=`False`, priorite=`priority_1_candidate`. Meilleure source data-extension deja amorcee localement, mais non integree a la chaine V9 validee.
- `open_interest` : present=`True`, utilise_V9=`False`, priorite=`priority_1_candidate`. Complement naturel pour tester si les regimes derivatives expliquent la faible separabilite OHLCV+aggTrades.
- `liquidations` : present=`False`, utilise_V9=`False`, priorite=`missing_or_unknown`. A ne pas prioriser tant qu'une source publique historique sans secret n'est pas prouvee.
- `long_short_ratios` : present=`True`, utilise_V9=`False`, priorite=`priority_2_candidate`. Utile apres funding/open interest, a condition de clarifier publication time et couverture historique.
- `multi_exchange_multi_venue` : present=`True`, utilise_V9=`False`, priorite=`priority_2_candidate`. Candidat secondaire apres consolidation d'une premiere source derivatives causale.
- `on_chain` : present=`False`, utilise_V9=`False`, priorite=`missing_or_unknown`. Non recommande maintenant faute de preuve locale et de garde-fous d'acquisition.
- `macro_news_sentiment` : present=`True`, utilise_V9=`False`, priorite=`later_candidate`. A evaluer plus tard; certaines acquisitions macro peuvent requerir une cle externe et doivent rester separees.
- `other_derivatives` : present=`True`, utilise_V9=`False`, priorite=`priority_2_candidate`. A examiner apres funding/open interest pour eviter une integration trop large d'un coup.

## Hypotheses H1-H11
- `H1` label encore mal defini : `likely` (medium). Ne pas relancer de walk-forward; revoir les conditions de label seulement apres inventaire data.
- `H2` features actuelles insuffisantes : `likely` (high). Tester d'abord des sources complementaires ou une selection feature plus ciblee.
- `H3` horizon h4 pas adapte : `possible` (medium). Ne pas prioriser un nouvel horizon sans source data complementaire.
- `H4` multi-classe DOWN/FLAT/UP trop difficile : `possible` (medium). Garder le binaire comme hypothese secondaire, pas decision principale.
- `H5` fenetre 2023-2024 trop limitee : `possible` (medium). Extension de fenetre possible apres examen de disponibilite multi-annees.
- `H6` OHLCV+trades agreges ne contiennent pas assez d'information : `likely` (high). Prioriser data-extension derivatives/microstructure avant nouveau label complexe.
- `H7` besoin d'extension data/features avant nouveau label : `likely` (high). Creer une version V9.15 de readiness data-extension.
- `H8` besoin d'arreter la branche refined labels : `possible` (medium). Ne pas arreter avant un diagnostic data-extension strict.
- `H9` besoin d'un label binaire plus simple avant toute autre chose : `possible` (medium). Hypothese secondaire si data-extension ne reduit pas le bruit.
- `H10` besoin d'un label quantile-based plutot que seuil directionnel : `possible` (medium). A garder en reserve apres diagnostic des sources complementaires.
- `H11` besoin de microstructure / derivatives pour esperer une separabilite : `likely` (high). Decision corrigee orientee data-extension avant nouveaux labels.

## Recommandation suivante
- V9.15 Data Extension Readiness / Derivatives Feature Candidate.
- La prochaine version doit auditer les sources derivatives/microstructure disponibles avant de redessiner encore les labels.
- Aucun backtest n'est recommande a ce stade.

## Interdits maintenus
- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest execute.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- Aucun sidecar et aucune empreinte ZIP.
