"""
validate_from_file.py
=====================

Soccer blueprint settlement validator with per-blueprint breakdown.

Reads:
    predictions.json   — the picks to settle
    results.txt        — the actual scores

Writes:
    validation_report.md
    Telegram notification (if secrets configured)
"""

import json
import os
import re
import sys
import requests
from collections import defaultdict
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

PREDICTIONS_FILE = "predictions.json"
TOP30_FILE = "top_30_predictions.json"
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
    if not name:
        return ""
    name = name.lower()
    tokens = re.split(r"[\s\.\-_]+", name)
    kept = [t for t in tokens if t and t not in STRIP_WORDS]
    return "".join(kept)


# ============================================================
# RESULTS PARSER — handles both formats
# ============================================================

def parse_validation_file(filepath: str = RESULTS_FILE) -> dict:
    if not os.path.exists(filepath):
        print(f"❌ '{filepath}' not found.")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {}

    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        match_name = None
        for line in lines:
            m = re.match(
                r'^\**\s*(.+?)\s*\**\s+RESULT:\s*(\d+)\s*[-:]\s*(\d+)',
                line, re.IGNORECASE
            )
            if m and ' vs ' in m.group(1):
                nm = m.group(1).strip().strip('*').strip()
                results[normalize_name(nm)] = {
                    'raw_name': nm,
                    'home_score': int(m.group(2)),
                    'away_score': int(m.group(3)),
                }
                match_name = None
                continue

            if ' vs ' in line and 'RESULT:' not in line.upper():
                match_name = line.strip().strip('*').strip()
                continue

            if 'RESULT:' in line.upper() and match_name:
                score = re.search(r'(\d+)\s*[-:]\s*(\d+)', line)
                if score:
                    results[normalize_name(match_name)] = {
                        'raw_name': match_name,
                        'home_score': int(score.group(1)),
                        'away_score': int(score.group(2)),
                    }
                match_name = None

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
                results[normalize_name(nm)] = {
                    'raw_name': nm,
                    'home_score': int(m.group(2)),
                    'away_score': int(m.group(3)),
                }

    return results


# ============================================================
# PLAY EVALUATION
# ============================================================

