# Data Provider Decision Matrix

Cette matrice compare les sources de donnees derivees pour Galapagos.
Les couts exacts ne sont pas inventes: ils restent `requires manual check` quand ils ne sont pas verifies.

## Decision actuelle (V1.17)

Ne pas acheter de provider tant que les donnees publiques ne montrent pas un signal derive robuste.
Cependant, la V1.17 introduit un module `data_gap_analysis` qui diagnostique si l'echec du signal sur les fenetres recentes (2026) est du a l'absence de donnees granulaires (ex: intrabar data, liquidations precises, aggregate OI). Si ce rapport recommande un provider payant pour ameliorer les features, une revue detaillee sera necessaire, mais **l'achat reste suspendu**.

## Providers

### Binance public

- Cout mensuel: free
- Funding: partial
- Open interest: partial
- Liquidations: limited_or_unavailable
- Agregat multi-exchange: no
- Score priorite: 4
- Note: Best free starting point, but not enough for full liquidation/multi-exchange research.

### Bybit public

- Cout mensuel: free
- Funding: partial
- Open interest: partial
- Liquidations: limited_or_unavailable
- Agregat multi-exchange: no
- Score priorite: 4
- Note: Complements Binance for funding and OI, but public breadth is limited.

### CoinGlass

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: yes
- Agregat multi-exchange: yes
- Score priorite: 9
- Note: Watchlist only; purchase needs a public-data signal candidate first.

### CryptoQuant

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: yes
- Agregat multi-exchange: yes
- Score priorite: 7
- Note: Potentially strong on on-chain/exchange derivatives; price must be checked.

### Kaiko

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: unknown
- Agregat multi-exchange: yes
- Score priorite: 7
- Note: Institutional quality, likely overkill until signal is proven.

### Glassnode

- Cout mensuel: requires manual check
- Funding: partial
- Open interest: partial
- Liquidations: unknown
- Agregat multi-exchange: partial
- Score priorite: 3
- Note: More useful if macro/on-chain context becomes central.

### CCData

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: unknown
- Agregat multi-exchange: yes
- Score priorite: 7
- Note: Candidate if exchange-normalized market data becomes priority.

### Amberdata

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: yes
- Agregat multi-exchange: yes
- Score priorite: 9
- Note: Likely expensive; only justify after public signal evidence.

### Laevitas

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: yes
- Agregat multi-exchange: yes
- Score priorite: 9
- Note: Derivatives-focused watchlist provider.

### Coinalyze

- Cout mensuel: requires manual check
- Funding: yes
- Open interest: yes
- Liquidations: yes
- Agregat multi-exchange: yes
- Score priorite: 8
- Note: Potential lower-cost alternative to evaluate manually.
