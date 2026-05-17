# Documentation V1.59 - Controlled Collector Preflight Planning

## 1. Contexte et Objectifs
Cette phase (V1.59) établit le cadre de planification pour un futur préflight local contrôlé. L'objectif est de définir les frontières de sécurité et les protocoles de vérification sans aucune exécution réelle.

## 2. Périmètre du Futur Preflight (Plannifié)
Le futur préflight sera limité à :
- **Simulation Totale** : Utilisation de mocks pour les réponses API.
- **Réseau Désactivé** : Aucune connexion socket ne sera autorisée.
- **Écritures Limitées** : Seuls les rapports de diagnostic dans `reports/` seront autorisés.

## 3. Politiques de Sécurité Définies
- **Network Gate** : Verrouillage strict (`network_enabled: false`). Toute activation future nécessite une approbation séparée.
- **Write Gate** : Interdiction d'écrire dans `data/`. Aucun fichier parquet/csv ne doit être créé.
- **Stop Conditions** : Arrêt immédiat et rollback si une activité non autorisée (réseau, écriture data) est détectée.

## 4. Plan de Test Dry-run
Un futur dry-run devra valider :
1. L'intégrité de la coupure réseau.
2. L'efficacité du blocage des écritures data.
3. La conformité du schéma des manifests simulés.
4. Le respect de la politique de causalité des timestamps.

## 5. Verdict et État du Système
**Verdict : MICROSTRUCTURE_PREFLIGHT_PLAN_READY**

- **Phase Autorisée** : `controlled_local_preflight_dryrun` (V1.60+)
- **Collecte Réelle Approuvée** : NON
- **Réseau Activé** : NON
- **Infrastructure Only** : OUI

Le système reste dans un état de planification pure, garantissant l'absence totale d'interaction réelle avec les bourses ou le réseau.
