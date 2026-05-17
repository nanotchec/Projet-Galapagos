# Design de cache decisionnel

Ce document propose un cache de decisions pour comparer des variantes deterministes sans bruit LLM.
Il n'est pas active globalement en V1.10.4.

## Objectif

Quand le meme contexte est soumis plusieurs fois a GPT-5.5, la decision peut varier. Pour comparer
un filtre de cout, une politique de sortie ou une contrainte deterministe, il faut pouvoir reutiliser
exactement la meme decision LLM.

## Cle de cache proposee

- `context_hash`
- `prompt_hash`
- `model`
- `reasoning_effort`
- `provider_name`
- `prompt_mode`

## Valeur stockee

- raw_response ;
- decision parse ;
- parser metadata ;
- validator metadata ;
- provider duration ;
- created_at ;
- source run id.

## Usage recommande

- Activer le cache uniquement pour les evaluations comparatives.
- Ne pas l'utiliser pour masquer une erreur provider.
- Ne jamais cacher un fallback sans le marquer explicitement.
- Garder les decisions par version de prompt.

## Limite V1.10.4

Le cache est seulement documente. Il n'est pas active sans validation explicite.

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
