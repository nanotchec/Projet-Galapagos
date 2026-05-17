# Methodologie research V1.11

V1.11 separe la qualite du signal du backtest trading. Un signal peut avoir un
forward return interessant tout en etant non tradable apres frais, slippage,
drawdown ou contraintes de risque.

Les labels forward returns, MFE et MAE sont research-only. Ils utilisent le futur
uniquement pour evaluer un signal deja forme, jamais pour prendre une decision.

Chaque signal doit etre compare a des baselines simples :
- cash / no trade ;
- buy-and-hold BTC ;
- entrees aleatoires de meme frequence ;
- filtres de tendance simples.

Le LLM ne doit pas etre considere comme moteur d'alpha tant que les signaux
quantitatifs ne montrent pas d'edge brut robuste. Son role futur preferable est
celui de reviewer/risk analyst sur un candidat statistique.

Les mini-echantillons ne prouvent rien. Sous 30 observations, le rapport doit
emettre un warning fort. Sous 100 observations, la confiance reste faible.

## V1.24 Signal Selection
La selection cost-aware doit etre evaluee avant toute activation du reviewer LLM.
Un filtre de signaux doit etre compare a :
- all candidates ;
- no trade ;
- random same-count ;
- policy baseline existante.

Un filtre qui ameliore le net moyen mais ne bat pas random same-count reste non valide.
Un filtre positif avec moins de 30 trades reste un simple signal de recherche.
Le holdout reste verrouille tant qu'aucun signal robuste n'est observe sur l'historique intrabar continu.

## V1.24.1 Causalite des filtres

Les colonnes de labels futurs (`forward_return_*`, MFE/MAE futurs, PnL realise,
exit_reason) peuvent servir a evaluer une decision deja formee, mais pas a selectionner
les candidats. Tout filtre candidat doit declarer ses colonnes utilisees et son statut
causal. Les champs diagnostic-only sont exclus du choix du meilleur filtre.

Un filtre observe sur tout l'historique doit ensuite etre regarde en walk-forward. Un
resultat positif global sans stabilite temporelle reste une hypothese, pas un edge valide.

## V1.18 Intrabar Foundation
## V1.36 Infrastructure Freeze (v1.36.8)

À partir de la V1.36, toute recherche doit s'appuyer sur l'Univers de Trade Canonique Reproductible. Cet univers fige l'unité de trade, les politiques de jointure, de déduplication et de warmup. La séparation entre `selection_frame` (causale) et `outcome_frame` (future) est strictement appliquée et auditée via un fingerprint stable. La V1.36.8 durcit la traçabilité des releases en forçant l'inclusion explicite de preuves pour les artefacts de recommandation. Aucune validation de stratégie n'est autorisée durant cette phase d'infrastructure.

## V1.37.2 Data Integrity Enforcement (Real Data Split)
A partir de la V1.37.2, l'intégrité des datasets canoniques est protégée par des gardes automatisés :
- `input_path_guard` : bloque toute donnée provenant de répertoires non officiels (mock, scratch, tmp).
- `count_sanity_guard` : vérifie que le volume de données correspond à la baseline historique (171 648 lignes).
- L'alignement documentaire de la cohérence (`consistency_check_status`) est strictement exigé pour toute release.
