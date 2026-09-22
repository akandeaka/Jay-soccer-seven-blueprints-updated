"""
validate_from_file.py
=====================

Soccer blueprint settlement validator with full breakdown.

Reads:
    predictions.json         — full prediction pool
    top_30_predictions.json  — Top 30 picks (if present)
    results.txt              — actual match scores

Writes:
    validation_report.md
    Telegram notification

Outputs:
    1. Match-by-match list with scorelines and WIN/LOSS marks, grouped by blueprint
    2. Overall settlement (full pool)
    3. Top 30 breakdown
    4. Per-blueprint accuracy with play-type labels
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
# BLUEPRINT LABELS
# ============================================================

BP_LABELS = {
    'BP3':  'BP3 (Full Time Draw)',
    'BP4':  'BP4 (Straight Home Win)',
    'BP12': 'BP12 (Home Win + Over 2.5)',
    'BP13': 'BP13 (Straight Home Win)',
    'BP14': 'BP14 (Full Time Draw)',
}


def bp_label(bp):
    return BP_LABELS.get(bp, bp)


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
    """
    Parse results.txt into {normalized_match_name: {home_score, away_score, raw_name}}.

    Handles:
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

    # Pass 1: multi-line block form
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

    # Pass 2 (fallback): scan every line for one-line entries
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
# SETTLEMENT HELPERS
# ============================================================

def settle_pool(preds, validation_results):
    """Return list of settled entries for a pool of predictions."""
    settled = []
    for p in preds:
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

        if actual is not None:
            entry['won'] = evaluate_play(
                play, actual['home_score'], actual['away_score']
            )
        settled.append(entry)
    return settled


def summarize(settled):
    """Compute wins/losses/not_found and per-blueprint breakdown."""
    per_bp = defaultdict(lambda: {'w': 0, 'l': 0, 'nf': 0})
    wins = losses = nf = 0

    for e in settled:
        bp = e['blueprint']
        if e['won'] is None:
            per_bp[bp]['nf'] += 1
            nf += 1
        elif e['won']:
            per_bp[bp]['w'] += 1
            wins += 1
        else:
            per_bp[bp]['l'] += 1
            losses += 1

    total_settled = wins + losses
    rate = (wins / total_settled * 100) if total_settled else 0.0

    return {
        'wins': wins,
        'losses': losses,
        'not_found': nf,
        'total_settled': total_settled,
        'rate': round(rate, 1),
        'per_bp': {bp: dict(s) for bp, s in per_bp.items()},
    }


