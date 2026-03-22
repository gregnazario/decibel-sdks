# Decibel Python SDK — Example Trading Bots

Example bots for Decibel testnet. Each bot demonstrates a different trading pattern.

## Prerequisites

1. **Create an API Wallet** at [app.decibel.trade/api](https://app.decibel.trade/api)
   - Connect your wallet → "Create API Wallet"
   - Copy the private key (shown once) and wallet address

2. **Get a Bearer Token** from [geomi.dev](https://geomi.dev)
   - Create a project → Add an "API Key" resource
   - Network: select "Decibel Devnet" (for testnet)
   - Copy the "Key secret" — this is your bearer token

3. **Create a `.env` file** in this directory:

```bash
cp .env.example .env
# Then edit .env with your credentials
```

4. **Install the SDK**:

```bash
cd .. && pip install -e ".[dev]"
```

## Examples

| Script | Description | Requires Private Key |
|--------|-------------|---------------------|
| `01_market_monitor.py` | Stream live prices and orderbook depth | No |
| `02_account_dashboard.py` | Monitor positions, orders, and risk metrics | No |
| `03_place_and_manage_orders.py` | Place orders, set TP/SL, cancel orders | Yes |
| `04_market_making_bot.py` | Two-sided quoting with inventory management | Yes |
| `05_risk_watchdog.py` | Emergency position closer when risk limits breach | Yes |

## Running

```bash
# Read-only examples (no private key needed)
python 01_market_monitor.py
python 02_account_dashboard.py

# Trading examples (needs PRIVATE_KEY in .env)
python 03_place_and_manage_orders.py
python 04_market_making_bot.py
python 05_risk_watchdog.py
```

## Network

All examples default to **Decibel testnet** (Netna devnet). Testnet has free funds — you can get test USDC from the faucet via the [Decibel App](https://app.decibel.trade).

To use mainnet, change the config import from `DecibelConfig.testnet()` to `DecibelConfig.mainnet()` and update your bearer token accordingly.
