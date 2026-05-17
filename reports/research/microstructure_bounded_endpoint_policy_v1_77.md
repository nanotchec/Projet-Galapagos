# Microstructure Bounded Endpoint Policy

```json
{
  "source": "Binance",
  "endpoint_type": "Public Unauthenticated",
  "symbol": "BTCUSDT",
  "url_template": "https://api.binance.com/api/v3/trades?symbol={symbol}&limit={limit}",
  "endpoint_allowed": true,
  "endpoint_authentication_required": false,
  "secrets_required": false,
  "authenticated_request_allowed": false
}
```
