# Pre-Registered Signal Validation Protocol (V1.26)

## Contexte
Suite aux analyses de robustesse de la V1.25.1, il a été établi que le filtre `low_frequency_strict_score` est prometteur mais non robuste en raison d'une concentration de performance et d'un risque de sur-apprentissage élevé.

Cette version V1.26 fige officiellement un protocole de validation pour éviter toute optimisation ad-hoc lors des prochaines phases.

## Paramètres Figés (Locked)
- **Filtre** : `low_frequency_strict_score`
- **Policy** : `horizon_only`
- **Seuils** : Tous les paramètres de score et de fréquence sont verrouillés.
- **Données** : Seules les données post-2026-05-06 ou des sources alternatives strictement non utilisées sont admissibles pour une validation confirmatoire.

## Critères de Succès Fixes
Pour qu'un signal soit considéré comme robuste, il devra remplir TOUS les critères suivants sur une fenêtre out-of-sample :
- **Volume** : Au moins 60 trades sélectionnés.
- **PnL** : Moyenne nette > 0.
- **Concentration** : Top 10 trades < 50% de la performance totale.
- **Baseline** : Battre le `monthly_count_preserving_random` à un niveau p95.
- **Sensibilité** : Rester positif avec un modèle de coût à 0.30%.
- **Récent** : Performance positive sur la fenêtre la plus récente.

## Interdictions Strictes
- **Pas de Tuning** : Interdiction de modifier les seuils du filtre pour "améliorer" les résultats.
- **Pas de Sélection Inverse** : Interdiction d'utiliser des métriques futures (`forward_return`) pour sélectionner les trades.
- **Pas de Reviewer LLM** : Le reviewer reste désactivé tant qu'une validation statistique out-of-sample n'est pas passée.

## Preuves Actuelles
Les preuves existantes (V1.24/V1.25) sont classées comme **Discovery** et **Retrospective Robustness**. Elles ne constituent pas une preuve confirmatoire.
## Correction V1.26.1 (Complétude du Protocole)
La version V1.26.1 complète le protocole figé :
- **Verrouillage Étendu** : Les règles de sélection (`selection_rules_locked`) et les sources de données (`data_sources_locked`) sont désormais explicitement verrouillées.
- **Sources de Données Figées** :
    - Predictions: `v1_16_3`
    - Research Dataset: `alpha_scores`
    - Intrabar: `history_5m_v1_22`
- **Critères de Succès Étendus** : Ajout du PnL médian, du profit factor minimal (1.2), et de l'absence totale de fuite (leakage audit).
- **Incertitude de Durée** : L'estimation de durée (14-16 mois) est marquée comme hautement incertaine car elle dépend du rythme historique des trades (4.3 trades/mois).
- **Rapports d'Entrée** : Le script de construction valide désormais la présence de l'intégralité des rapports de robustesse V1.25.1.

## Exécution V1.27 (Paper-Forward Harness)
La version V1.27 introduit le harnais technique pour l'exécution du protocole :
- **Automatisation** : Script `run_paper_forward_validation.py` pour une application systématique.
- **Détection OOS** : Comparaison automatique avec la date pivot du 6 mai 2026.
- **Vérification Immuable** : Audit automatique des colonnes interdites et du verrouillage du protocole avant exécution.

## Mise à jour V1.26.4 (Audit de Définition Source)
La version V1.26.4 renforce la traçabilité de la définition du filtre :
- **Audit Automatique** : La définition est extraite directement de `selection_rules.py` et recoupée avec les rapports historiques.
- **Transparence Tie-Break** : Documente l'absence de tri secondaire explicite dans l'implémentation historique (Warning).
- **Audit de Sécurité** : Vérification systématique de l'absence de colonnes interdites (`forbidden_selection_columns`) dans la logique de sélection.
- **Statut de Complétude** : `PREREGISTRATION_PROTOCOL_COMPLETE_WITH_TIE_BREAK_WARNING`.

## Mise à jour V1.26.5 (Audit de Source Durci)
La version V1.26.5 apporte un niveau de preuve maximal sur l'origine du protocole :
- **Audit Strict** : Vérification de la famille de règle (`frequency`), de la causalité (`true`), et des colonnes utilisées.
- **Vérification de Cohérence** : Le count historique (122 trades) est désormais une ancre de l'audit.
- **Audit de Complétude Étendu** : 27 points de contrôle incluant l'interdiction de `future_returns`, `realized_pnl`, et `exit_reason`.
- **Extraction Status** : `SOURCE_MATCHED_CODE_AND_REPORTS_STRICT`.

## Mise à jour V1.26.6 (Intégrité de l'Archive)
La version V1.26.6 stabilise le cadre documentaire :
- **Protocole de Référence** : La V1.26.6 est établie comme l'unique protocole de référence pour les validations futures.
- **Audit de l'Archive** : Identification et documentation des mutations dans les protocoles V1.26.2 et V1.26.3.
- **Supersedes** : Les versions V1.26.2 à V1.26.5 sont formellement remplacées.
- **Status d'Intégrité** : `PREREGISTRATION_ARCHIVE_HAS_SUPERSEDED_INCONSISTENCIES` (mais validé pour la suite car isolé).
