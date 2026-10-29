# IndiaTradingIntelligence (development baseline)

An offline-first Python foundation for the 11 research skills: scanner, news triage, entry timing, exit planning, backtesting, risk management, position sizing, paper-order workflow, alerts, earnings arithmetic, and disclosure-row normalization.

## Important status

This is a **new baseline built because the uploaded ZIP contained no application source files**. It is not a completed reconstruction of the code on your Mac. The current broker module is deliberately a simulation only: it does not connect to Alpaca, IBKR, or any other broker; it cannot submit or cancel live orders. No real brokerage credentials are needed.

The first implementations are intentionally small and explicit. News triage uses keywords; disclosure tracking normalizes rows supplied by the caller and does not fetch filings; earnings analysis performs arithmetic on supplied values; backtesting is a toy close-only moving-average simulation. None is a prediction or investment advice. Results omit realistic transaction costs and other market frictions unless stated.

## Requirements

Python 3.10+; runtime uses only the standard library. Tests use `pytest`.

## Setup on macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install pytest
pytest -q
```

## Examples

```bash
iti budget --account 5000 --max-loss 50 --entry 100 --stop 95
iti exit-plan --entry 100 --stop 95 --reward-risk 2
```

Create `order.json`:
```json
{"symbol":"ABC","side":"buy","qty":5,"entry":100,"stop":95}
```

Check and simulate (never sends an order):
```bash
iti risk-check order.json --max-loss 25
iti paper-order order.json
iti paper-order order.json --approve
```

Backtest example requires a JSON array of positive close prices:
```bash
iti backtest closes.json --fast 3 --slow 5
```

## Safety principles

- No live trading path exists in this baseline.
- An explicit `--approve` flag only marks a simulated order accepted; it does not contact a broker.
- Every order must pass risk checks in this implementation.
- Validate all data and results independently before making decisions.
- Do not paste keys or secrets into chat or commit them to source control.

## Remaining work before production use

Real data adapters, robust exchange calendars/time zones, point-in-time data controls, event/news source verification, corporate-action handling, realistic backtest execution and costs, persistent audit trails, portfolio-level exposure limits, duplicate/idempotency handling, monitoring, dependency/security scanning, and a full independent review remain out of scope. Do not use this baseline for live trading.
