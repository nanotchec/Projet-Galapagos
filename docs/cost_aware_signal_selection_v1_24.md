# Cost-Aware Signal Selection - V1.24

## Objectif

V1.24 ne modifie pas les sorties, les stops, les take-profits, le prompt GPT ou le reviewer LLM.
La version teste uniquement une hypothese de recherche offline :

> Garder moins de candidats, mais uniquement ceux dont le potentiel brut estime peut depasser les couts.

## Base utilisee

- Base scientifique : V1.23.1.
- Intrabar 5m continu : valide.
- Policies comparees : `fixed_percent`, `atr_proxy`, `horizon_only`.
- Policy de reference principale : `horizon_only`, car elle etait la moins mauvaise en V1.23.1.

## Filtres testes

V1.24 compare :
- tous les candidats ;
- no trade ;
- seuils de probabilite ;
- top decile/quartile de probabilite ;
- seuils cost-aware sur move attendu ;
- seuils MFE proxy ;
- filtres de regime ;
- reductions de frequence.

Chaque filtre est compare a une baseline random same-count avec seed fixe.

## Limites

Les filtres sont des hypotheses. Ils ne deviennent pas une strategie.
Un resultat positif sur un petit echantillon reste `PROMISING_BUT_UNVALIDATED`.
Un filtre qui ne bat pas random same-count n'est pas interpretable comme edge.

## Securite

- Aucun ordre reel.
- Aucun Codex CLI.
- Aucun holdout.
- Aucun levier.
- Reviewer LLM desactive.

## Correctif V1.24.1

L'analyse externe de V1.24 a signale un risque de fuite : le proxy
`gross_expected_move_pct` pouvait utiliser des colonnes `forward_return_*`, donc des
rendements futurs realises. V1.24.1 separe maintenant :

- `causal_expected_move_pct`, utilisable par les regles de selection ;
- `diagnostic_forward_move_pct`, reserve aux diagnostics offline ;
- les colonnes de PnL/MFE/MAE realisees, autorisees seulement pour l'evaluation.

Le meilleur filtre final est choisi uniquement parmi les regles causales. Une analyse
walk-forward par fenetres temporelles est ajoutee avant toute discussion future sur un
candidate gate. Le reviewer LLM reste desactive.
