"""Core implementations for the eleven research skills. No live brokerage calls."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence
import math

@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def validate(self) -> None:
        vals = (self.open, self.high, self.low, self.close, self.volume)
        if not all(math.isfinite(float(v)) for v in vals):
            raise ValueError("candle values must be finite")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close, self.low) or self.low > min(self.open, self.close, self.high):
            raise ValueError("invalid OHLC range")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")

def scan_opening_range(candles: Sequence[Candle], range_count: int = 3) -> dict:
    """Simple deterministic opening-range breakout scan on ordered candles."""
    if range_count < 1 or len(candles) <= range_count:
        raise ValueError("need more candles than range_count")
    for candle in candles:
        candle.validate()
    top = max(c.high for c in candles[:range_count])
    bottom = min(c.low for c in candles[:range_count])
    last = candles[-1]
    signal = "breakout_up" if last.close > top else "breakout_down" if last.close < bottom else "inside_range"
    return {"range_high": top, "range_low": bottom, "last_close": last.close, "signal": signal}

def headline_triage(headlines: Iterable[str]) -> list[dict]:
    """Transparent keyword triage, not a claim of sentiment or investment advice."""
    groups = {
        "earnings": ("earnings", "revenue", "eps", "guidance"),
        "deal": ("merger", "acquisition", "takeover"),
        "regulatory": ("sec", "lawsuit", "investigation", "regulator"),
        "market": ("upgrade", "downgrade", "offering", "halt"),
    }
    out = []
    for headline in headlines:
        text = str(headline).strip()
        lower = text.lower()
        tags = [tag for tag, words in groups.items() if any(word in lower for word in words)]
        out.append({"headline": text, "tags": tags or ["unclassified"], "method": "keyword rules; verify manually"})
    return out

def entry_check(close: float, trigger: float, expired: bool = False) -> str:
    if not all(math.isfinite(float(v)) and float(v) > 0 for v in (close, trigger)):
        raise ValueError("prices must be finite and positive")
    return "expired" if expired else "triggered" if close > trigger else "waiting"

def exit_plan(entry: float, stop: float, reward_risk: float = 2.0) -> dict:
    if not all(math.isfinite(float(v)) and float(v) > 0 for v in (entry, stop, reward_risk)):
        raise ValueError("values must be finite and positive")
    if stop >= entry:
        raise ValueError("long-position stop must be below entry")
    risk = entry - stop
    return {"entry": entry, "stop": stop, "risk_per_share": risk, "target": round(entry + risk * reward_risk, 8), "reward_risk": reward_risk}

def budget_size(account_value: float, max_loss: float, entry: float, stop: float, cash_available: float | None = None) -> dict:
    vals = (account_value, max_loss, entry, stop)
    if not all(math.isfinite(float(v)) and float(v) > 0 for v in vals):
        raise ValueError("budget inputs must be finite and positive")
    if stop >= entry:
        raise ValueError("stop must be below entry for a long position")
    cash = account_value if cash_available is None else cash_available
    if not math.isfinite(float(cash)) or cash < 0:
        raise ValueError("cash_available must be finite and non-negative")
    risk_qty = math.floor(max_loss / (entry - stop))
    cash_qty = math.floor(cash / entry)
    qty = max(0, min(risk_qty, cash_qty))
    return {"quantity": qty, "estimated_cost": round(qty * entry, 2), "planned_loss": round(qty * (entry - stop), 2), "risk_limit": max_loss}

def risk_check(order: dict, limits: dict | None = None) -> dict:
    limits = limits or {}
    reasons = []
    loss = None
    try:
        symbol = str(order.get("symbol", "")).strip().upper()
        side = str(order.get("side", "")).lower()
        qty = float(order.get("qty"))
        entry = float(order.get("entry"))
        stop = float(order.get("stop"))
        if not symbol or not symbol.isalnum():
            reasons.append("invalid symbol")
        if side not in ("buy", "sell"):
            reasons.append("side must be buy or sell")
        if not math.isfinite(qty) or qty <= 0 or qty != math.floor(qty):
            reasons.append("quantity must be a positive whole number")
        if not math.isfinite(entry) or entry <= 0:
            reasons.append("entry must be positive and finite")
        if not math.isfinite(stop) or stop <= 0 or stop >= entry:
            reasons.append("long order requires a positive stop below entry")
        if not reasons:
            loss = (entry - stop) * qty
            max_loss = float(limits.get("max_loss_per_trade", float("inf")))
            max_position = float(limits.get("max_position_value", float("inf")))
            if not math.isfinite(max_loss) and max_loss != float("inf") or max_loss < 0:
                reasons.append("invalid max_loss_per_trade limit")
            if not math.isfinite(max_position) and max_position != float("inf") or max_position < 0:
                reasons.append("invalid max_position_value limit")
            if loss > max_loss:
                reasons.append("max loss per trade exceeded")
            if qty * entry > max_position:
                reasons.append("max position value exceeded")
    except (TypeError, ValueError, OverflowError, AttributeError):
        reasons.append("missing or malformed numeric order fields")
        loss = None
    return {"verdict": "BLOCK" if reasons else "PASS", "reasons": reasons, "estimated_stop_loss": round(loss, 2) if loss is not None else None}

def backtest_closes(closes: Sequence[float], fast: int = 3, slow: int = 5) -> dict:
    """Toy moving-average crossover backtest; signals use past/current closes only."""
    if fast < 1 or slow <= fast:
        raise ValueError("require 1 <= fast < slow")
    if len(closes) < slow + 1:
        raise ValueError("not enough closes")
    if not all(math.isfinite(float(x)) and float(x) > 0 for x in closes):
        raise ValueError("closes must be positive finite numbers")
    cash = 1.0
    units = 0.0
    trades = 0
    equity = []
    for i, price in enumerate(closes):
        if i + 1 >= slow:
            fast_avg = sum(closes[i-fast+1:i+1]) / fast
            slow_avg = sum(closes[i-slow+1:i+1]) / slow
            if fast_avg > slow_avg and units == 0:
                units = cash / price
                cash = 0
                trades += 1
            elif fast_avg < slow_avg and units > 0:
                cash = units * price
                units = 0
                trades += 1
        equity.append(cash + units * price)
    final = equity[-1]
    return {"initial_equity": 1.0, "final_equity": round(final, 6), "return_pct": round((final - 1) * 100, 4), "trade_events": trades, "equity_curve": equity, "note": "Illustrative close-only simulation; excludes fees, slippage, taxes and survivorship bias."}

def paper_order(order: dict, approved: bool = False, risk_limits: dict | None = None) -> dict:
    """Validate and record an in-memory simulated order; never connects to a broker."""
    risk = risk_check(order, risk_limits)
    if risk["verdict"] != "PASS":
        return {"status": "blocked", "risk": risk, "order": dict(order)}
    if not approved:
        return {"status": "awaiting_explicit_approval", "risk": risk, "order": dict(order), "live_trading": False}
    return {"status": "simulated_accepted", "risk": risk, "order": dict(order), "live_trading": False, "broker_order_id": None}

def price_alert(price: float, target: float, direction: str = "above") -> bool:
    if not all(math.isfinite(float(v)) and float(v) > 0 for v in (price, target)):
        raise ValueError("prices must be positive and finite")
    if direction not in ("above", "below"):
        raise ValueError("direction must be above or below")
    return price >= target if direction == "above" else price <= target

def analyst_growth(previous: float, current: float) -> dict:
    if not all(math.isfinite(float(v)) for v in (previous, current)) or previous == 0:
        raise ValueError("values must be finite and previous must be non-zero")
    return {"previous": previous, "current": current, "change": round(current - previous, 4), "growth_pct": round((current - previous) / abs(previous) * 100, 4), "note": "Arithmetic comparison only; confirm source periods and accounting context."}

def parse_disclosure_rows(rows: Iterable[dict]) -> list[dict]:
    """Normalize already-downloaded public disclosure rows; performs no network access."""
    normalized = []
    for row in rows:
        member = str(row.get("member", "")).strip()
        ticker = str(row.get("ticker", "")).strip().upper()
        trade_date = str(row.get("transaction_date", "")).strip()
        disclosure_date = str(row.get("disclosure_date", "")).strip()
        if not member or not trade_date or not disclosure_date:
            continue
        normalized.append({"member": member, "ticker": ticker or None, "transaction_date": trade_date, "disclosure_date": disclosure_date, "asset": str(row.get("asset", "")).strip() or None, "source": str(row.get("source", "")).strip() or None})
    return normalized

SKILLS = {
    "scanner": scan_opening_range, "news": headline_triage, "entry": entry_check,
    "exit": exit_plan, "timemachine": backtest_closes, "risk": risk_check,
    "budget": budget_size, "broker": paper_order, "alerts": price_alert,
    "analyst": analyst_growth, "disclosure_tracker": parse_disclosure_rows,
}
