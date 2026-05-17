# LLM as reviewer design

Philosophie future : le LLM ne cree pas l'alpha. Il recoit un candidat
quantitatif et agit comme reviewer/risk analyst.

Actions possibles futures :
- `ACCEPT`
- `REJECT`
- `REDUCE_SIZE`
- `WAIT`

Contexte cible :

```json
{
  "candidate": "LONG",
  "alpha_score": 0.63,
  "expected_return_6bars": 0.012,
  "expected_cost": 0.004,
  "historical_edge_for_similar_setups": {
    "n": 240,
    "mean_return": 0.006,
    "hit_rate": 0.56,
    "worst_decile": -0.018
  },
  "regime": "uptrend"
}
```

Le risk engine reste deterministe. Aucun live n'est autorise tant qu'un edge net
n'est pas valide hors calibration.

## ML candidate score required before LLM reviewer (V1.15)

Le LLM reviewer ne doit etre reactive que si :
- un modele ou score quantitatif bat le baseline aleatoire ;
- l'edge brut est positif sur au moins deux fenetres walk-forward ;
- l'edge est stable par regime (uptrend, downtrend, range) ;
- les couts ne detruisent pas totalement l'edge ;
- les probabilites sont suffisamment calibrees (gap < 10%).

Si le verdict ML est ML_NO_EDGE ou ML_EDGE_DESTROYED_BY_COSTS, ne pas
investir dans le LLM reviewer.

Codex CLI ne doit pas etre appele. Aucun holdout ne doit etre execute.

## V1.24 Status
La V1.24 confirme que le reviewer LLM reste desactive.
Avant tout reviewer, Galapagos doit montrer qu'un gate quantitatif cost-aware bat les baselines random same-count et conserve une esperance nette robuste.
Le LLM ne doit pas etre utilise pour masquer un signal brut trop faible.

## V1.15.1 Hardening Result

L'evaluation ML a ete durcie en V1.15.1 (walk-forward chronologique strict, baselines trading-like, tests de permutation, analyse par top-bucket). 
Si le modele ne bat pas les baselines de maniere statistiquement significative (p-value permutation test) et avec un edge net positif, le LLM reviewer reste completement desactive.
Un LLM ne peut pas magiquement extraire du signal la ou des modeles ensemblistes (Random Forest, Gradient Boosting) echouent.

## V1.15.2 Conservative Verdict

Apres audit, la V1.15.1 permettait un verdict trop optimiste base sur une seule fenetre positive. 
Desormais, le verdict `ML_READY_FOR_ENSEMBLE_SIGNALS` exige qu'au moins 2 fenetres chronologiques prouvent de maniere robuste :
- Le succes du test de permutation
- Un edge net positif post-frais dans le top decile
- Une surperformance par rapport a l'Alpha Score

Sans ces conditions, le verdict retombe a `ML_REGIME_DEPENDENT_WEAK_EDGE` ou `ML_FAILS_ROBUSTNESS_CHECKS`.

## V1.15.3 Packaging & Metric Consistency

La V1.15.3 confirme un signal faible et dependant du regime. 
Les comparaisons de metrics (random baseline same-count) ont ete durcies et l'evaluation croisee (ML vs Alpha) precise desormais explicitement le ratio des fenetres victorieuses, evitant les booleens globaux trompeurs.

## V1.15.4 Release Packaging Final Fix

La V1.15.4 apporte un correctif strict sur le flux de generation du zip de release (execution en 2 passes) pour garantir l'inclusion des rapports d'audit finaux.
Le verdict scientifique reste inchange par rapport a la V1.15.3.
Le LLM reviewer reste completement desactive (verdict: `ML_REGIME_DEPENDENT_WEAK_EDGE`).
La prochaine etape ne doit pas etre d'activer le LLM, mais plutot :
- d'ameliorer les features/donnees ;
- de tester les signaux ensemblistes (offline) avec prudence ;
- ou d'ajouter plus d'historique ou de granularite intrabar.

## V1.16 Ensemble Signal Lab & Reviewer Candidates

La V1.16 introduit la generation systematique de `reviewer_candidates_v1_16.jsonl`. 
Ces fichiers structurent les donnees pour une future analyse par LLM :
- Probabilites d'ensemble (moyenne/mediane)
- Niveau d'accord entre les modeles (Agreement)
- Contexte de regime (macro, derives)
- Flags de risque (dependance au regime, desaccord)

Le verdict `ENSEMBLE_REVIEWER_CANDIDATES_READY` confirme que l'ensemble produit un signal exploitable (positif apres frais) sur les fenetres de validation, justifiant la preparation des donnees pour le reviewer. 
Cependant, l'activation du LLM pour la prise de decision reste suspendue tant que la robustesse n'est pas prouvee sur l'ensemble des fenetres testees.
Codex CLI reste strictement interdit.

## V1.24.1 Reviewer toujours desactive

V1.24.1 ne change pas la philosophie reviewer. Le LLM ne doit pas etre active tant que les
filtres de selection causaux n'ont pas montre une robustesse walk-forward suffisante. Le
risque de fuite detecte en V1.24 confirme qu'il faut d'abord stabiliser le protocole de
recherche avant de demander au LLM de revoir des candidats.

Le reviewer reste donc desactive :

- pas de Codex CLI ;
- pas de holdout ;
- pas de trading live ;
- pas d'ordre reel ;
- pas d'utilisation de colonnes futures dans un contexte decisionnel.

## V1.17 Recent Regime Failure Analysis

La V1.17 confirme l'echec de la fenetre recente (2026) avec un signal net negatif apres couts. 
L'activation du LLM reviewer est **explicitement suspendue** jusqu'a nouvel ordre. 
Un module d'analyse d'echec (`failure_analysis`) est introduit pour diagnostiquer la cause de la deterioration du signal (ex: derive des features, changement de regime de marche, couts de trading trop eleves pour la volatilite). Le LLM ne doit pas compenser un mauvais signal quantitatif de base.

## V1.18 Intrabar Data Foundation
La V1.18 introduit la fondation de donnees intrabar (5m/1m) pour ameliorer le diagnostic d'echec. 
Le LLM reviewer reste **strictement desactive**. 
L'objectif est d'abord de s'assurer que le signal quantitatif peut survivre a une simulation d'execution realiste (slippage, spread, TP/SL intra-bougie) avant de depenser des ressources sur le LLM. 
Les rapports V1.18 (`intrabar_vs_4h_comparison`) servent de garde-fou : si la simulation intrabar montre que l'edge est detruit par le bruit, le verdict restera negatif meme si les probabilites de l'ensemble semblent elevees sur 4h.
Codex CLI reste strictement interdit.
