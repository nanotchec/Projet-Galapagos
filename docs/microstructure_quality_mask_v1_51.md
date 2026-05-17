# Microstructure Quality Mask and Data Action Plan (V1.51)

## Contexte
La version V1.50.1 a révélé des lacunes importantes dans la couverture des données microstructure, particulièrement sur l'année 2026. Cette version V1.51 définit une politique de qualité stricte sous forme de masque pour sécuriser les futures recherches.

## Règles de Qualité
Les seuils suivants ont été définis pour le masque de qualité :
- Couverture intrabar minimale : 95%
- Taux d'absence maximal : 5%
- Tolérance aux gaps : 3600 secondes
- Alignement des timestamps : 99%

## Analyse d'Impact
Le masque de qualité impacte principalement l'année 2026, qui est actuellement bloquée à 100%. Les années 2024 et 2025 restent exploitables à 100%.

- **Ratio utilisable global** : 92.4%
- **Ratio bloqué global** : 7.6%
- **Status 2026** : BLOCKED

## Plan d'Action de Données
1. **Urgent** : Ré-acquisition des données intrabar pour 2026.
2. **Rework** : Stabilisation des proxies de liquidité (Amihud) avant ré-intégration.
3. **Condition** : La couverture intrabar doit dépasser 98% pour lever le blocage sur 2026.

## Conclusion
Le masque de qualité est **PARTIAL_BUT_USABLE**. Les recherches peuvent continuer sur 2024/2025, mais 2026 doit être enrichie avant tout nouveau diagnostic de régime.

---
**RESEARCH_ONLY** : Aucun système de trading n'est activé.
