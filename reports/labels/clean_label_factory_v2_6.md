# Rapport de Qualité — Galapagos V2.6 Clean Forward Label Factory

Ce document fournit une analyse exhaustive de la qualité physique, structurelle et causale des labels forward générés par la version **V2.6**. 

---

## 1. Objectif technique
La version V2.6 établit un processus rigoureux de labellisation forward, séparé à 100% du stockage des caractéristiques (features) de la V2.5.2. Ces labels sont calculés à partir de la série temporelle d'OHLCV validée V2.4.

---

## 2. Intrants et Extrants
- **Données sources (Input) :** Série OHLCV Parquet Silver V2.4.
- **Labels générés (Output) :** Fichiers Parquet Gold sous `data/gold/labels/forward_returns/`.

---

## 3. Définition des horizons et classification
- **Horizons :** Horizons de projection de barres $h \in [1, 3, 5]$
- **Seuil (Threshold) :** Classification catégorielle avec seuil fixe de `0.0005`.
- **Formule returns :** 
  - $R_t^s = \frac{\text{close}_{t+h}}{\text{close}_t} - 1.0$ (Simple Return)
  - $R_t^l = \ln\left(\frac{\text{close}_{t+h}}{\text{close}_t}\right)$ (Log Return)
- **Classification UP/DOWN/FLAT :**
  - `"UP"` si $R_t^l > 0.0005$
  - `"DOWN"` si $R_t^l < -0.0005$
  - `"FLAT"` sinon.

---

## 4. Règles strictes de non-leakage et de causalité
- **Séparation causale :** Pour toute observation avec labels valides, l'horodatage de disponibilité de ces labels (`label_available_ts`) est garanti strictement supérieur à la date de décision (`decision_ts`).
- **Nullification de queue (Tail Rows) :** Les dernières $h$ lignes de chaque timeframe ne disposant pas d'un horizon futur suffisant sont explicitement marquées avec `label_valid = false` et leurs valeurs sont nulles (None/NaN) pour interdire toute extrapolation.
- **Isolation :** Aucun label n'est écrit ou fusionné dans le dossier des features Gold. Aucun fichier de dataset ML fusionné n'est créé.

---

## 5. Synthèse de la qualité par timeframe

### Timeframe : 1m
- **Lignes totales :** 1440
- **Lignes attendues :** 1440
- **Doublons détectés :** 0
- **Lignes de queue (Tail Rows) :** 5
- **Séparation causale validée :** Oui
- **Présence de colonnes interdites :** Non (PASS)
- **Validité des horodatages de queue :** Oui
- **Nombre de labels valides par horizon :**
  - Horizon 1 : 1439 valides
  - Horizon 3 : 1437 valides
  - Horizon 5 : 1435 valides

### Timeframe : 5m
- **Lignes totales :** 288
- **Lignes attendues :** 288
- **Doublons détectés :** 0
- **Lignes de queue (Tail Rows) :** 5
- **Séparation causale validée :** Oui
- **Présence de colonnes interdites :** Non (PASS)
- **Validité des horodatages de queue :** Oui
- **Nombre de labels valides par horizon :**
  - Horizon 1 : 287 valides
  - Horizon 3 : 285 valides
  - Horizon 5 : 283 valides

### Timeframe : 15m
- **Lignes totales :** 96
- **Lignes attendues :** 96
- **Doublons détectés :** 0
- **Lignes de queue (Tail Rows) :** 5
- **Séparation causale validée :** Oui
- **Présence de colonnes interdites :** Non (PASS)
- **Validité des horodatages de queue :** Oui
- **Nombre de labels valides par horizon :**
  - Horizon 1 : 95 valides
  - Horizon 3 : 93 valides
  - Horizon 5 : 91 valides

### Timeframe : 1h
- **Lignes totales :** 24
- **Lignes attendues :** 24
- **Doublons détectés :** 0
- **Lignes de queue (Tail Rows) :** 5
- **Séparation causale validée :** Oui
- **Présence de colonnes interdites :** Non (PASS)
- **Validité des horodatages de queue :** Oui
- **Nombre de labels valides par horizon :**
  - Horizon 1 : 23 valides
  - Horizon 3 : 21 valides
  - Horizon 5 : 19 valides

---

## 6. Sécurité et limitations de conformité
- **public_read_only :** True
- **orders_enabled :** False
- **trading_enabled :** False
- **ml_enabled :** False
- **labels_enabled :** True
- **backtest_enabled :** False
- **paper_live_enabled :** False

> [!IMPORTANT]
> - V2.6 produit uniquement des labels forward separes sur BTCUSDT 2024-01-15 a partir des donnees OHLCV V2.4 validees.
> - V2.6 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.
> - V2.6 n'autorise aucun paper live et aucun trading reel.
