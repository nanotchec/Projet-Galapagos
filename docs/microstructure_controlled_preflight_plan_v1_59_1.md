# Documentation V1.59.1 - Controlled Collector Preflight Planning (Flags Aligned)

## 1. Contexte et Objectifs
Cette phase (V1.59.1) est une mise à jour corrective de la V1.59 visant à aligner les flags de sécurité obligatoires dans tous les rapports centraux. L'objectif est de garantir que le système porte explicitement les mentions de simulation et de restriction de fixtures.

## 2. Périmètre du Futur Preflight (Plannifié)
Le futur préflight reste strictement limité à :
- **Simulation Totale** : Utilisation de mocks pour les réponses API.
- **Réseau Désactivé** : Aucune connexion socket ne sera autorisée.
- **Écritures Limitées** : Seuls les rapports de diagnostic dans `reports/` seront autorisés.

## 3. Politiques de Sécurité Alignées
- **Network Gate** : Verrouillage strict (`network_enabled: false`).
- **Write Gate** : Interdiction d'écrire dans `data/`.
- **Dry-run Only** : Le système est configuré pour une exécution en mode test uniquement.
- **Local Fixture Only** : Utilisation exclusive de données locales de test.
- **Synthetic Sample** : Les échantillons utilisés sont synthétiques ou minimaux pour éviter tout risque de fuite ou d'exécution réelle.

## 4. Verdict et État du Système
**Verdict : MICROSTRUCTURE_PREFLIGHT_PLAN_READY**

- **Version** : V1.59.1
- **Phase Autorisée** : `controlled_local_preflight_dryrun` (V1.60+)
- **Collecte Réelle Approuvée** : NON
- **Réseau Activé** : NON
- **Infrastructure Only** : OUI
- **Safety Flags Aligned** : OUI

Le système reste dans un état de planification pure, garantissant l'absence totale d'interaction réelle avec les bourses ou le réseau.
