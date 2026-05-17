# Causal Executability Audit (V1.28)

Ce document décrit les résultats de l'audit de causalité réalisé sur le filtre de référence `low_frequency_strict_score` (meilleur score par période de 7 jours).

## Problématique
La sélection du "meilleur score de la semaine" pose une question fondamentale d'exécutabilité : peut-on prendre cette décision en temps réel ?
Si la décision nécessite de comparer un score de lundi avec celui de jeudi avant de choisir, alors le trade de lundi ne peut pas être pris lundi.

## Résultats de l'Audit

### Audit Sémantique
La règle est classée comme **NON_CAUSAL_FULL_PERIOD_SELECTION** car elle utilise une fonction `groupby("period")` suivie d'un tri par score sur l'ensemble de la période.

### Détection de Lookahead
L'audit empirique confirme que dans la majorité des cas, le signal sélectionné se produit avant la fin de la période, mais sa sélection n'est confirmée qu'après avoir observé les signaux restants de la semaine.

### Verdict d'Exécutabilité
La règle est classée comme **RETROSPECTIVE_ONLY**. Elle ne peut pas être exécutée en temps réel telle qu'elle est définie dans le protocole V1.26.6.

## Mise à jour V1.28.1 : Correction d'Incohérence
La version V1.28.1 corrige les rapports intermédiaires pour aligner strictement tous les indicateurs sur le verdict de non-causalité.

### Reclassification Officielle
- **Statut du Filtre** : RETROSPECTIVE_DISCOVERY_ONLY.
- **Protocoles Invalidés pour le Live** : V1.26.6, V1.27.4.
- **Règle de Sélection** : `highest_score_per_period` est confirmée comme structurellement non-causale pour une exécution live directe.

## Conséquences
1. **Reclassification** : Le protocole V1.26.6 est reclassé comme **RETROSPECTIVE_DISCOVERY_ONLY**.
2. **Harnais Forward** : Le harnais V1.27.4 est valide techniquement mais la stratégie auditée ne doit pas être utilisée pour une validation paper-forward live sans une règle de décision causale.
3. **Recherche Future** : La version V1.29 devra impérativement implémenter des filtres causaux (ex: seuils fixes) et cost-aware.

## Conclusion
Bien que la stratégie `low_frequency_strict_score` soit statistiquement intéressante, son implémentation actuelle est un oracle intra-semaine. Elle sert de preuve de concept mais pas de protocole de trading exécutable.
