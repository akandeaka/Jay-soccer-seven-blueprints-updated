"""
JAY SOCCER BLUEPRINTS - COMPLETE TOP-30 & HIGH-ACCURACY ACCUMULATOR SYSTEM
---------------------------------------------------------------------------
Pipeline:
  1. Parse raw match odds from input_matches.txt (CSV or block text).
  2. Classify each match via the validated BlueprintEngine (BP3, BP4, BP12, BP13).
  3. Rank candidates using Composite Scoring: S = Confidence * log2(1 + Odds).
  4. Extract the Top 30 highest-value predictions with per-blueprint quotas.
  5. Build 2_ODDS, 4_ODDS, 7_ODDS, 10_ODDS accumulators strictly from the
     Top 30 pool, minimizing leg count, enforcing ZERO match duplication,
     and forcing each ticket inside its target odds range.
  6. Save predictions.json, top_30_predictions.json, and accumulators.json.
  7. Post-match audit via results.txt across Full Pool, Top 30,
     and individual Accumulator Tickets.
  8. Dispatch summaries via Telegram and Email.

Only data-validated blueprints are enabled:
  BP3, BP4, BP12, BP13, BP14
"""

import os
import sys
import json
import re
import csv
import math
import smtplib
import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from email.message import EmailMessage

from blueprint_engine import BlueprintEngine, ENABLED_BLUEPRINTS


# ============================================================
# TOP 30 ALLOCATION
# ============================================================

# Slots reserved per blueprint (sums to 30).
# Rationale:
#   BP4  8  — highest live hit rate (65%)
#   BP14 7  — large live sample, above break-even (45%)
#   BP3  6  — strong backtest (+3.77%)
#   BP12 5  — strong backtest (+9.54%)
#   BP13 4  — backtest +2.10%
BP_QUOTA = {
    'BP4':  8,
    'BP14': 7,
    'BP3':  6,
    'BP12': 5,
    'BP13': 4,
}

# Priority order for using unused slots (best first).
BP_PRIORITY = ['BP4', 'BP14', 'BP3', 'BP12', 'BP13']


# ============================================================
# CONFIGURATION
# ============================================================

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')


# ============================================================
# BLUEPRINT ENGINE SINGLETON
# ============================================================

_engine_singleton = None


def _get_engine():
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = BlueprintEngine()
    return _engine_singleton


def analyze_match(match: dict):
    """Delegate to the validated BlueprintEngine."""
    result = _get_engine().classify(match)
    if not result:
        return None

    play_lower = result['play'].lower()
    if 'draw' in play_lower or result['blueprint'] == 'BP3':
        result['odds'] = result.get('draw_odds') or 1.50
    else:
        result['odds'] = result.get('home_odds') or 1.50

    return result


# ============================================================
# TARGETED INPUT PARSER
# ============================================================

