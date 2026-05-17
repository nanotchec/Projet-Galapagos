# Inspiration Freqtrade

Freqtrade fait bien plusieurs choses : separation configuration/code, dry-run, backtesting, gestion
du wallet simule, prise en compte des frais, logs, diagnostics et interface de supervision.

Galapagos reprend conceptuellement :

- la discipline paper trading avant execution reelle ;
- les limites de risque configurees ;
- la separation entre strategie, configuration et execution ;
- l'importance des journaux et rapports ;
- la comparaison de profils.

Galapagos ne reprend pas :

- le moteur Freqtrade comme dependance principale ;
- son modele de strategie comme centre du systeme ;
- l'execution live ;
- une UI complete des la V1.

La raison principale est que Galapagos doit controler finement le contexte structure envoye au LLM,
le format JSON strict, le risk engine deterministe et l'audit de chaque decision agent.

