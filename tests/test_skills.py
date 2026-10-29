import math
import pytest
from iti.skills import (
    Candle, scan_opening_range, headline_triage, entry_check, exit_plan,
    budget_size, risk_check, backtest_closes, paper_order, price_alert,
    analyst_growth, parse_disclosure_rows,
)

def test_scanner_breakout_and_validation():
    bars = [Candle("1", 10, 11, 9, 10), Candle("2", 10, 12, 9.5, 11), Candle("3", 11, 11.5, 10, 11), Candle("4", 12, 13, 11, 12.5)]
    assert scan_opening_range(bars, 3)["signal"] == "breakout_up"
    with pytest.raises(ValueError):
        scan_opening_range(bars, 0)

def test_headlines_tagged():
    got = headline_triage(["Company reports earnings revenue growth", "Unrelated headline"])
    assert "earnings" in got[0]["tags"] and got[1]["tags"] == ["unclassified"]

def test_entry_and_exit_plan():
    assert entry_check(101, 100) == "triggered"
    assert exit_plan(100, 95, 2)["target"] == 110
    with pytest.raises(ValueError):
        exit_plan(100, 101)

def test_budget_respects_risk_and_cash():
    got = budget_size(1000, 50, 100, 90)
    assert got["quantity"] == 5 and got["planned_loss"] == 50
    assert budget_size(1000, 50, 100, 90, cash_available=250)["quantity"] == 2

def test_risk_blocks_bad_and_limits():
    order = {"symbol": "ABC", "side": "buy", "qty": 10, "entry": 100, "stop": 95}
    assert risk_check(order, {"max_loss_per_trade": 40})["verdict"] == "BLOCK"
    assert risk_check(order, {"max_loss_per_trade": 50, "max_position_value": 1000})["verdict"] == "PASS"
    assert risk_check({})["verdict"] == "BLOCK"
    assert risk_check(order, {"max_loss_per_trade": -1})["verdict"] == "BLOCK"

def test_backtest_validates_and_returns_equity():
    result = backtest_closes([10, 9, 8, 9, 11, 12, 13, 12, 10], 2, 3)
    assert len(result["equity_curve"]) == 9 and math.isfinite(result["final_equity"])
    with pytest.raises(ValueError):
        backtest_closes([1, 2], 3, 2)

def test_paper_order_never_live_and_needs_approval():
    order = {"symbol": "ABC", "side": "buy", "qty": 1, "entry": 100, "stop": 95}
    assert paper_order(order)["status"] == "awaiting_explicit_approval"
    approved = paper_order(order, approved=True)
    assert approved["status"] == "simulated_accepted"
    assert approved["live_trading"] is False and approved["broker_order_id"] is None
    assert paper_order({**order, "qty": 0}, approved=True)["status"] == "blocked"

def test_alerts_and_analyst_math():
    assert price_alert(101, 100)
    assert not price_alert(99, 100)
    assert analyst_growth(100, 125)["growth_pct"] == 25

def test_disclosure_normalization_skips_incomplete():
    rows = [{"member": "A Member", "ticker": "abc", "transaction_date": "2026-01-01", "disclosure_date": "2026-01-03"}, {"member": "", "transaction_date": "x", "disclosure_date": "y"}]
    got = parse_disclosure_rows(rows)
    assert got[0]["ticker"] == "ABC" and len(got) == 1
