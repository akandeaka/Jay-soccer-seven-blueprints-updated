"""
validate_blueprints.py
======================

Compare live prediction performance against backtest expectations, per blueprint.

Reads:  prediction_history.json   (written by the validation workflow)
Writes: console report only — no files modified

Usage:
    python validate_blueprints.py

What it does:
  1. Loads every settled pick from prediction_history.json.
  2. Groups them by blueprint.
  3. Computes live hit rate, average odds, and ROI per blueprint.
  4. Compares live ROI against the backtest expectation.
  5. Flags any blueprint where the delta exceeds the tolerance threshold.

Interpreting the output:
  Delta within ±3          → edge holding up as expected
  Delta > +3               → outperforming backtest
  Delta < -3 (small N)     → noise, keep watching
  Delta < -5 (50+ picks)   → market has likely adapted; consider disabling
"""

import json
import os
import sys
from collections import defaultdict


# ============================================================
# EXPECTED BACKTEST RESULTS (from 55,699-match backtest)
# ============================================================

EXPECTED_ROI = {
    'BP3':  3.77,   # Draw in close matches (±0.50)
    'BP4':  2.10,   # Home Win @ 1.72-1.80, high-scoring league
    'BP12': 9.54,   # Home + Over 2.5 @ 1.20-1.30, top leagues
    'BP13': 2.10,   # Home Win @ 1.70-1.75, select leagues
    'BP14': 1.40,   # Draw in wider close matches (±0.75)
}

BP_NAMES = {
    'BP3':  'Draw (close match, ±0.50)',
    'BP4':  'Home Win @ 1.72-1.80',
    'BP12': 'Home + Over 2.5 @ 1.20-1.30',
    'BP13': 'Home Win @ 1.70-1.75',
    'BP14': 'Draw (wider close match, ±0.75)',
}

# Tolerance thresholds
DELTA_OK = 3.0          # within ±3 = on track
DELTA_MIN_N = 50        # 50+ picks before the -5 warning is meaningful
DELTA_WARN = -5.0       # below this, flag as adapted


# ============================================================
# HELPERS
# ============================================================

def compute_roi(wins: int, n: int, avg_odds: float) -> float:
    """Standard expected-value ROI per unit staked."""
    if n == 0 or avg_odds <= 1.0:
        return 0.0
    hit = wins / n
    return (hit * (avg_odds - 1) - (1 - hit)) * 100


