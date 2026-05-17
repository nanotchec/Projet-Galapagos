# Causal Cost-Aware Signal Research (V1.29)

Ce document décrit la phase de recherche exploratoire initiée après l'invalidation du filtre rétrospectif `low_frequency_strict_score` en V1.28.1.

## Objectif
L'objectif de la V1.29 est d'identifier des familles de filtres **strictement causaux** et **cost-aware**, capables de prendre une décision d'exécution au moment exact du signal, sans connaissance du futur.

## Familles de Filtres Explorées
- **Probability Threshold** : Utilisation d'un seuil fixe sur `predicted_probability`.
- **First Above Threshold Per Period** : Sélection du premier signal de la semaine qui dépasse un certain seuil. Contrairement au "weekly top score", cette règle est causale car elle s'arrête au premier candidat valide.
- **Causal Running Top Score** : Signal si le score actuel est le meilleur vu *jusqu'à présent* dans la période.
- **Cooldown Filter** : Limitation de la fréquence par un délai minimal entre deux trades.

## Méthodologie d'Audit
Chaque filtre implémenté est passé au crible d'un audit de causalité pour vérifier :
- Qu'il n'utilise pas de fonctions de tri sur l'ensemble de la période (`groupby().max()`).
- Qu'il ne dépend pas des outcomes futurs (`net_pnl`, `forward_return`).

## Résultats Exploratoires
Les résultats de cette version sont strictement **exploratoires**. Aucun filtre identifié n'est considéré comme "validé" pour un usage réel. Ils servent à alimenter la réflexion pour un futur protocole de validation pré-enregistré (V1.30).

## Conclusion
La V1.29 démontre qu'il existe des alternatives causales prometteuses. La prochaine étape consiste à formaliser l'un de ces filtres dans un protocole de validation rigoureux.
