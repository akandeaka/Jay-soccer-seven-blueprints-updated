"""
validate_from_file.py
=====================

Soccer blueprint settlement validator.

Reads:
    predictions.json   — the picks to settle
    results.txt        — the actual scores

Writes:
    validation_report.md
    Telegram notification (if secrets configured)

Output:
    Prints a settlement report to stdout + sends summary to Telegram.

Format handling:
    results.txt can contain either:
      (A) Multi-line blocks, blank-line separated:
              Team A vs Team B
              RESULT: 2-1
      (B) One-line entries:
              Team A vs Team B RESULT: 2-1
"""

import json
import os
import re
import sys
import requests
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

PREDICTIONS_FILE = "predictions.json"
RESULTS_FILE = "results.txt"
REPORT_FILE = "validation_report.md"


# ============================================================
# NAME NORMALISATION
# ============================================================

STRIP_WORDS = {
    "fc", "ac", "utd", "united", "sv", "vfb", "sc", "afc",
    "cd", "ud", "cf", "if", "fk", "bk", "sk", "ik",
    "calcio", "club", "de", "the", "real", "atletico",
}


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation and common club suffixes."""
    if not name:
        return ""
    name = name.lower()
    tokens = re.split(r"[\s\.\-_]+", name)
    kept = [t for t in tokens if t and t not in STRIP_WORDS]
    return "".join(kept)


# ============================================================
# RESULTS PARSER — handles both multi-line and one-line formats
# ============================================================

def parse_validation_file(filepath: str = RESULTS_FILE) -> dict:
    """
    Parse results.txt into {normalized_match_name: {home_score, away_score}}.

    Handles both:
      - Multi-line blocks (blank-line separated):
            Team A vs Team B
            RESULT: 2-1
      - One-line entries:
            Team A vs Team B RESULT: 2-1
    """
    if not os.path.exists(filepath):
        print(f"❌ '{filepath}' not found.")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {}

    # ---- Strategy 1: split into blocks on blank lines ----
    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        match_name = None
        for line in lines:
            # One-line form: "Team A vs Team B RESULT: 2-1"
            m = re.match(
                r'^\**\s*(.+?)\s*\**\s+RESULT:\s*(\d+)\s*[-:]\s*(\d+)',
                line, re.IGNORECASE
            )
            if m and ' vs ' in m.group(1):
                nm = m.group(1).strip().strip('*').strip()
                key = normalize_name(nm)
                results[key] = {
                    'raw_name': nm,
                    'home_score': int(m.group(2)),
                    'away_score': int(m.group(3)),
                }
                match_name = None
                continue

            # Multi-line form: match name on its own line
            if ' vs ' in line and 'RESULT:' not in line.upper():
                match_name = line.strip().strip('*').strip()
                continue

            # Multi-line form: RESULT on next line
            if 'RESULT:' in line.upper() and match_name:
                score = re.search(r'(\d+)\s*[-:]\s*(\d+)', line)
                if score:
                    key = normalize_name(match_name)
                    results[key] = {
                        'raw_name': match_name,
                        'home_score': int(score.group(1)),
                        'away_score': int(score.group(2)),
                    }
                match_name = None

    # ---- Strategy 2 (fallback): scan line-by-line for one-line entries ----
    if not results:
        for line in content.split('\n'):
            line = line.strip()
            if not line or ' vs ' not in line:
                continue
            m = re.match(
                r'^\**\s*(.+?)\s*\**\s+RESULT:\s*(\d+)\s*[-:]\s*(\d+)',
                line, re.IGNORECASE
            )
            if m:
                nm = m.group(1).strip().strip('*').strip()
                key = normalize_name(nm)
                results[key] = {
                    'raw_name': nm,
                    'home_score': int(m.group(2)),
                    'away_score': int(m.group(3)),
                }

    return results


# ============================================================
# PLAY EVALUATION
# ============================================================

def evaluate_play(play: str, home: int, away: int) -> bool:
    """Return True if the predicted play won given the final score."""
    total = home + away
    p = play.lower()

    if 'straight home win' in p or p == 'home win':
        return home > away
    if 'straight away win' in p or p == 'away win':
        return away > home
    if 'full time draw' in p or p == 'draw':
        return home == away

    if 'home win + over 2.5' in p or 'home win and over 2.5' in p:
        return home > away and total > 2

    if 'draw or gg' in p or 'draw or both teams' in p:
        return home == away or (home > 0 and away > 0)
    if 'draw or under 2.5' in p:
        return home == away or total < 3
    if 'draw or over 2.5' in p:
        return home == away or total > 2

    if 'both teams to score' in p or 'btts' in p:
        btts = home > 0 and away > 0
        if ' no' in p or '- no' in p:
            return not btts
        return btts

    if 'over 1.5' in p:
        return total > 1
    if 'over 2.5' in p:
        return total > 2
    if 'over 3.5' in p:
        return total > 3
    if 'under 2.5' in p:
        return total < 3
    if 'under 3.5' in p:
        return total < 4

    if '1x &' in p or '1x and' in p:
        return home >= away
    if 'x2 &' in p or 'x2 and' in p:
        return away >= home

    return False


def find_actual_result(match_name: str, validation_results: dict):
    """Find the score for a match name using fuzzy key lookup."""
    if not match_name:
        return None
    key = normalize_name(match_name)
    if key in validation_results:
        return validation_results[key]
    # Try substring matching
    for k, data in validation_results.items():
        if key and (key in k or k in key):
            return data
    return None


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not set — skipping send.")
        return False
    if len(message) > 4000:
        message = message[:3950] + "\n…(truncated)"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=30)
        ok = r.json().get("ok", False)
        print("✅ Telegram sent." if ok else f"⚠️ Telegram error: {r.text}")
        return ok
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 60)
    print("⚽ VALIDATION ENGINE — FUZZY MATCH & SETTLEMENT")
    print("=" * 60)

    if not os.path.exists(PREDICTIONS_FILE):
        print(f"❌ '{PREDICTIONS_FILE}' not found.")
        sys.exit(1)

    with open(PREDICTIONS_FILE) as f:
        predictions = json.load(f)

    validation_results = parse_validation_file(RESULTS_FILE)
    if not validation_results:
        print(f"❌ No valid score entries retrieved from {RESULTS_FILE}")
        sys.exit(1)

    print(f"📋 Loaded {len(predictions)} predictions")
    print(f"📊 Loaded {len(validation_results)} match results\n")

    # Settle every prediction
    report_lines = []
    wins = 0
    losses = 0
    not_found = 0

    report_lines.append("# 🏁 SETTLEMENT REPORT")
    report_lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    report_lines.append("━" * 34)
    report_lines.append("📊 TOP PREDICTIONS")
    report_lines.append("━" * 34)

    for p in predictions:
        match = p.get("match", "")
        play = p.get("play", "")
        actual = find_actual_result(match, validation_results)

        if actual is None:
            not_found += 1
            report_lines.append(f"⏳ {match}")
            report_lines.append(f"   🎯 {play} | Score: NOT FOUND")
            continue

        home = actual["home_score"]
        away = actual["away_score"]
        won = evaluate_play(play, home, away)

        if won:
            wins += 1
            emoji = "✅"
        else:
            losses += 1
            emoji = "❌"

        report_lines.append(f"{emoji} {match}")
        report_lines.append(f"   🎯 {play} | Score: {home}-{away}")

    total_settled = wins + losses
    accuracy = (wins / total_settled * 100) if total_settled else 0.0

    report_lines.append("")
    report_lines.append("━" * 34)
    report_lines.append("📊 SUMMARY")
    report_lines.append(f"✅ Wins:   {wins}")
    report_lines.append(f"❌ Losses: {losses}")
    report_lines.append(f"⏳ Not found: {not_found}")
    report_lines.append(f"📈 Accuracy: {wins}/{total_settled} ({accuracy:.1f}%)")

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Telegram
    tg_message = (
        f"🏁 <b>SETTLEMENT REPORT</b>\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Wins: {wins}\n"
        f"❌ Losses: {losses}\n"
        f"⏳ Not found: {not_found}\n"
        f"📈 <b>Accuracy: {wins}/{total_settled} ({accuracy:.1f}%)</b>"
    )
    send_telegram(tg_message)

    print(f"\n💾 Report saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