def parse_matches(target_file: str = "input_matches.txt") -> list:
    if not os.path.exists(target_file):
        print(f"❌ Input file '{target_file}' not found in root directory!")
        return []

    print(f"📂 Found input file: {target_file}")
    with open(target_file, 'r', encoding='utf-8-sig') as f:
        content = f.read().strip()

    if not content:
        print(f"❌ '{target_file}' is empty!")
        return []

    content = content.split("The system did not generate")[0].strip()
    matches = []

    # ---------------- CSV Format Parsing ----------------
    if ',' in content and any(h in content.lower() for h in
                              ['team a', 'home odds', 'team_a', 'home_odds']):
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        reader = csv.DictReader(lines)
        for row in reader:
            try:
                cleaned = {(k.strip().lower() if k else ''): (v.strip() if v else '')
                           for k, v in row.items() if k}
                team_a = cleaned.get('team a') or cleaned.get('team_a') \
                         or cleaned.get('home team') or ''
                team_b = cleaned.get('team b') or cleaned.get('team_b') \
                         or cleaned.get('away team') or ''
                league = cleaned.get('league', 'Unknown')

                if not team_a or not team_b:
                    continue

                def parse_odd(val):
                    m = re.search(r'(\d+\.\d+|\d+)', str(val))
                    return float(m.group(1)) if m else 0.0

                matches.append({
                    'match': f"{team_a} vs {team_b}",
                    'home_team': team_a,
                    'away_team': team_b,
                    'league': league,
                    'home_odds': parse_odd(cleaned.get('home odds')
                                           or cleaned.get('home_odds')),
                    'draw_odds': parse_odd(cleaned.get('draw odds')
                                           or cleaned.get('draw_odds')),
                    'away_odds': parse_odd(cleaned.get('away odds')
                                           or cleaned.get('away_odds')),
                })
            except Exception:
                continue
        return matches

    # ---------------- Block Text Parsing ----------------
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        if ' vs ' not in lines[i]:
            i += 1
            continue

        match_info = {'match': lines[i]}
        teams = lines[i].split(' vs ')
        match_info['home_team'] = teams[0].strip()
        match_info['away_team'] = teams[1].strip() if len(teams) > 1 else ''
        i += 1

        if i < len(lines) and '|' not in lines[i]:
            match_info['league'] = lines[i]
            i += 1
        else:
            match_info['league'] = 'Unknown'

        if i < len(lines) and '|' in lines[i]:
            odds = re.findall(r'(\d+\.\d+)', lines[i])
            if len(odds) >= 3:
                match_info['home_odds'] = float(odds[0])
                match_info['draw_odds'] = float(odds[1])
                match_info['away_odds'] = float(odds[2])
            i += 1
        else:
            i += 1
            continue

        matches.append(match_info)

    return matches


# ============================================================
# COMPOSITE SCORING
# ============================================================

def calculate_composite_score(pick: dict) -> float:
    conf = float(pick.get('confidence', 60.0))
    odds = float(pick.get('odds', 1.50))
    if odds <= 1.0:
        return 0.0
    return conf * math.log2(1.0 + odds)


# ============================================================
# TOP 30 SELECTION WITH PER-BLUEPRINT QUOTAS
# ============================================================

def select_top_30(all_predictions: list) -> list:
    """
    Allocate Top 30 slots proportionally by blueprint.

    Pass 1: fill each BP up to its quota.
    Pass 2: unused slots roll to the highest-composite remaining picks.
    """
    ranked = sorted(all_predictions,
                    key=lambda x: x['composite_score'],
                    reverse=True)

    by_bp = defaultdict(list)
    for p in ranked:
        by_bp[p.get('blueprint')].append(p)

    top30 = []
    used = set()

    # Pass 1: fill each BP up to its quota, in priority order.
    for bp in BP_PRIORITY:
        quota = BP_QUOTA.get(bp, 0)
        for p in by_bp.get(bp, []):
            if len(top30) >= 30 or quota <= 0:
                break
            top30.append(p)
            used.add(id(p))
            quota -= 1

    # Pass 2: unused slots go to highest-composite remaining picks.
    for p in ranked:
        if len(top30) >= 30:
            break
        if id(p) not in used:
            top30.append(p)

    return top30[:30]


# ============================================================
# ACCUMULATOR BUILDER
# ============================================================

