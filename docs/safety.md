# Securite

- Paper trading only.
- Aucun ordre reel.
- Aucune cle API d'execution necessaire.
- `PaperBroker.create_order` leve `RealTradingDisabledError`.
- Le risk engine impose stop loss, limites de risque, limites de pertes et kill switch.
- Le cycle n'appelle pas `PaperBroker.execute_decision` si le risk engine refuse.
- Toute reponse LLM invalide devient `NO_TRADE`.
- Le provider `openai-codex` existe comme interface mais n'a pas d'appel runtime actif en V1 locale.
- Un test statique scanne `src/` contre les patterns d'execution reelle dangereux.
- Les comptes paper sont separes par profil depuis V1.3.
- En V1.8A, GPT-5.5 low reasoning est prepare pour tester stabilite et format, pas pour prouver
  une performance.
- Les appels reseau LLM sont desactives par defaut via `allow_network_calls: false`.
- Tout provider reel indisponible doit echouer proprement et retomber vers diagnostic/fallback, pas
  vers une execution.
- Les secrets ne doivent jamais etre logges.
- Les reponses invalides, les donnees indisponibles utilisees ou les validations echouees menent a
  `NO_TRADE`.
- En V1.8C, `CodexCLIProvider` utilise uniquement `codex exec` via `subprocess` avec `shell=False`,
  `--sandbox read-only`, timeout obligatoire et `--output-last-message`.
- `allow_codex_cli_calls` vaut `false` par defaut. Un appel reel au CLI doit etre autorise
  explicitement par flag ou configuration.
- Le provider ne lit pas de tokens internes et ne logge pas de secrets. Les sorties stdout/stderr
  sont tronquees dans les metadonnees.

## Sorties paper

Pour une candle OHLCV, le stop-loss est prioritaire si stop-loss et take-profit sont touches dans la
meme candle. Ce choix est conservateur, car Galapagos ne connait pas l'ordre intrabar exact.