def fmt_bp(s):
    if not s:
        return "—"
    t = s['w'] + s['l']
    rate = (s['w'] / t * 100) if t else 0.0
    return f"{s['w']}W / {s['l']}L ({rate:.0f}%)"


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 72)
    print("⚽ VALIDATION ENGINE — FULL BREAKDOWN")
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
    print(f"📊 Loaded {len(validation_results)} match results")

    top30 = []
    if os.path.exists(TOP30_FILE):
        with open(TOP30_FILE) as f:
            top30 = json.load(f)
        print(f"⭐ Loaded {len(top30)} Top-30 picks")
    else:
        print("⚠️ Top 30 file missing — using only full pool")

    print()

    # Settle both pools
    full_settled = settle_pool(predictions, validation_results)
    full_summary = summarize(full_settled)

    top30_settled = settle_pool(top30, validation_results) if top30 else []
    top30_summary = summarize(top30_settled) if top30_settled else None

    # ---------- Group by blueprint ----------
    by_bp = defaultdict(list)
    for e in full_settled:
        by_bp[e['blueprint']].append(e)

    # ---------- Match-by-match list ----------
    report_lines = [
        "# 🏁 SETTLEMENT REPORT",
        f"📅 {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 📋 Match Results",
        "",
    ]

    print("=" * 72)
    print("📋 MATCH RESULTS")
    print("=" * 72)

    for bp in sorted(by_bp.keys()):
        entries = by_bp[bp]
        s = full_summary['per_bp'][bp]
        t = s['w'] + s['l']
        rate = (s['w'] / t * 100) if t else 0.0

        header = f"── {bp_label(bp)} ── {s['w']}W / {s['l']}L ({rate:.0f}%)"
        print(header)
        report_lines.append(f"### {bp_label(bp)} — {s['w']}W / {s['l']}L ({rate:.0f}%)")
        report_lines.append("")

        for e in entries:
            if e['won'] is None:
                mark = "⏳"
                score_str = "—"
                line = f"   {mark}  {e['match']}  |  Score: {score_str}"
                md_line = f"- ⏳ {e['match']} — Score: {score_str}"
            elif e['won']:
                mark = "✅ WIN "
                score_str = f"{e['actual']['home_score']}-{e['actual']['away_score']}"
                line = f"   {mark}  {e['match']}  |  Score: {score_str}"
                md_line = f"- ✅ **WIN** — {e['match']} | Score: {score_str}"
            else:
                mark = "❌ LOSS"
                score_str = f"{e['actual']['home_score']}-{e['actual']['away_score']}"
                line = f"   {mark}  {e['match']}  |  Score: {score_str}"
                md_line = f"- ❌ **LOSS** — {e['match']} | Score: {score_str}"

            print(line)
            report_lines.append(md_line)

        print()
        report_lines.append("")

    # ---------- Summary 1: Full Pool ----------
    print("=" * 72)
    print("📋 SUMMARY 1 — FULL POOL SETTLEMENT")
    print("=" * 72)
    fp = full_summary
    print(f"   Total predictions:    {len(predictions)}")
    print(f"   Settled (matched):    {fp['total_settled']}")
    print(f"   ✅ Wins:              {fp['wins']}")
    print(f"   ❌ Losses:            {fp['losses']}")
    print(f"   ⏳ Not found:          {fp['not_found']}")
    print(f"   Accuracy:             {fp['wins']}/{fp['total_settled']} ({fp['rate']}%)")
    print()

    report_lines.append("## 📋 Summary — Full Pool")
    report_lines.append(
        f"- Total: {len(predictions)} | Settled: {fp['total_settled']} | "
        f"Wins: {fp['wins']} | Losses: {fp['losses']} | "
        f"Not found: {fp['not_found']}"
    )
    report_lines.append(f"- **Accuracy: {fp['wins']}/{fp['total_settled']} ({fp['rate']}%)**")
    report_lines.append("")

    # ---------- Summary 2: Top 30 ----------
    if top30_summary:
        print("=" * 72)
        print("⭐ SUMMARY 2 — TOP 30 PERFORMANCE")
        print("=" * 72)
        t30 = top30_summary
        print(f"   Total in Top 30:      {len(top30)}")
        print(f"   Settled (matched):    {t30['total_settled']}")
        print(f"   ✅ Wins:              {t30['wins']}")
        print(f"   ❌ Losses:            {t30['losses']}")
        print(f"   ⏳ Not found:          {t30['not_found']}")
        print(f"   Accuracy:             {t30['wins']}/{t30['total_settled']} ({t30['rate']}%)")
        print()

        report_lines.append("## ⭐ Summary — Top 30")
        report_lines.append(
            f"- Total: {len(top30)} | Settled: {t30['total_settled']} | "
            f"Wins: {t30['wins']} | Losses: {t30['losses']} | "
            f"Not found: {t30['not_found']}"
        )
        report_lines.append(
            f"- **Accuracy: {t30['wins']}/{t30['total_settled']} ({t30['rate']}%)**"
        )
        report_lines.append("")

    # ---------- Summary 3: Per Blueprint ----------
    print("=" * 72)
    print("📊 SUMMARY 3 — PER-BLUEPRINT ACCURACY")
    print("=" * 72)
    print(f"{'Blueprint':<34}{'Full Pool':<22}{'Top 30':<22}")
    print("-" * 72)

    all_bps = set(full_summary['per_bp'].keys())
    if top30_summary:
        all_bps |= set(top30_summary['per_bp'].keys())

    for bp in sorted(all_bps):
        fp_s = full_summary['per_bp'].get(bp)
        t30_s = top30_summary['per_bp'].get(bp) if top30_summary else None
        print(f"{bp_label(bp):<34}{fmt_bp(fp_s):<22}{fmt_bp(t30_s):<22}")

    print("-" * 72)

    report_lines.append("## 📈 Per-Blueprint Accuracy")
    report_lines.append("")
    report_lines.append("| Blueprint | Full Pool | Top 30 |")
    report_lines.append("|-----------|-----------|--------|")
    for bp in sorted(all_bps):
        fp_s = full_summary['per_bp'].get(bp)
        t30_s = top30_summary['per_bp'].get(bp) if top30_summary else None
        report_lines.append(f"| {bp_label(bp)} | {fmt_bp(fp_s)} | {fmt_bp(t30_s)} |")

    report_text = "\n".join(report_lines)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    # ---------- Telegram: match list + summaries ----------
    tg_lines = [
        "🏁 <b>SETTLEMENT REPORT</b>",
        f"📅 {datetime.now().strftime('%Y-%m-%d')}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "📋 <b>MATCH RESULTS</b>",
        "",
    ]

    for bp in sorted(by_bp.keys()):
        entries = by_bp[bp]
        s = full_summary['per_bp'][bp]
        t = s['w'] + s['l']
        rate = (s['w'] / t * 100) if t else 0.0

        tg_lines.append(f"<b>{bp_label(bp)}</b> — {s['w']}W/{s['l']}L ({rate:.0f}%)")

        for e in entries:
            if e['won'] is None:
                tg_lines.append(f"  ⏳ {e['match']}")
            elif e['won']:
                tg_lines.append(
                    f"  ✅ {e['match']} | {e['actual']['home_score']}-{e['actual']['away_score']}"
                )
            else:
                tg_lines.append(
                    f"  ❌ {e['match']} | {e['actual']['home_score']}-{e['actual']['away_score']}"
                )
        tg_lines.append("")

    tg_lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📋 <b>FULL POOL</b>",
        f"   ✅ {fp['wins']}W / ❌ {fp['losses']}L / ⏳ {fp['not_found']} NF",
        f"   Accuracy: {fp['wins']}/{fp['total_settled']} ({fp['rate']}%)",
    ]

    if top30_summary:
        t30 = top30_summary
        tg_lines += [
            "",
            "⭐ <b>TOP 30</b>",
            f"   ✅ {t30['wins']}W / ❌ {t30['losses']}L / ⏳ {t30['not_found']} NF",
            f"   Accuracy: {t30['wins']}/{t30['total_settled']} ({t30['rate']}%)",
        ]

    tg_lines += ["", "📊 <b>PER-BLUEPRINT</b>"]
    for bp in sorted(all_bps):
        fp_s = full_summary['per_bp'].get(bp)
        t30_s = top30_summary['per_bp'].get(bp) if top30_summary else None
        tg_lines.append(f"<b>{bp_label(bp)}</b>")
        tg_lines.append(f"  Full: {fmt_bp(fp_s)}  |  Top30: {fmt_bp(t30_s)}")

    send_telegram("\n".join(tg_lines))

    print(f"\n💾 Report saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
