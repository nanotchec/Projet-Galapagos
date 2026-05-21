# Galapagos V2.6 — Clean Forward Label Factory Preview

> Correction V2.6.2 : V2.6.1 a été refusée en strict car le validateur acceptait certains chemins réalistes de dataset ML ou d'exécution, notamment `data/gold/datasets/ml_offline`. V2.6.2 conserve les schémas stricts V2.6.1 et ajoute un garde-fou physique contre les artefacts ML/dataset/backtest/execution. La candidate reste `pending_external_audit`.

Ce document décrit l'architecture technique, les spécifications physiques et les mécanismes de sécurité de la première usine de labels forward (Label Factory) de Galapagos.

---

## 1. Objectifs de la Version V2.6

La version **V2.6 — Clean Forward Label Factory Preview** introduit le calcul systématique et l'isolation stricte des labels prédictifs futurs (forward-looking labels) calculés à partir des séries OHLCV validées en V2.4.

Les principes fondamentaux de cette version sont :
- **Causalité stricte** : Pas de leakage temporel. L'alignement temporel assure qu'une décision prise à un instant $t$ ne peut accéder à un label que lorsque celui-ci est physiquement disponible dans le futur.
- **Isolation physique** : Les labels sont stockés séparément des caractéristiques (features V2.5) dans le répertoire `data/gold/labels/forward_returns/`.
- **Validation physique** : Un validateur physique rigoureux rejette toute colonne interdite (les labels ne doivent pas fuiter dans les features ou les données silver, et inversement).
- **Conformité réglementaire** : Usage exclusif de recherche historique. Aucun trading réel, modèle ML ou backtest n'est autorisé.

---

## 2. Architecture des Fichiers

L'implémentation est intégrée de façon modulaire sous le package `src/galapagos/labels/` :
- `schemas.py` : Déclaration du schéma strict `LABEL_COLUMNS_V2_6` et de la liste d'exclusion `FORBIDDEN_COLUMNS_V2_6`.
- `registry.py` : Configuration des constantes physiques (horizons `[1, 3, 5]`, seuil de classification simple `0.0005`).
- `forward_returns.py` : Moteur de calcul mathématique des returns, directions, classifications et gestion des masques d'invalidité.
- `quality.py` : Analyseur statistique pour mesurer la complétude, la monotonie temporelle et la causalité.
- `validation.py` : Validateur physique complet en charge de valider les structures, checksums, cohérences internes et absence de leakage.

---

## 3. Spécifications du Calcul Physique des Labels

Pour chaque horizon $h \in \{1, 3, 5\}$ (exprimé en nombre de barres de la timeframe concernée), les métriques suivantes sont calculées :

### 3.1. Prix Futur et Returns
- **Prix Futur (`future_close_h`)** : Représente le prix de clôture décalé dans le futur :
  $$\text{future\_close\_h}_t = \text{close}_{t+h}$$
- **Simple Return (`future_simple_return_h`)** :
  $$R^{\text{simple}}_{t, h} = \frac{\text{future\_close\_h}_t}{\text{close}_t} - 1.0$$
- **Log Return (`future_log_return_h`)** :
  $$R^{\text{log}}_{t, h} = \ln\left(\frac{\text{future\_close\_h}_t}{\text{close}_t}\right)$$

### 3.2. Direction et Classification
- **Direction (`direction_h`)** : Vaut `1.0` si le log return est positif, `-1.0` s'il est négatif, et `0.0` s'il est nul.
- **Classification Up/Down/Flat (`up_down_flat_h`)** : Classification ternaire basée sur le seuil strict de $0.0005$ ($0.05\%$) :
  $$\text{up\_down\_flat\_h}_t = \begin{cases} 
  \text{"UP"} & \text{si } R^{\text{log}}_{t, h} > 0.0005 \\
  \text{"DOWN"} & \text{si } R^{\text{log}}_{t, h} < -0.0005 \\
  \text{"FLAT"} & \text{sinon}
  \end{cases}$$

### 3.3. Alignement Temporel et Disponibilité Causale
- **Timestamp de fin (`label_end_ts_h`)** : Moment où la barre future se clôture :
  $$\text{label\_end\_ts\_h}_t = \text{close\_ts}_{t+h}$$
- **Date de Disponibilité (`label_available_ts`)** : Représente l'instant exact où l'ensemble des labels pour tous les horizons ($1$, $3$, et $5$) est physiquement connu :
  $$\text{label\_available\_ts}_t = \max_{h \in \{1, 3, 5\}} (\text{label\_end\_ts\_h}_t) = \text{label\_end\_ts\_5}_t$$
  
  Pour toute décision prise à l'instant $t$ (associée à `decision_ts`), nous avons la garantie stricte que :
  $$\text{label\_available\_ts}_t > \text{decision\_ts}_t$$
  Ce décalage temporel assure qu'aucun modèle ne pourra utiliser d'information future lors de l'entraînement ou de la prédiction (absence totale de look-ahead bias).

### 3.4. Gestion des Queues de Séries (`tail_row`)
Comme les calculs font appel à des données futures ($t+h$), les dernières lignes de chaque fichier ne disposent pas d'assez d'historique futur pour calculer les labels de tous les horizons.
- Une ligne est marquée comme `tail_row = True` si au moins un des horizons $h \in \{1, 3, 5\}$ est invalide.
- Pour ces lignes de queue, l'ensemble des métriques associées aux horizons invalides est **strictement nullifié** (`NaN` pour les floats, `None`/`NaN` pour les chaînes et timestamps) afin d'éviter toute pollution ou fausse interpolation.

---

## 4. Moteur de Validation Physique & Sécurité

Le validateur de la V2.6 applique un protocole d'audit extrêmement rigoureux :
1. **Intégrité Structurelle** : Vérification de la présence et de l'ordre exact de toutes les colonnes définies par `LABEL_COLUMNS_V2_6`.
2. **Rejet Strict des Colonnes Interdites** : Toute présence de colonnes de features V2.5 (`pct_change_1m`, `volatility_1m`, etc.) ou de signaux/modèles de trading dans les fichiers de labels est immédiatement rejetée.
3. **Causalité et Cohérence Temporelle** : Garantit mathématiquement que pour chaque ligne valide, `label_available_ts` est égal au timestamp de clôture du plus grand horizon ($h=5$) et est postérieur à `decision_ts`.
4. **Cohérence du Manifeste & Rapports** : Les métadonnées physiques (checksums SHA256 des Parquets labels, tailles de fichiers, nombre de lignes) doivent correspondre exactement aux informations consignées dans les manifestes JSON.
5. **Schéma strict V2.6.1** : Le manifest et le rapport JSON refusent toute clé inattendue et le rapport doit être une projection déterministe du manifest.

---

## 5. Clause de Non-Trading & Non-ML

Conformément à la charte Galapagos :
> [!WARNING]
> La version V2.6 est une préversion technique ("Preview") conçue à des fins exclusives de recherche historique (Data/Research Only).
>
> Il est strictement interdit d'utiliser ces labels pour :
> 1. Entraîner des modèles d'apprentissage automatique (Machine Learning / Deep Learning).
> 2. Générer des signaux de trading en temps réel ou simulé.
> 3. Soumettre des ordres d'achat ou de vente à un courtier ou une bourse.
> 4. Exécuter un backtest d'une quelconque stratégie d'investissement.
