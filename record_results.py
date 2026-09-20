"""
record_results.py
=================

Reads results.txt (final scores) and settles matching picks in
prediction_history.json.

results.txt format (one result per line):
    Team A vs Team B RESULT: 2-1

Fuzzy matching handles common name variations (FC, Utd, City, etc.).

Usage:
    python record_results.py
    python record_results.py --results path/to/results.txt
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime


HISTORY_FILE = "prediction_history.json"
RESULTS_FILE = "results.txt"


# ============================================================
# NAME NORMALISATION
# ============================================================

STRIP_WORDS = {
    "fc", "ac", "utd", "united", "sv", "vfb", "sc", "afc",
    "cd", "ud", "cf", "if", "fk", "bk", "sk", "ik", "fk",
    "calcio", "club", "de", "the", "real", "atletico",
}


def normalise(name: str) -> str:
    """Lowercase, strip punctuation and common club suffixes."""
    if not name:
        return ""
    name = name.lower()
    tokens = re.split(r"[\s\.\-_]+", name)
    kept = [t for t in tokens if t and t not in STRIP_WORDS]
    return "".join(kept)


# ============================================================
# LOADING
# ============================================================

def load_history(path):
    if not os.path.exists(path):
        print(f"❌ {path} not found.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_results_file(path):
    """Returns list of (match_string, home_score, away_score)."""
    if not os.path.exists(path):
        print(f"❌ {path} not found.")
        sys.exit(1)

    results = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or " vs " not in line:
                continue
            if "RESULT:" not in line.upper():
                continue

            # Split at RESULT:
            match_part, result_part = re.split(r"RESULT\s*:", line,
                                                maxsplit=1, flags=re.IGNORECASE)
            match_name = match_part.strip()
            score = re.search(r"(\d+)\s*[-:]\s*(\d+)", result_part)
            if not score:
                continue
            results.append((
                match_name,
                int(score.group(1)),
                int(score.group(2)),
            ))
    return results


# ============================================================
# PLAY EVALUATION
# ============================================================

def evaluate_play(play: str, home: int, away: int) -> bool:
    """Determine if the predicted play won given the final score."""
    total = home + away
    p = play.lower()

    # Straight results
    if "straight home win" in p or p == "home win":
        return home > away
    if "straight away win" in p or p == "away win":
        return away > home
    if "full time draw" in p or p == "draw":
        return home == away

    # Combined home + goals
    if "home win + over 2.5" in p or "home win and over 2.5" in p:
        return home > away and total > 2

    # Draw + goals
    if "draw or gg" in p or "draw or both teams" in p:
        return home == away or (home > 0 and away > 0)
    if "draw or under 2.5" in p:
        return home == away or total < 3
    if "draw or over 2.5" in p:
        return home == away or total > 2

    # BTTS
    if "both teams to score" in p or "btts" in p:
        btts = home > 0 and away > 0
        if " no" in p or "- no" in p:
            return not btts
        return btts

    # Goals
    if "over 1.5" in p:
        return total > 1
    if "over 2.5" in p:
        return total > 2
    if "over 3.5" in p:
        return total > 3
    if "under 2.5" in p:
        return total < 3
    if "under 3.5" in p:
        return total < 4

    # Double chance
    if "1x &" in p or "1x and" in p:
        return home >= away
    if "x2 &" in p or "x2 and" in p:
        return away >= home

    # Default: cannot evaluate
    return False


# ============================================================
# MATCHING
# ============================================================

def match_name_to_result(match_name, results_normalised):
    """Try to find a result entry matching this match."""
    target = normalise(match_name)
    if not target:
        return None
    if target in results_normalised:
        return results_normalised[target]

    # Fuzzy: check if either is a substring of the other
    for key, value in results_normalised.items():
        if target in key or key in target:
            return value
    return None


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=RESULTS_FILE,
                        help="Path to results file")
    args = parser.parse_args()

    history = load_history(HISTORY_FILE)
    raw_results = parse_results_file(args.results)

    if not raw_results:
        print(f"⚠️  No valid results found in {args.results}.")
        print("    Expected lines like: 'Team A vs Team B RESULT: 2-1'")
        return

    results_normalised = {
        normalise(m): (h, a) for m, h, a in raw_results
    }

    settled = 0
    unmatched_picks = []

    for entry in history:
        if entry.get("status") != "PENDING":
            continue

        found = match_name_to_result(entry.get("match", ""), results_normalised)
        if found is None:
            unmatched_picks.append(entry.get("match"))
            continue

        home_score, away_score = found
        won = evaluate_play(entry.get("play", ""), home_score, away_score)

        entry["status"] = "WIN" if won else "LOSS"
        entry["won"] = won
        entry["home_score"] = home_score
        entry["away_score"] = away_score
        entry["settled_at"] = datetime.now().isoformat(timespec="seconds")
        settled += 1

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"📄 Results parsed from {args.results}: {len(raw_results)}")
    print(f"✅ Picks settled: {settled}")

    if unmatched_picks:
        print(f"⚠️  {len(unmatched_picks)} pending picks had no matching result:")
        for m in unmatched_picks[:10]:
            print(f"     - {m}")
        if len(unmatched_picks) > 10:
            print(f"     ... and {len(unmatched_picks) - 10} more")


if __name__ == "__main__":
    main()