def build_optimal_accumulators(top_30_pool: list) -> dict:
    if not top_30_pool:
        return {}

    candidates = sorted(top_30_pool,
                        key=lambda x: x.get('composite_score', 0),
                        reverse=True)

    targets = [
        ('2_ODDS',  1.85, 2.45,  3),
        ('4_ODDS',  3.60, 4.60,  4),
        ('7_ODDS',  6.50, 7.80,  5),
        ('10_ODDS', 9.50, 11.50, 5),
    ]

    accumulators = {}
    used_matches = set()

    for ticket_key, min_odds, max_odds, max_legs in targets:
        available_pool = [p for p in candidates if p['match'] not in used_matches]
        if len(available_pool) < 2:
            continue

        best_combo = None
        best_combo_score = -1.0
        best_combo_odds = 0.0

        search_pool = available_pool[:14]
        for r in range(2, min(max_legs + 1, len(search_pool) + 1)):
            for combo in combinations(search_pool, r):
                total_odds = 1.0
                total_score = 0.0
                for leg in combo:
                    total_odds *= float(leg.get('odds', 1.50))
                    total_score += leg.get('composite_score', 0)

                if min_odds <= total_odds <= max_odds:
                    adjusted = total_score / (len(combo) ** 0.5)
                    if adjusted > best_combo_score:
                        best_combo_score = adjusted
                        best_combo = combo
                        best_combo_odds = total_odds

        if best_combo:
            legs = list(best_combo)
        else:
            ticket_legs = []
            running_odds = 1.0
            for p in available_pool:
                if len(ticket_legs) >= max_legs:
                    break
                leg_odds = float(p.get('odds', 1.50))
                candidate_odds = running_odds * leg_odds
                if candidate_odds > max_odds:
                    continue
                ticket_legs.append(p)
                running_odds = candidate_odds
                if running_odds >= min_odds:
                    break

            if running_odds < min_odds:
                print(f"   ⚠️ {ticket_key}: no viable combination "
                      f"(best fallback odds {running_odds:.2f} < {min_odds})")
                continue

            legs = ticket_legs
            best_combo_odds = running_odds

        for m in legs:
            used_matches.add(m['match'])

        avg_conf = sum(float(m.get('confidence', 0)) for m in legs) / len(legs)
        accumulators[ticket_key] = {
            'matches': legs,
            'odds': round(best_combo_odds, 2),
            'leg_count': len(legs),
            'avg_confidence': round(avg_conf, 1),
            'blueprints_used': [m.get('blueprint') for m in legs],
        }

    return accumulators


# ============================================================
# AUDIT
# ============================================================

def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'\b(fc|ac|utd|united|sv|vfb|sc|afc|cd|ud)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name).strip()


def load_validation_results(filepath: str = "results.txt") -> dict:
    if not os.path.exists(filepath):
        return {}

    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if ' vs ' in line and 'RESULT:' not in line:
            match_name = line
            i += 1
            while i < len(lines) and 'RESULT:' not in lines[i]:
                i += 1
            if i < len(lines) and 'RESULT:' in lines[i]:
                score_match = re.search(r'(\d+)-(\d+)', lines[i])
                if score_match:
                    results[match_name] = {
                        'home_score': int(score_match.group(1)),
                        'away_score': int(score_match.group(2)),
                    }
        i += 1
    return results


def evaluate_prediction(play: str, actual: dict) -> bool:
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    p = play.lower()

    if 'home win' in p or p == '1':
        return home > away
    if 'away win' in p or p == '2':
        return away > home
    if 'draw' in p and 'or' not in p:
        return home == away
    if 'home win + over 2.5' in p:
        return home > away and total > 2
    if 'both teams to score' in p or 'gg' in p or 'btts' in p:
        if ' - no' in p or ' no' in p.split('btts')[-1]:
            return not (home > 0 and away > 0)
        return home > 0 and away > 0
    if 'over 1.5' in p:
        return total > 1
    if 'over 2.5' in p:
        return total > 2
    if 'under 2.5' in p:
        return total < 3
    if 'under 3.5' in p:
        return total < 4
    if 'draw or under 2.5' in p:
        return (home == away) or total < 3
    if 'draw or gg' in p:
        return (home == away) or (home > 0 and away > 0)
    return False


