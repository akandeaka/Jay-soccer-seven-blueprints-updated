"""
record_predictions.py
=====================

Appends today's predictions from predictions.json into prediction_history.json.

- Safe to run multiple times per day (dedupes by match name + date).
- Each entry is initialised with status="PENDING".
- Never overwrites existing entries.

Usage:
    python record_predictions.py
"""

import json
import os
import sys
from datetime import datetime


PREDICTIONS_FILE = "predictions.json"
HISTORY_FILE = "prediction_history.json"


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def main():
    preds = load_json(PREDICTIONS_FILE)
    if preds is None:
        print(f"❌ {PREDICTIONS_FILE} not found. Run main.py first.")
        sys.exit(1)

    if not isinstance(preds, list) or not preds:
        print(f"⚠️  {PREDICTIONS_FILE} is empty or malformed. Nothing to record.")
        sys.exit(0)

    history = load_json(HISTORY_FILE) or []
    if not isinstance(history, list):
        history = []

    # Build a dedupe key set
    existing_keys = {
        (e.get("date"), e.get("match"), e.get("blueprint"))
        for e in history
    }

    today = datetime.now().strftime("%Y-%m-%d")
    added = 0
    skipped = 0

    for p in preds:
        key = (today, p.get("match"), p.get("blueprint"))
        if key in existing_keys:
            skipped += 1
            continue

        entry = {
            "date": today,
            "match": p.get("match"),
            "league": p.get("league"),
            "blueprint": p.get("blueprint"),
            "play": p.get("play"),
            "confidence": p.get("confidence"),
            "odds": p.get("odds"),
            "home_odds": p.get("home_odds"),
            "draw_odds": p.get("draw_odds"),
            "away_odds": p.get("away_odds"),
            "status": "PENDING",
            "won": None,
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
            "settled_at": None,
        }
        history.append(entry)
        existing_keys.add(key)
        added += 1

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"📊 {PREDICTIONS_FILE}: {len(preds)} picks")
    print(f"📝 Added to history: {added}")
    print(f"↩️  Skipped (already recorded): {skipped}")
    print(f"💾 Total entries in {HISTORY_FILE}: {len(history)}")


if __name__ == "__main__":
    main()
