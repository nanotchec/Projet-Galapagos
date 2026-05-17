# Batch checkpoint / resume design

Objectif : eviter de perdre un long run si quota ou limite Codex CLI est atteint.

Regles :
- Chaque decision GPT future est ecrite dans le decision cache des qu'elle est
  obtenue.
- Un checkpoint contient `completed_items`, `pending_items` et `failures`.
- Si quota atteint, le run s'arrete proprement et marque `quota_limited=true`.
- La reprise ne traite que les items pending.
- `max_concurrency=1` par defaut.

La parallelisation massive n'est pas activee en V1.11. Elle pourra devenir une
option future controlee, mais ne doit jamais contourner les limites du provider
ni augmenter le risque de perte d'etat.

Runbook resume :
- verifier le checkpoint ;
- verifier le decision cache ;
- relancer uniquement les pending ;
- ne pas refresh le cache sauf experience explicitement autorisee.