def audit_and_validate_all(all_predictions: list, top_30: list,
                           accumulators: dict, actual_results: dict):
    if not actual_results:
        return None

    def check_pred(pred):
        match_name = pred['match']
        predicted_play = pred['play']
        norm_match = normalize_name(match_name)

        actual = None
        for res_key, score_data in actual_results.items():
            if normalize_name(res_key) in norm_match or norm_match in normalize_name(res_key):
                actual = score_data
                break

        if actual:
            is_win = evaluate_prediction(predicted_play, actual)
            return {
                'match': match_name,
                'blueprint': pred['blueprint'],
                'play': predicted_play,
                'confidence': pred['confidence'],
                'odds': pred.get('odds', 1.50),
                'score': f"{actual['home_score']}-{actual['away_score']}",
                'status': 'WIN' if is_win else 'LOSS',
                'is_win': is_win,
                'evaluated': True,
            }
        return {
            'match': match_name,
            'blueprint': pred['blueprint'],
            'play': predicted_play,
            'confidence': pred['confidence'],
            'odds': pred.get('odds', 1.50),
            'score': 'N/A',
            'status': 'PENDING',
            'is_win': False,
            'evaluated': False,
        }

    def summarize_pool(preds, label):
        audit = [check_pred(p) for p in preds]
        ev = [p for p in audit if p['evaluated']]
        wins = sum(1 for p in ev if p['is_win'])
        losses = len(ev) - wins
        rate = (wins / len(ev) * 100) if ev else 0.0

        per_bp = defaultdict(lambda: {'w': 0, 'l': 0})
        for p in ev:
            bp = p['blueprint']
            if p['is_win']:
                per_bp[bp]['w'] += 1
            else:
                per_bp[bp]['l'] += 1

        print(f"\n{label}")
        print(f"   Total:     {len(preds)}")
        print(f"   Settled:   {len(ev)}")
        print(f"   ✅ Wins:   {wins}")
        print(f"   ❌ Losses: {losses}")
        print(f"   Accuracy:  {wins}/{len(ev)} ({rate:.1f}%)")
        print(f"   Per-Blueprint:")
        for bp in sorted(per_bp.keys()):
            s = per_bp[bp]
            t = s['w'] + s['l']
            r = (s['w'] / t * 100) if t else 0.0
            print(f"     {bp:<6} {s['w']}W / {s['l']}L  ({r:.1f}%)")

        return {
            'total': len(preds),
            'settled': len(ev),
            'wins': wins,
            'losses': losses,
            'rate': round(rate, 2),
            'per_bp': {bp: dict(s) for bp, s in per_bp.items()},
        }

    print("\n" + "=" * 60)
    print("📊 POST-MATCH VALIDATION AUDIT")
    print("=" * 60)

    full_stats = summarize_pool(all_predictions, "📋 FULL POOL")
    top30_stats = summarize_pool(top_30, "⭐ TOP 30")

    acc_audit = {}
    for acc_name, acc_data in accumulators.items():
        leg_results = [check_pred(m) for m in acc_data['matches']]
        eval_legs = [l for l in leg_results if l['evaluated']]

        ticket_won = (len(eval_legs) == len(leg_results)
                      and all(l['is_win'] for l in eval_legs))
        ticket_lost = any(l['evaluated'] and not l['is_win'] for l in leg_results)

        status = 'WIN' if ticket_won else ('LOSS' if ticket_lost else 'PENDING')

        acc_audit[acc_name] = {
            'target_odds': acc_data['odds'],
            'leg_count': acc_data['leg_count'],
            'status': status,
            'legs': leg_results,
        }

    print("\n🎰 ACCUMULATOR TICKET AUDIT:")
    for acc_name, data in acc_audit.items():
        print(f"   • {acc_name:<8} | Odds: {data['target_odds']:<5} | "
              f"Status: {data['status']}")
    print("=" * 60 + "\n")

    audit_summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'full_pool_stats': full_stats,
        'top_30_stats': top30_stats,
        'accumulators': acc_audit,
    }

    with open("validation_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=4)

    return audit_summary


# ============================================================
# NOTIFICATIONS
# ============================================================

def send_telegram(message: str) -> bool:
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("⚠️ Telegram details missing. Skipping Telegram notification.")
        return False

    if len(message) > 4000:
        message = message[:3950] + "\n\n... (truncated)"

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
        }, timeout=30)
        if r.json().get('ok', False):
            print("✅ Telegram notification dispatched.")
            return True
        print(f"⚠️ Telegram send failure: {r.text}")
        return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