def evaluate_play(play: str, home: int, away: int) -> bool:
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
    if not match_name:
        return None
    key = normalize_name(match_name)
    if key in validation_results:
        return validation_results[key]
    for k, data in validation_results.items():
        if key and (key in k or k in data['raw_name'].lower().replace(' ', '')):
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
    print("=" * 72)
    print("⚽ VALIDATION ENGINE — PER-BLUEPRINT SETTLEMENT")
    print("=" * 72)

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
    settled = []          # list of dicts with full info
    per_bp = defaultdict(lambda: {'wins': 0, 'losses': 0, 'not_found': 0})

    for p in predictions:
        match = p.get("match", "")
        play = p.get("play", "")
        bp = p.get("blueprint", "?")
        odds = p.get("odds", 0)

        actual = find_actual_result(match, validation_results)
        entry = {
            'match': match,
            'play': play,
            'blueprint': bp,
            'odds': odds,
            'confidence': p.get('confidence', 0),
            'actual': actual,
            'won': None,
        }

        if actual is None:
            entry['won'] = None
            per_bp[bp]['not_found'] += 1
        else:
            won = evaluate_play(play, actual['home_score'], actual['away_score'])
            entry['won'] = won
            if won:
                per_bp[bp]['wins'] += 1
            else:
                per_bp[bp]['losses'] += 1

        settled.append(entry)

    # -------- Print match-by-match results grouped by blueprint --------
    report_lines = []
    report_lines.append("# 🏁 SETTLEMENT REPORT")
    report_lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    report_lines.append("")

    # Group by blueprint for display
    by_bp = defaultdict(list)
    for e in settled:
        by_bp[e['blueprint']].append(e)

    for bp in sorted(by_bp.keys()):
        entries = by_bp[bp]
        wins = per_bp[bp]['wins']
        losses = per_bp[bp]['losses']
        nf = per_bp[bp]['not_found']
        total = wins + losses
        rate = (wins / total * 100) if total else 0.0

        header = f"── {bp} ── {wins}W / {losses}L / {nf} NF ({rate:.1f}%)"
        report_lines.append(header)
        print(header)

        for e in entries:
            if e['won'] is None:
                mark = "⏳"
                score_str = "Score: NOT FOUND"
            elif e['won']:
                mark = "✅"
                score_str = f"Score: {e['actual']['home_score']}-{e['actual']['away_score']}"
            else:
                mark = "❌"
                score_str = f"Score: {e['actual']['home_score']}-{e['actual']['away_score']}"

            line = f"   {mark} {e['match']} | {e['play']} | {score_str}"
            print(line)
            report_lines.append(line)
        report_lines.append("")
        print()

    # -------- Per-blueprint summary --------
    print("=" * 72)
    print("📊 PER-BLUEPRINT ACCURACY")
    print("=" * 72)
    print(f"{'BP':<6}{'Wins':<8}{'Losses':<10}{'Not Found':<12}{'Hit %':<10}")
    print("-" * 72)
    report_lines.append("## 📊 Per-Blueprint Accuracy")
    report_lines.append("")
    report_lines.append("| BP | Wins | Losses | Not Found | Hit % |")
    report_lines.append("|----|------|--------|-----------|-------|")

    total_wins = 0
    total_losses = 0
    total_nf = 0

    for bp in sorted(per_bp.keys()):
        s = per_bp[bp]
        t = s['wins'] + s['losses']
        rate = (s['wins'] / t * 100) if t else 0.0
        print(f"{bp:<6}{s['wins']:<8}{s['losses']:<10}{s['not_found']:<12}{rate:<10.1f}")
        report_lines.append(
            f"| {bp} | {s['wins']} | {s['losses']} | {s['not_found']} | {rate:.1f}% |"
        )
        total_wins += s['wins']
        total_losses += s['losses']
        total_nf += s['not_found']

    total_settled = total_wins + total_losses
    overall_rate = (total_wins / total_settled * 100) if total_settled else 0.0

    print("-" * 72)
    print(f"{'TOTAL':<6}{total_wins:<8}{total_losses:<10}{total_nf:<12}{overall_rate:<10.1f}")
    print("=" * 72)
    report_lines.append("")
    report_lines.append(
        f"**Overall: {total_wins}W / {total_losses}L / {total_nf} NF "
        f"({overall_rate:.1f}%)**"
    )

    # -------- Top 30 breakdown --------
    if os.path.exists(TOP30_FILE):
        with open(TOP30_FILE) as f:
            top30 = json.load(f)
        top30_matches = {e.get('match') for e in top30}
        top30_entries = [e for e in settled if e['match'] in top30_matches]
        t30_w = sum(1 for e in top30_entries if e['won'] is True)
        t30_l = sum(1 for e in top30_entries if e['won'] is False)
        t30_nf = sum(1 for e in top30_entries if e['won'] is None)
        t30_total = t30_w + t30_l
        t30_rate = (t30_w / t30_total * 100) if t30_total else 0.0

        print()
        print(f"📌 Top 30: {t30_w}W / {t30_l}L / {t30_nf} NF ({t30_rate:.1f}%)")
        report_lines.append("")
        report_lines.append(
            f"**Top 30: {t30_w}W / {t30_l}L / {t30_nf} NF ({t30_rate:.1f}%)**"
        )

    # -------- Save report --------
    report_text = "\n".join(report_lines)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    # -------- Telegram summary --------
    tg_lines = [
        "🏁 <b>SETTLEMENT REPORT</b>",
        f"📅 {datetime.now().strftime('%Y-%m-%d')}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for bp in sorted(per_bp.keys()):
        s = per_bp[bp]
        t = s['wins'] + s['losses']
        rate = (s['wins'] / t * 100) if t else 0.0
        tg_lines.append(f"<b>{bp}</b>: {s['wins']}W / {s['losses']}L ({rate:.0f}%)")

    tg_lines.append("")
    tg_lines.append(f"<b>Overall: {total_wins}W / {total_losses}L ({overall_rate:.1f}%)</b>")

    send_telegram("\n".join(tg_lines))

    print(f"\n💾 Report saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