def load_history(path: str = "prediction_history.json") -> list:
    if not os.path.exists(path):
        print(f"❌ {path} not found.")
        print("   The validation workflow writes this file daily at 01:00 UTC.")
        print("   Check back after the system has run for at least one full cycle.")
        sys.exit(0)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ {path} is not valid JSON: {e}")
        sys.exit(1)

    if isinstance(data, dict):
        # Some versions store {"records": [...]} or similar
        for key in ("records", "history", "predictions", "entries"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # If it's a dict of dates → lists, flatten
        flat = []
        for v in data.values():
            if isinstance(v, list):
                flat.extend(v)
        return flat

    return data if isinstance(data, list) else []


def entry_is_settled(entry: dict) -> bool:
    """A pick is settled when it has a definitive win/loss result."""
    if entry.get("won") is not None:
        return True
    status = str(entry.get("status", "")).upper()
    return status in ("WIN", "LOSS")


def entry_won(entry: dict) -> bool:
    if entry.get("won") is not None:
        return bool(entry["won"])
    return str(entry.get("status", "")).upper() == "WIN"


def entry_odds(entry: dict) -> float:
    for key in ("odds", "avg_odds", "price"):
        v = entry.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return 0.0


# ============================================================
# MAIN
# ============================================================

def main():
    history = load_history("prediction_history.json")
    total = len(history)
    settled = [e for e in history if entry_is_settled(e)]

    print()
    print("=" * 92)
    print("📊 LIVE PERFORMANCE vs BACKTEST EXPECTATION")
    print("=" * 92)
    print(f"Total entries in history:   {total}")
    print(f"Settled (win/loss known):   {len(settled)}")
    print(f"Pending (no result yet):    {total - len(settled)}")
    print()

    if not settled:
        print("⏳ No settled picks yet. Run this again after the validation")
        print("   workflow has processed at least one day of results.")
        return

    # Aggregate per blueprint
    stats = defaultdict(lambda: {"n": 0, "wins": 0, "odds_sum": 0.0})
    for e in settled:
        bp = e.get("blueprint")
        if bp not in EXPECTED_ROI:
            continue
        s = stats[bp]
        s["n"] += 1
        s["odds_sum"] += entry_odds(e)
        if entry_won(e):
            s["wins"] += 1

    # Report header
    print(f"{'BP':<6}{'Description':<34}{'N':<7}{'Wins':<7}"
          f"{'Hit%':<8}{'AvgOdds':<10}{'ROI%':<10}{'Expected':<10}"
          f"{'Delta':<9}{'Status'}")
    print("-" * 92)

    any_settled = False
    for bp in ["BP3", "BP4", "BP12", "BP13", "BP14"]:
        s = stats[bp]
        if s["n"] == 0:
            print(f"{bp:<6}{BP_NAMES[bp]:<34}{'0':<7}"
                  f"{'—':<7}{'—':<8}{'—':<10}{'—':<10}"
                  f"{EXPECTED_ROI[bp]:<10}{'—':<9}no data")
            continue

        any_settled = True
        avg_odds = s["odds_sum"] / s["n"]
        live_roi = compute_roi(s["wins"], s["n"], avg_odds)
        expected = EXPECTED_ROI[bp]
        delta = live_roi - expected

        # Determine status
        if s["n"] >= DELTA_MIN_N and delta < DELTA_WARN:
            status = "🔴 ADAPTED — consider disabling"
        elif abs(delta) <= DELTA_OK:
            status = "✅ on track"
        elif delta > DELTA_OK:
            status = "🟢 outperforming"
        else:
            status = "🟡 below expected (keep watching)"

        print(f"{bp:<6}{BP_NAMES[bp]:<34}{s['n']:<7}{s['wins']:<7}"
              f"{s['wins']/s['n']*100:<8.2f}{avg_odds:<10.3f}"
              f"{live_roi:+<10.2f}{expected:<10.2f}"
              f"{delta:+<9.2f}{status}")

    print("-" * 92)

    if not any_settled:
        print("No enabled blueprint has settled picks yet.")
        return

    # Summary of totals across all enabled BPs
    total_n = sum(s["n"] for s in stats.values())
    total_wins = sum(s["wins"] for s in stats.values())
    total_odds = sum(s["odds_sum"] for s in stats.values())
    if total_n:
        combined_avg = total_odds / total_n
        combined_roi = compute_roi(total_wins, total_n, combined_avg)
        print()
        print(f"Combined live performance ({total_n} settled picks):")
        print(f"   Hit rate:  {total_wins/total_n*100:.2f}%")
        print(f"   Avg odds:  {combined_avg:.3f}")
        print(f"   Live ROI:  {combined_roi:+.2f}%")
        print(f"   Backtest blended expectation: ~+4.4%")

    print()
    print("Legend:")
    print("  ✅ on track                — live ROI within ±3 of backtest")
    print("  🟢 outperforming           — live ROI more than 3 above backtest")
    print("  🟡 below expected          — small negative delta, watch closely")
    print("  🔴 ADAPTED                 — delta < -5 over 50+ picks")
    print()
    print("Action guide:")
    print("  • A single 🔴 over 50+ picks → remove that BP from ENABLED_BLUEPRINTS")
    print("  • 🔴 with N < 50            → noise, keep collecting data")
    print("  • All 🟢 or ✅              → system as designed; leave it alone")
    print("=" * 92)
    print()


if __name__ == "__main__":
    main()
