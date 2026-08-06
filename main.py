"""
JAY SOCCER BLUEPRINTS - COMPLETE TOP-30 & HIGH-ACCURACY ACCUMULATOR SYSTEM
---------------------------------------------------------------------------
1. Parses raw match odds from input_matches.txt (supports CSV or block text).
2. Evaluates all matches across the 11-Blueprint engine.
3. Ranks candidates using Composite Scoring: S = Confidence * log2(1 + Odds).
4. Extracts the Top 30 highest-value predictions.
5. Builds 2_ODDS, 4_ODDS, 7_ODDS, and 10_ODDS accumulators strictly from the 
   Top 30 pool, minimizing leg count and enforcing ZERO match duplication.
6. Saves predictions.json, top_30_predictions.json, and accumulators.json.
7. Performs post-match audit via validation_results.txt across the Full Pool, 
   Top 30 Pool, and individual Accumulator Tickets.
8. Dispatches summaries via Telegram and Email.
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
from datetime import datetime
from itertools import combinations
from email.message import EmailMessage

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
# LEAGUE CLASSIFICATIONS & BLUEPRINT DETECTORS
# ============================================================
HIGH_SCORING_LEAGUES = ['bundesliga', 'eredivisie', 'brazil', 'brasileirao', 'friendly', 'club friendly']
MEDIUM_SCORING_LEAGUES = ['premier league', 'epl', 'ligue 1', 'championship', 'europa league']
LOW_SCORING_LEAGUES = ['la liga', 'serie a', 'turkey', 'russia', 'greece']

BTTS_HIGH_LEAGUES = ['bundesliga', 'eredivisie', 'brazil', 'premier league', 'epl', 'friendly', 'club friendly']
BTTS_LOW_LEAGUES = ['la liga', 'serie a', 'turkey', 'russia']

def get_league_type(league: str) -> str:
    league_lower = league.lower()
    if any(hs in league_lower for hs in HIGH_SCORING_LEAGUES):
        return 'high'
    elif any(ms in league_lower for ms in MEDIUM_SCORING_LEAGUES):
        return 'medium'
    return 'low'

def check_blueprint_1(home, away):
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return {'blueprint': '1', 'play': 'Straight Home Win', 'confidence': 95}
    return None

def check_blueprint_2(home, away):
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return {'blueprint': '2', 'play': 'Home Win', 'confidence': 90}
    return None

def check_blueprint_3(home, away):
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return {'blueprint': '3', 'play': '1X & Over 1.5 Goals', 'confidence': 85}
    return None

def check_blueprint_4(home):
    if 1.72 <= home <= 1.80:
        return {'blueprint': '4', 'play': 'Over 1.5 Goals', 'confidence': 75}
    return None

def check_blueprint_5(home):
    if 1.90 <= home <= 2.02:
        return {'blueprint': '5', 'play': '1X & Under 3.5 FT', 'confidence': 70}
    return None

def check_blueprint_6(draw, league):
    if 2.75 <= draw <= 2.95:
        return {'blueprint': '6', 'play': 'Draw or Under 2.5 Goals', 'confidence': 68}
    return None

def check_blueprint_7(draw, league):
    if 2.96 <= draw <= 3.20:
        return {'blueprint': '7', 'play': 'Draw or Over 2.5 Goals', 'confidence': 65}
    return None

def check_blueprint_8(draw, league):
    if 3.21 <= draw <= 3.60:
        league_type = get_league_type(league)
        if league_type == 'high':
            return {'blueprint': '8', 'play': 'Draw or GG', 'confidence': 68}
        return {'blueprint': '8', 'play': 'Draw or GG', 'confidence': 65}
    return None

def check_blueprint_9(home, league):
    if 1.40 <= home <= 1.55:
        league_lower = league.lower()
        if any(bl in league_lower for bl in BTTS_LOW_LEAGUES):
            return {'blueprint': '9', 'play': 'Both Teams to Score - NO', 'confidence': 55}
    return None

def check_blueprint_10(home, league):
    if 1.56 <= home <= 1.75:
        league_lower = league.lower()
        if any(bh in league_lower for bh in BTTS_HIGH_LEAGUES):
            return {'blueprint': '10', 'play': 'Both Teams to Score - YES', 'confidence': 70}
        return {'blueprint': '10', 'play': 'Both Teams to Score - YES', 'confidence': 65}
    return None

def check_blueprint_11(draw, league):
    if 3.60 <= draw <= 3.75:
        return {'blueprint': '11', 'play': 'Over 2.5 Goals', 'confidence': 60}
    return None

def analyze_match(match: dict):
    home = match.get('home_odds', 0.0)
    draw = match.get('draw_odds', 0.0)
    away = match.get('away_odds', 0.0)
    league = match.get('league', 'Unknown')
    match_name = match.get('match', '')
    
    result = (check_blueprint_1(home, away) or
              check_blueprint_2(home, away) or
              check_blueprint_3(home, away) or
              check_blueprint_4(home) or
              check_blueprint_5(home) or
              check_blueprint_6(draw, league) or
              check_blueprint_7(draw, league) or
              check_blueprint_8(draw, league) or
              check_blueprint_9(home, league) or
              check_blueprint_10(home, league) or
              check_blueprint_11(draw, league))
    
    if result:
        result['match'] = match_name
        result['league'] = league
        result['home_odds'] = home
        result['draw_odds'] = draw
        result['away_odds'] = away
        
        play = result['play'].lower()
        if 'home' in play or result['blueprint'] in ['1', '2']:
            result['odds'] = home if home > 0 else 1.50
        elif 'draw' in play:
            result['odds'] = draw if draw > 0 else 1.50
        else:
            result['odds'] = home if home > 0 else 1.50
            
        return result
    return None

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

    # CSV Format Parsing
    if ',' in content and any(h in content.lower() for h in ['team a', 'home odds', 'team_a', 'home_odds']):
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        reader = csv.DictReader(lines)
        for row in reader:
            try:
                cleaned = {(k.strip().lower() if k else ''): (v.strip() if v else '') for k, v in row.items() if k}
                team_a = cleaned.get('team a') or cleaned.get('team_a') or cleaned.get('home team') or ''
                team_b = cleaned.get('team b') or cleaned.get('team_b') or cleaned.get('away team') or ''
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
                    'home_odds': parse_odd(cleaned.get('home odds') or cleaned.get('home_odds')),
                    'draw_odds': parse_odd(cleaned.get('draw odds') or cleaned.get('draw_odds')),
                    'away_odds': parse_odd(cleaned.get('away odds') or cleaned.get('away_odds'))
                })
            except Exception:
                continue
        return matches

    # Line/Pipe Text Parsing
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
# COMPOSITE SCORING & ACCUMULATOR ENGINE
# ============================================================
def calculate_composite_score(pick: dict) -> float:
    conf = float(pick.get('confidence', 60.0))
    odds = float(pick.get('odds', 1.50))
    return conf * math.log2(1.0 + odds)

def build_optimal_accumulators(top_30_pool: list) -> dict:
    if not top_30_pool:
        return {}

    candidates = sorted(top_30_pool, key=lambda x: x.get('composite_score', 0), reverse=True)

    targets = [
        ('2_ODDS', 1.85, 2.45, 3),
        ('4_ODDS', 3.60, 4.60, 4),
        ('7_ODDS', 6.50, 7.80, 5),
        ('10_ODDS', 9.50, 11.50, 5)
    ]

    accumulators = {}
    used_matches = set()

    for ticket_key, min_odds, max_odds, max_legs in targets:
        available_pool = [p for p in candidates if p['match'] not in used_matches]
        
        best_combo = None
        best_combo_score = -1.0
        best_combo_odds = 0.0

        for r in range(2, min(max_legs + 1, len(available_pool) + 1)):
            for combo in combinations(available_pool[:14], r):
                total_odds = 1.0
                total_score = 0.0
                
                for leg in combo:
                    total_odds *= float(leg.get('odds', 1.50))
                    total_score += leg.get('composite_score', 0)
                
                if min_odds <= total_odds <= max_odds:
                    adjusted_score = total_score / (len(combo) ** 0.5)
                    if adjusted_score > best_combo_score:
                        best_combo_score = adjusted_score
                        best_combo = combo
                        best_combo_odds = total_odds

        if not best_combo:
            ticket_legs = []
            running_odds = 1.0
            for p in available_pool:
                leg_odds = float(p.get('odds', 1.50))
                if len(ticket_legs) < max_legs:
                    ticket_legs.append(p)
                    running_odds *= leg_odds
                    if running_odds >= min_odds:
                        break
            if ticket_legs:
                best_combo = tuple(ticket_legs)
                best_combo_odds = running_odds

        if best_combo:
            legs = list(best_combo)
            for m in legs:
                used_matches.add(m['match'])
            
            avg_conf = sum(float(m.get('confidence', 0)) for m in legs) / len(legs)
            accumulators[ticket_key] = {
                'matches': legs,
                'odds': round(best_combo_odds, 2),
                'leg_count': len(legs),
                'avg_confidence': round(avg_conf, 1),
                'blueprints_used': [m.get('blueprint') for m in legs]
            }

    return accumulators

# ============================================================
# AUDIT & SCORE VALIDATION
# ============================================================
def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'\b(fc|ac|utd|united|sv|vfb|sc|afc|cd|ud)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name).strip()

def load_validation_results(filepath: str = "validation_results.txt") -> dict:
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
                        'away_score': int(score_match.group(2))
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
    elif 'away win' in p or p == '2':
        return away > home
    elif 'draw' in p and 'or' not in p:
        return home == away
    elif 'both teams to score' in p or 'gg' in p:
        return home > 0 and away > 0
    elif 'over 1.5' in p:
        return total > 1
    elif 'over 2.5' in p:
        return total > 2
    elif 'under 2.5' in p:
        return total < 3
    elif 'under 3.5' in p:
        return total < 4
    elif 'draw or under 2.5' in p:
        return (home == away) or total < 3
    elif 'draw or gg' in p:
        return (home == away) or (home > 0 and away > 0)
    return False

def audit_and_validate_all(all_predictions: list, top_30: list, accumulators: dict, actual_results: dict):
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
                'evaluated': True
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
            'evaluated': False
        }

    full_audit = [check_pred(p) for p in all_predictions]
    eval_full = [p for p in full_audit if p['evaluated']]
    full_wins = sum(1 for p in eval_full if p['is_win'])
    full_rate = (full_wins / len(eval_full) * 100) if eval_full else 0.0

    top30_audit = [check_pred(p) for p in top_30]
    eval_top30 = [p for p in top30_audit if p['evaluated']]
    top30_wins = sum(1 for p in eval_top30 if p['is_win'])
    top30_rate = (top30_wins / len(eval_top30) * 100) if eval_top30 else 0.0

    acc_audit = {}
    for acc_name, acc_data in accumulators.items():
        leg_results = [check_pred(m) for m in acc_data['matches']]
        eval_legs = [l for l in leg_results if l['evaluated']]
        
        ticket_won = (len(eval_legs) == len(leg_results)) and all(l['is_win'] for l in eval_legs)
        ticket_lost = any(l['evaluated'] and not l['is_win'] for l in leg_results)
        
        status = 'WIN' if ticket_won else ('LOSS' if ticket_lost else 'PENDING')
        
        acc_audit[acc_name] = {
            'target_odds': acc_data['odds'],
            'leg_count': acc_data['leg_count'],
            'status': status,
            'legs': leg_results
        }

    audit_summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'full_pool_stats': {
            'total_predictions': len(all_predictions),
            'evaluated': len(eval_full),
            'wins': full_wins,
            'win_rate_percent': round(full_rate, 2)
        },
        'top_30_stats': {
            'total_predictions': len(top_30),
            'evaluated': len(eval_top30),
            'wins': top30_wins,
            'win_rate_percent': round(top30_rate, 2)
        },
        'accumulators': acc_audit
    }

    with open("validation_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=4)

    print("\n" + "="*60)
    print("📊 POST-MATCH VALIDATION AUDIT")
    print("="*60)
    print(f"Full Pool Win Rate (All {len(all_predictions)}): {full_wins}/{len(eval_full)} ({full_rate:.1f}%)")
    print(f"Top 30 Win Rate:              {top30_wins}/{len(eval_top30)} ({top30_rate:.1f}%)")
    print("-" * 60)
    print("🎰 ACCUMULATOR TICKET AUDIT:")
    for acc_name, data in acc_audit.items():
        print(f"   • {acc_name:<8} | Odds: {data['target_odds']:<5} | Status: {data['status']}")
    print("="*60 + "\n")

    return audit_summary

# ============================================================
# NOTIFICATIONS (TELEGRAM & EMAIL)
# ============================================================
def send_telegram(message: str) -> bool:
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("⚠️ Telegram details missing. Skipping Telegram notification.")
        return False
    
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
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
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS - TOP 30 & ACCUMULATOR ENGINE")
    print("="*60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Parse input_matches.txt
    matches = parse_matches("input_matches.txt")
    if not matches:
        print("❌ Pipeline stopped: No valid matches retrieved.")
        sys.exit(1)
        
    print(f"📊 Parsed {len(matches)} raw fixtures.")

    # Step 2: Run 11-Blueprint Analysis & Rank Pool
    all_predictions = []
    for m in matches:
        res = analyze_match(m)
        if res:
            res['composite_score'] = calculate_composite_score(res)
            all_predictions.append(res)

    if not all_predictions:
        print("❌ No matches passed blueprint criteria today.")
        sys.exit(0)

    # Rank all predictions by composite score descending
    ranked_predictions = sorted(all_predictions, key=lambda x: x['composite_score'], reverse=True)
    top_30_predictions = ranked_predictions[:30]

    print(f"🎯 Total Eligible Predictions: {len(all_predictions)}")
    print(f"⭐ Extracted Top {len(top_30_predictions)} Predictions.")

    # Step 3: Build Accumulators STRICTLY from Top 30 Pool
    accumulators = build_optimal_accumulators(top_30_predictions)
    print(f"🎰 Generated {len(accumulators)} tickets (2_ODDS, 4_ODDS, 7_ODDS, 10_ODDS).")

    # Step 4: Export JSON Files
    with open("predictions.json", "w", encoding="utf-8") as f:
        json.dump(all_predictions, f, indent=4)

    with open("top_30_predictions.json", "w", encoding="utf-8") as f:
        json.dump(top_30_predictions, f, indent=4)
        
    with open("accumulators.json", "w", encoding="utf-8") as f:
        json.dump(accumulators, f, indent=4)
    print("💾 Saved predictions.json, top_30_predictions.json, and accumulators.json")

    # Step 5: Score Validation Audit (if validation_results.txt is present)
    actual_results = load_validation_results("validation_results.txt")
    if actual_results:
        audit_and_validate_all(all_predictions, top_30_predictions, accumulators, actual_results)

    # Step 6: Telegram Dispatch
    tg_msg = f"⚽ <b>JAY SOCCER BLUEPRINTS - TOP 30</b>\n📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for idx, p in enumerate(top_30_predictions, 1):
        tg_msg += f"{idx}. #{p['blueprint']} {p['match']} -> <b>{p['play']}</b> ({p['confidence']}%)\n"
        if len(tg_msg) > 3500:
            send_telegram(tg_msg)
            tg_msg = ""

    if accumulators:
        tg_msg += "\n🎰 <b>OPTIMIZED ACCUMULATORS:</b>\n"
        for acc_name, acc_data in accumulators.items():
            tg_msg += f"\n<b>{acc_name}</b> (Odds: {acc_data['odds']} | Legs: {acc_data['leg_count']})\n"
            for m in acc_data['matches']:
                tg_msg += f"   - {m['match']} ({m['play']})\n"

    send_telegram(tg_msg)

    # Step 7: Email Audit Report
    email_body = f"JAY SOCCER BLUEPRINTS - AUDIT REPORT\n"
    email_body += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    email_body += "="*60 + "\n\n"
    email_body += f"TOTAL MATCHES PARSED: {len(matches)}\n"
    email_body += f"TOTAL ELIGIBLE PREDICTIONS: {len(all_predictions)}\n\n"
    email_body += "TOP 30 PREDICTIONS:\n"
    for idx, p in enumerate(top_30_predictions, 1):
        email_body += f"{idx:02d}. [BP #{p['blueprint']}] {p['match']} | Play: {p['play']} | Odds: {p['odds']} | Conf: {p['confidence']}%\n"

    email_body += "\n" + "="*60 + "\n"
    email_body += "GENERATED ACCUMULATORS:\n"
    for acc_name, acc_data in accumulators.items():
        email_body += f"\n[{acc_name}] Total Odds: {acc_data['odds']} | Legs: {acc_data['leg_count']}\n"
        for m in acc_data['matches']:
            email_body += f"   - {m['match']} | BP #{m['blueprint']} | Play: {m['play']} | Odds: {m['odds']}\n"
            
    send_email_report(
        subject=f"Top 30 Soccer Predictions & Accumulators - {datetime.now().strftime('%Y-%m-%d')}",
        body=email_body
    )

    print("\n" + "="*60)
    print("✅ EXECUTION FINISHED SUCCESSFULLY")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