def send_email_report(subject: str, body: str):
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD or not Config.NOTIFICATION_EMAIL:
        print("⚠️ Email credentials missing. Skipping email report.")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = Config.SMTP_USER
    msg['To'] = Config.NOTIFICATION_EMAIL
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(msg)
        print("✅ Email report dispatched successfully.")
    except Exception as e:
        print(f"❌ Email exception: {e}")


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("⚽ JAY SOCCER BLUEPRINTS - TOP 30 & ACCUMULATOR ENGINE")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✅ Enabled blueprints: {ENABLED_BLUEPRINTS}\n")

    # Step 1: Parse input
    matches = parse_matches("input_matches.txt")
    if not matches:
        print("❌ Pipeline stopped: No valid matches retrieved.")
        sys.exit(1)

    print(f"📊 Parsed {len(matches)} raw fixtures.")

    # Step 2: Classify every match
    all_predictions = []
    for m in matches:
        res = analyze_match(m)
        if res:
            res['composite_score'] = calculate_composite_score(res)
            all_predictions.append(res)

    if not all_predictions:
        print("❌ No matches passed blueprint criteria today.")
        sys.exit(0)

    # Safety check
    seen_bps = {p['blueprint'] for p in all_predictions}
    unexpected = seen_bps - set(ENABLED_BLUEPRINTS)
    if unexpected:
        print(f"❌ UNEXPECTED blueprint IDs detected: {unexpected}")
        print(f"   Enabled set is {ENABLED_BLUEPRINTS}.")
        sys.exit(1)

    # Step 3: Per-blueprint counts in full pool
    pool_by_bp = defaultdict(int)
    for p in all_predictions:
        pool_by_bp[p['blueprint']] += 1
    print(f"📊 Full pool by blueprint: {dict(pool_by_bp)}")

    # Step 4: Quota-based Top 30
    top_30_predictions = select_top_30(all_predictions)

    # Per-blueprint allocation in Top 30
    top30_by_bp = defaultdict(int)
    for p in top_30_predictions:
        top30_by_bp[p['blueprint']] += 1
    print(f"🎯 Top 30 allocation: {dict(top30_by_bp)}")

    print(f"🎯 Total Eligible Predictions: {len(all_predictions)}")
    print(f"⭐ Extracted Top {len(top_30_predictions)} Predictions.")

    # Step 5: Build accumulators
    accumulators = build_optimal_accumulators(top_30_predictions)
    print(f"🎰 Generated {len(accumulators)} tickets.")

    # Step 6: Export JSON
    with open("predictions.json", "w", encoding="utf-8") as f:
        json.dump(all_predictions, f, indent=4)
    with open("top_30_predictions.json", "w", encoding="utf-8") as f:
        json.dump(top_30_predictions, f, indent=4)
    with open("accumulators.json", "w", encoding="utf-8") as f:
        json.dump(accumulators, f, indent=4)
    print("💾 Saved predictions.json, top_30_predictions.json, accumulators.json")

    # Step 7: Audit
    actual_results = load_validation_results("results.txt")
    audit_summary = None
    if actual_results:
        audit_summary = audit_and_validate_all(
            all_predictions, top_30_predictions,
            accumulators, actual_results
        )

    # Step 8: Telegram — Top 30 with allocation header
    tg_msg = (f"⚽ <b>JAY SOCCER BLUEPRINTS - TOP 30</b>\n"
              f"📅 {datetime.now().strftime('%Y-%m-%d')}\n")
    tg_msg += f"📊 Pool: {len(all_predictions)} | "
    tg_msg += f"Top 30: {dict(top30_by_bp)}\n\n"

    for idx, p in enumerate(top_30_predictions, 1):
        tg_msg += (f"{idx}. #{p['blueprint']} {p['match']} "
                   f"-> <b>{p['play']}</b> ({p['confidence']}%)\n")
        if len(tg_msg) > 3500:
            send_telegram(tg_msg)
            tg_msg = ""

    if accumulators:
        tg_msg += "\n🎰 <b>OPTIMIZED ACCUMULATORS:</b>\n"
        for acc_name, acc_data in accumulators.items():
            tg_msg += (f"\n<b>{acc_name}</b> "
                       f"(Odds: {acc_data['odds']} | Legs: {acc_data['leg_count']})\n")
            for m in acc_data['matches']:
                tg_msg += f"   - {m['match']} ({m['play']})\n"

    # Audit summary to Telegram if we have settled data
    if audit_summary:
        fp = audit_summary['full_pool_stats']
        t30 = audit_summary['top_30_stats']
        tg_msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        tg_msg += "📊 <b>SETTLEMENT SUMMARY</b>\n"
        tg_msg += f"Full Pool: {fp['wins']}W / {fp['losses']}L ({fp['rate']:.1f}%)\n"
        tg_msg += f"Top 30:    {t30['wins']}W / {t30['losses']}L ({t30['rate']:.1f}%)\n"
        tg_msg += "\n<b>Per-Blueprint (Top 30):</b>\n"
        for bp, s in sorted(t30['per_bp'].items()):
            t = s['w'] + s['l']
            r = (s['w'] / t * 100) if t else 0.0
            tg_msg += f"  {bp}: {s['w']}W/{s['l']}L ({r:.0f}%)\n"

    send_telegram(tg_msg)

    # Step 9: Email
    email_body = "JAY SOCCER BLUEPRINTS - AUDIT REPORT\n"
    email_body += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    email_body += "=" * 60 + "\n\n"
    email_body += f"TOTAL MATCHES PARSED: {len(matches)}\n"
    email_body += f"TOTAL ELIGIBLE PREDICTIONS: {len(all_predictions)}\n"
    email_body += f"FULL POOL BY BLUEPRINT: {dict(pool_by_bp)}\n"
    email_body += f"TOP 30 ALLOCATION: {dict(top30_by_bp)}\n\n"
    email_body += "TOP 30 PREDICTIONS:\n"
    for idx, p in enumerate(top_30_predictions, 1):
        email_body += (f"{idx:02d}. [BP #{p['blueprint']}] {p['match']} | "
                       f"Play: {p['play']} | Odds: {p['odds']} | "
                       f"Conf: {p['confidence']}%\n")

    if audit_summary:
        email_body += "\n" + "=" * 60 + "\n"
        email_body += "SETTLEMENT SUMMARY\n"
        fp = audit_summary['full_pool_stats']
        t30 = audit_summary['top_30_stats']
        email_body += f"Full Pool: {fp['wins']}W / {fp['losses']}L ({fp['rate']:.1f}%)\n"
        email_body += f"Top 30:    {t30['wins']}W / {t30['losses']}L ({t30['rate']:.1f}%)\n\n"
        email_body += "Per-Blueprint (Full Pool):\n"
        for bp, s in sorted(fp['per_bp'].items()):
            t = s['w'] + s['l']
            r = (s['w'] / t * 100) if t else 0.0
            email_body += f"  {bp}: {s['w']}W / {s['l']}L ({r:.1f}%)\n"
        email_body += "\nPer-Blueprint (Top 30):\n"
        for bp, s in sorted(t30['per_bp'].items()):
            t = s['w'] + s['l']
            r = (s['w'] / t * 100) if t else 0.0
            email_body += f"  {bp}: {s['w']}W / {s['l']}L ({r:.1f}%)\n"

    email_body += "\n" + "=" * 60 + "\n"
    email_body += "GENERATED ACCUMULATORS:\n"
    for acc_name, acc_data in accumulators.items():
        email_body += (f"\n[{acc_name}] Total Odds: {acc_data['odds']} | "
                       f"Legs: {acc_data['leg_count']}\n")
        for m in acc_data['matches']:
            email_body += (f"   - {m['match']} | BP #{m['blueprint']} | "
                           f"Play: {m['play']} | Odds: {m['odds']}\n")

    send_email_report(
        subject=f"Top 30 Soccer Predictions & Accumulators - "
                f"{datetime.now().strftime('%Y-%m-%d')}",
        body=email_body,
    )

    print("\n" + "=" * 60)
    print("✅ EXECUTION FINISHED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
