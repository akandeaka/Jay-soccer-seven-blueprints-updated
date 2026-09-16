"""
Compare live performance against backtest expectations per blueprint.
Run weekly: python validate_blueprints.py
"""

import json
import os
from collections import defaultdict


EXPECTED_ROI = {
    'BP3':  3.77,
    'BP4':  2.10,
    'BP12': 9.54,
    'BP13': 2.10,
}


def main():
    path = "prediction_history.json"
    if not os.path.exists(path):
        print(f"No {path} yet — check back after a few days of live picks.")
        return

    with open(path) as f:
        history = json.load(f)

    stats = defaultdict(lambda: {'n': 0, 'wins': 0, 'odds_sum': 0.0})

    for entry in history:
        bp = entry.get('blueprint')
        if bp not in EXPECTED_ROI:
            continue
        won = entry.get('won')
        if won is None:
            continue
        odds = float(entry.get('odds', 1.5))
        stats[bp]['n'] += 1
        stats[bp]['odds_sum'] += odds
        if won:
            stats[bp]['wins'] += 1

    print(f"\n{'=' * 80}")
    print(f"{'BP':<6}{'Live N':<10}{'Live ROI':<12}{'Expected':<12}{'Delta':<10}{'Status'}")
    print(f"{'-' * 80}")

    for bp in ['BP3', 'BP4', 'BP12', 'BP13']:
        s = stats[bp]
        if s['n'] == 0:
            print(f"{bp:<6}{'0':<10}{'—':<12}{EXPECTED_ROI[bp]:<12}{'—':<10}no data")
            continue
        hit = s['wins'] / s['n']
        avg = s['odds_sum'] / s['n']
        roi = (hit * (avg - 1) - (1 - hit)) * 100
        delta = roi - EXPECTED_ROI[bp]
        if abs(delta) <= 3:
            status = "✅ on track"
        elif delta > 0:
            status = "🟢 better"
        else:
            status = "🔴 worse"
        print(f"{bp:<6}{s['n']:<10}{roi:+<12.2f}{EXPECTED_ROI[bp]:<12}{delta:+.2f}   {status}")

    print(f"{'=' * 80}")
    print("If any BP shows delta < -5 over 50+ picks, the edge may have decayed.")


if __name__ == "__main__":
    main()
