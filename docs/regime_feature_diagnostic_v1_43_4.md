# Galapagos V1.43.4 : Final Feature Recommendation Semantics Fix

## Contexte
La version V1.43.4 finalise la sémantique des recommandations pour le cycle V1.44. Elle corrige des incohérences identifiées en V1.43.3 concernant le mélange des scores alpha et des sorties de modèles.

## Changements Majeurs

### 1. Séparation Stricte Alpha vs Modèle
- La famille hybride `alpha_score_or_model_output` a été supprimée.
- Les features sont désormais classées soit en `alpha_score_family` (signaux combinés), soit en `model_output_family` (probabilités, logits).
- Les recommandations pour la V1.44 excluent désormais explicitement toute feature liée aux modèles ou aux proxys de payoff pour se concentrer sur l'ingénierie brute stable.

### 2. Intégrité de l'Inventaire
- Correction du champ `usable_raw_feature_count` pour correspondre exactement à la longueur de la liste `usable_raw_features`.
- Population explicite des listes de diagnostic :
    - `diagnostic_only_model_output_features`
    - `diagnostic_only_ev_proxy_features`
- Ces listes permettent un audit clair des variables de "leakage" potentiel sans les mélanger au set d'entraînement futur.

### 3. Durcissement du Validateur
- Le validateur rejette désormais toute recommandation contenant des familles interdites ou la valeur générique `unknown`.
- Vérification systématique de la cohérence entre les comptes déclarés et les listes physiques de features.

## État du Projet
- **Version** : V1.43.4
- **Verdict** : REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY
- **Classification** : DIAGNOSTIC_ONLY
- **Sécurité** :
    - `no_strategy_validated = true`
    - `no_paper_live = true`
    - `no_real_trading = true`

**Note : Le système V1.43.4 ne peut toujours pas passer d'ordre réel.**
