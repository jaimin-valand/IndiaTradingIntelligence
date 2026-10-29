from __future__ import annotations
import argparse
import json
import sys
from .skills import budget_size, exit_plan, risk_check, paper_order, backtest_closes

def main(argv=None):
    parser = argparse.ArgumentParser(prog="iti", description="IndiaTradingIntelligence offline research toolkit (simulation only)")
    sub = parser.add_subparsers(dest="command", required=True)
    budget = sub.add_parser("budget", help="calculate whole-share position size")
    budget.add_argument("--account", type=float, required=True)
    budget.add_argument("--max-loss", type=float, required=True)
    budget.add_argument("--entry", type=float, required=True)
    budget.add_argument("--stop", type=float, required=True)
    exitp = sub.add_parser("exit-plan", help="calculate a long trade's stop/target")
    exitp.add_argument("--entry", type=float, required=True)
    exitp.add_argument("--stop", type=float, required=True)
    exitp.add_argument("--reward-risk", type=float, default=2.0)
    risk = sub.add_parser("risk-check", help="check an order JSON file")
    risk.add_argument("file")
    risk.add_argument("--max-loss", type=float, default=50)
    risk.add_argument("--max-position", type=float, default=5000)
    paper = sub.add_parser("paper-order", help="validate an order; --approve only simulates acceptance")
    paper.add_argument("file")
    paper.add_argument("--approve", action="store_true")
    paper.add_argument("--max-loss", type=float, default=50)
    paper.add_argument("--max-position", type=float, default=5000)
    backtest = sub.add_parser("backtest", help="run close-only moving-average simulation on a JSON array")
    backtest.add_argument("file")
    backtest.add_argument("--fast", type=int, default=3)
    backtest.add_argument("--slow", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        if args.command == "budget":
            result = budget_size(args.account, args.max_loss, args.entry, args.stop)
        elif args.command == "exit-plan":
            result = exit_plan(args.entry, args.stop, args.reward_risk)
        elif args.command in ("risk-check", "paper-order"):
            with open(args.file, encoding="utf-8") as handle:
                order = json.load(handle)
            limits = {"max_loss_per_trade": args.max_loss, "max_position_value": args.max_position}
            result = risk_check(order, limits) if args.command == "risk-check" else paper_order(order, args.approve, limits)
        else:
            with open(args.file, encoding="utf-8") as handle:
                closes = json.load(handle)
            result = backtest_closes(closes, args.fast, args.slow)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
