# Calibration & Expected Value Foundation (V1.30)

## Objectif
Cette version établit les bases scientifiques pour évaluer si les probabilités produites par les modèles ML de Galapagos sont exploitables économiquement. Elle remplace l'approche par seuil brut (`prob >= 0.65`) par une analyse de calibration et d'espérance mathématique (Expected Value).

## Méthodologie

### 1. Audit Point-in-Time
Toutes les colonnes sont auditées pour garantir qu'aucune donnée future (outcome) n'est présente dans la frame de sélection.
- **Selection Frame** : Uniquement colonnes causales connues au timestamp T.
- **Outcome Frame** : Uniquement colonnes de résultat (forward returns, actual target) connues à T+N.

### 2. Métriques de Calibration
Nous mesurons la fidélité des probabilités prédites par rapport aux fréquences observées :
- **Brier Score** : Mesure globale de l'erreur quadratique moyenne.
- **ECE (Expected Calibration Error)** : Différence moyenne entre confiance et précision par bins.
- **Reliability Diagrams** : Visualisation du gap de calibration par tranches de probabilité.

### 3. Expected Value (EV) Proxy
La formule d'espérance nette utilisée pour le diagnostic est :
`EV = p * MeanWin - (1-p) * MeanLoss - Costs`

Où :
- `p` est la probabilité prédite (actuellement non calibrée).
- `MeanWin` est le gain moyen conditionnel aux prédictions du bin.
- `MeanLoss` est la perte moyenne conditionnelle.
- `Costs` est un proxy de coût (commissions + slippage).

## Résultats V1.30

### Calibration Globale
- **ECE** : 0.148 (Indique un sur-confiance ou un drift du modèle).
- **Status** : `CALIBRATION_DEGRADED`.

### Diagnostic EV
Le diagnostic montre que même avec des probabilités élevées (>0.70), l'espérance nette est souvent érodée par :
1. Une asymétrie de payoff défavorable (MeanLoss > MeanWin).
2. Le drag des coûts de transaction.
3. Le manque de calibration des probabilités brutes.

## Prochaines Étapes (V1.31)
- Implémenter une calibration Walk-Forward (Isotonic Regression ou Platt Scaling).
- Construire une matrice de régimes causaux pour adapter l'EV au contexte de marché.
- Développer des filtres basés sur l'EV nette (EV-net filtering).
