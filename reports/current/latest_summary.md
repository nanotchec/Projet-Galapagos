# Résumé du Projet V2.6 (Clean Forward Label Factory Preview)

- **Dernières versions validées** :
  - V2.5.2 (Feature Store Causal Preview)
  - V2.4.8 (Resampling Silver OHLCV)
  - V2.3.1 (Ingestion Raw Public Archive)
- **Version candidate** : V2.6.
- **Statut candidate** : `pending_external_audit` (en attente de validation par audit externe).

---

## Synthèse technique de la candidate V2.6

1. **Calcul Physique de Labels Forward** :
   - Calcul de simple et log returns, directions, et classification Up/Down/Flat ternaire sur 3 horizons temporels $h \in \{1, 3, 5\}$ sur données OHLCV réelles validées V2.4.
   - Utilisation d'un seuil strict fixé à $0.0005$ ($0.05\%$) pour la classification ternaire.
2. **Garantie Anti-Leakage Temporel (Causal Separation)** :
   - Le timestamp de disponibilité des labels `label_available_ts` correspond à la clôture de la barre physique la plus éloignée ($h=5$).
   - Assertion mathématique stricte `label_available_ts > decision_ts` sur toute ligne valide, ce qui exclut tout biais de prédiction futur (look-ahead bias).
3. **Nullification des Queues de Séries (Tail Rows)** :
   - Les 5 dernières lignes ($h=5$) de chaque série temporelle sont taguées comme lignes de queue (`tail_row = True`).
   - Toutes les colonnes de labels associées aux horizons invalides dans ces queues sont **strictement nullifiées** (floats à `NaN` et strings/timestamps à `None` / `NaN`), garantissant une hygiène parfaite des données.
4. **Moteur de Validation Strict V2.6** :
   - Le validateur V2.6 intègre récursivement les validateurs V2.3, V2.4 et V2.5.2.
   - Il applique un audit de structure, de checksums SHA256 des Parquets labels, et rejette toute présence de caractéristiques de la V2.5.2 ou de signaux/modèles de trading dans les labels.
5. **Release ZIP & Smoke Test V2.6** :
   - L'archive clean `projet-galapagos-v2.6-clean.zip` (84 fichiers, 901 Ko) est créée de façon reproductible.
   - L'audit et le smoke test de release s'exécutent entièrement avec succès en moins de 5 secondes dans un environnement de test isolé temporaire.
6. **Zéro Trading, Zéro ML** :
   - Les labels sont exclusivement générés à des fins de recherche descriptive historique.
   - Aucun entraînement ML, trading réel, paper live, signal de trading ou backtest n'est autorisé.
