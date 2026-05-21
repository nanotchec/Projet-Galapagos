# Public Market Ingestion V2.3

## Statut

- Statut final : `PASS`
- Source : `binance_public_archive`
- Symbole : `BTCUSDT`
- Timeframe : `1m`
- Date : `2024-01-15`
- Run : `v2_3_20260519T151302Z_801c7cad`

## Qualite physique

- Lignes : `1440`
- Lignes attendues : `1440`
- Min event_ts : `2024-01-15T00:00:00Z`
- Max event_ts : `2024-01-15T23:59:00Z`
- Min close_ts : `2024-01-15T00:00:59.999000Z`
- Max close_ts : `2024-01-15T23:59:59.999000Z`
- Doublons : `0`
- Trous temporels : `0`
- Violations OHLC : `0`
- Volumes negatifs : `0`
- Lignes avec null critique : `0`
- Checksum raw : `281154f7aab59486732bbe9ad19e8ad9cbaeb7142565cce4b3edf6406301ebf8`
- Checksum silver : `1ca0840df651680f5ede34a719d06539225ea075dfbd525865fa24d78648eb0f`

## Details des trous

- Aucun trou detecte.

## Securite

- Public read-only : `True`
- Authentification : `False`
- Cle API : `False`
- Endpoint prive : `False`
- Ordres : `False`
- Paper live : `False`
- Trading : `False`
- ML : `False`
- Labels : `False`
- Backtest : `False`

## Limitations

- V2.3 couvre une seule source publique read-only, un seul symbole, un seul timeframe et une seule journee.
- V2.3 ne valide aucune strategie, aucun modele ML, aucun signal, aucun backtest et aucun trading.

V2.3 ne valide aucune strategie. V2.3 ne valide aucun modele ML. V2.3 ne produit aucun signal de trading. V2.3 ne produit aucun ordre. V2.3 n'autorise aucun paper live. V2.3 est uniquement une preview d'ingestion de donnees publiques reelles.
