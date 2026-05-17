# Decisions d'architecture

## Pas Freqtrade comme coeur

Freqtrade est une reference utile pour dry-run, backtesting, frais, wallet simule et diagnostics.
Galapagos reste une architecture maison afin de controler le contexte LLM, le schema de decision,
le risk engine et la journalisation detaillee.

## Kraken/CCXT et Binance Futures

Kraken via CCXT fournit les OHLCV spot BTC/USD. Binance Futures est prevu pour funding et open
interest. Les donnees derivees difficiles restent exposees avec statut explicite `unavailable`.

## SQLite V1

SQLite suffit pour un agent local macOS, simplifie l'inspection et permet une migration future vers
un service permanent.

Depuis V1.1, SQLite porte aussi l'etat paper courant : cash simule et positions ouvertes.

## Streamlit V1

Streamlit donne une supervision rapide sans framework web lourd.

## LLM abstrait

Le provider prioritaire est `openai-codex`, mais le runtime local ne fournit pas encore d'appel
direct. L'interface existe, echoue proprement, et `MockLLMProvider` couvre tests et developpement.

Depuis V1.3, `openai-codex` est configurable avec `auth_mode`, `base_url`, `model`,
`timeout_seconds` et `max_retries`. En mode `chatgpt_codex`, il reste non fonctionnel tant qu'un
bridge Codex/ChatGPT n'est pas expose au processus Python local.

## Portefeuilles paper separes

Le cash paper est stocke par profil (`galapagos_30m`, `galapagos_4h`) afin que la comparaison ne
melange pas les performances des deux horizons.

## Regle stop-loss intrabar

Si une candle touche stop-loss et take-profit, le stop-loss gagne. Cette convention evite de
sur-estimer les performances en OHLCV sans donnees intrabar.

## LLM offline avant provider reel

Decision V1.7 : ajouter `llm_offline_conservative`, `llm_offline_balanced` et
`llm_offline_aggressive` avant de brancher un vrai provider.

Raison : valider le chemin complet `DecisionContext -> prompt -> raw response JSON -> parser ->
validation contextuelle -> risk engine -> paper broker` sans dependre d'une authentification ou
d'un runtime LLM externe.

Ce que cela teste : structure du contexte, schema de decision, audit via `context_hash` et
`prompt_hash`, distribution des decisions, refus risk engine et comparaison contre baselines.

Ce que cela ne prouve pas : aucune profitabilite future et aucune qualite d'un vrai LLM.

## Preparation openai-codex GPT-5.5 low

Decision V1.8A : configurer `openai-codex` pour `gpt-5.5` avec `reasoning_effort: low`, mais garder
`allow_network_calls: false` par defaut.

Raison : preparer l'integration et les diagnostics sans supposer qu'un bridge ChatGPT/Codex est
expose au processus Python local.

Le provider doit signaler clairement ce qui manque : `base_url`, gateway locale, auth compatible ou
activation explicite du reseau. Aucun secret ne doit etre logge.

Cette etape teste la preparation d'integration, pas la qualite ni la profitabilite d'un modele reel.

## Codex CLI comme provider local

Decision V1.8C : ajouter un provider `codex_cli` distinct de `openai-codex`.

Raison : le diagnostic V1.8B a valide `codex exec` en mode non interactif avec `gpt-5.5`,
`reasoning_effort: low`, `--sandbox read-only` et `--output-last-message`. Cette voie permet a
Galapagos d'obtenir une reponse JSON via le compte ChatGPT/Codex local sans cle API classique.

Limites : le provider reste experimental, limite aux samples courts, et ne prouve aucune
profitabilite. Les appels reels sont bloques par defaut avec `allow_codex_cli_calls: false`.

## Protocole anti-overfit V1.9

Decision V1.9 : ne pas optimiser GPT-5.5 sur le run V1.8C.9, car l'echantillon de 20 candidats est
trop petit et trop facile a sur-ajuster.

Galapagos ajoute donc un harnais `anti_overfit` qui decoupe l'historique BTC 4h en fenetres
temporelles non chevauchantes :

- `calibration` pour debug ;
- `validation_1` et `validation_2` pour evaluation intermediaire ;
- `holdout` pour test final intouchable.

Le dry-run selectionne les fenetres et les candidats sans appel GPT-5.5. Les appels Codex CLI reels
doivent etre lances explicitement avec `--allow-codex-cli` et le holdout cree un marqueur
`HOLDOUT_USED.txt`.

Le verdict reste volontairement prudent : un resultat positif sur une seule fenetre ne suffit pas.
Le holdout ne doit jamais servir a retoucher le prompt ; si le prompt change apres lecture du
holdout, il faut creer un nouveau holdout.

## Decision cache V1.10.5

V1.10.5 active un cache decisionnel pour les evaluations Codex GPT. Le but n'est pas d'ameliorer
la strategie, mais de stabiliser les comparaisons : une variante deterministe doit pouvoir etre
rejouee sur les memes decisions GPT au lieu de rappeler Codex CLI et subir une nouvelle variance.

Cle de cache :

- `context_hash` ;
- `prompt_hash` ;
- `model` ;
- `reasoning_effort` ;
- `prompt_mode` ;
- `constraints_config_hash` ;
- `schema_version`.

Les entrees sont stockees dans `data/decision_cache/codex_cli/`, exclu du zip et du suivi Git. Elles
contiennent la reponse brute, la decision parse, les diagnostics parser/provider, la duree et les
previews stdout/stderr tronquees. Aucun secret n'est stocke.

Construire le cache sans holdout :

```bash
python scripts/build_decision_cache.py --config configs/evaluation/btc_4h_long_only_force_close_v1_10_1.yaml --windows calibration,validation_1,validation_2 --allow-codex-cli --max-calls 60
```

Rejouer sans rappeler GPT :

```bash
python scripts/replay_cached_decisions.py --config configs/evaluation/btc_4h_long_only_force_close_v1_10_1.yaml --windows calibration,validation_1,validation_2 --use-decision-cache --cache-readonly
```

Le holdout reste bloque par defaut. Ne prechauffer le holdout qu'avec une version figee, un flag
explicite, et un protocole qui interdit toute retouche apres lecture du resultat.
## V1.11 - decision de recherche

Galapagos reste en paper/research. V1.11 ne modifie pas le prompt GPT de trading
et ne lance pas Codex CLI.

Decision d'architecture :
- mesurer d'abord la qualite des signaux avec forward returns, MFE/MAE et
  random baselines ;
- comparer toute strategie a cash et buy-and-hold BTC ;
- considerer le LLM comme reviewer futur, pas comme moteur d'alpha tant que les
  signaux quantitatifs ne montrent pas d'edge ;
- garder le holdout verrouille jusqu'a obtention d'hypotheses robustes sur
  calibration + validation.
