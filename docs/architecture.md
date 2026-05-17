# Architecture

```text
donnees marche
-> normalisation
-> indicateurs
-> detection de regime
-> scenarios candidats
-> contexte structure
-> agent LLM decideur
-> validation par risk engine
-> paper broker
-> persistance positions ouvertes
-> gestion sorties stop/take-profit/duree/CLOSE
-> journalisation SQLite
-> analyse de performance
-> rapports
-> dashboard
```

Chaque module a une responsabilite limitee. Le LLM ne calcule pas les indicateurs et ne peut pas
executer d'ordre. Le risk engine est deterministe et transforme toute decision invalide en
`NO_TRADE`.

Depuis V1.1, `PaperState` recharge le cash et les positions ouvertes depuis SQLite avant chaque
cycle. Le cycle n'appelle jamais le broker si `RiskEngine.approved` vaut `False`.

## LLM offline pipeline

Depuis V1.7, Galapagos peut simuler un pipeline de decision de type LLM sans provider reel.
Le replay construit un `DecisionContext` JSON standardise, genere un prompt strict, produit une
reponse brute JSON via une policy `llm_offline_*`, puis applique le parser, la validation
contextuelle, le risk engine et le paper broker.

Ce pipeline teste les contrats, les fallbacks, les hashes d'audit, les rapports et la cage de
risque. Il ne prouve pas la profitabilite d'un futur agent LLM.

## CodexCLIProvider

Depuis V1.8C, Galapagos peut appeler Codex CLI localement avec `codex exec` :

```text
DecisionContext -> prompt strict -> subprocess codex exec -> output_last_message
-> parser JSON -> validation contextuelle -> risk engine -> paper broker
```

Le provider `codex_cli` impose `sandbox: read-only`, un timeout, une limite de taille de prompt et
un fallback `NO_TRADE` en cas d'erreur. Il n'utilise pas de cle API classique et ne lit aucun token
interne. Il s'appuie uniquement sur le CLI deja authentifie par l'utilisateur.
