"""
MAIN ORCHESTRATOR - SOCCER BLUEPRINT SYSTEM, MULTI-ACCUMULATOR & VALIDATION PIPELINE
--------------------------------------------------------------------------------------
1. Loads all predictions (predictions.json).
2. Rank-orders picks strictly by highest probability/confidence (league filtering disabled).
3. Generates 2_ODDS, 4_ODDS, 7_ODDS, and 10_ODDS accumulators with STRICT zero-match repetition across tickets.
4. Parses actual scorelines (validation_results.txt) and cross-evaluates single picks & ticket legs[cite: 5].
5. Computes win rates globally and broken down per Blueprint ID.
6. Exports full audit to validated_results.csv and ticket structures to accumulators.json.
7. Dispatches comprehensive log via Email and summary via Telegram.
"""

import os
import sys
import json
import re
import smtplib
import requests
import pandas as pd
from datetime import datetime
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
# ACCUMULATOR BUILDER (PROBABILITY-BASED, STRICT MUTUAL EXCLUSIVITY)
# ============================================================
def build_accumulators(predictions: list) -> dict:
    """
    Builds 2_ODDS, 4_ODDS, 7_ODDS, and 10_ODDS accumulators:
    - Ranked purely by highest win probability / confidence score.
    - Zero match repetition across all accumulator tickets.
    """
    if not predictions:
        return {}

    formatted_picks = []
    for p in predictions:
        item = dict(p)
        match_name = item.get('match', f"{item.get('home_team', '')} vs {item.get('away_team', '')}")
        item['match_name'] = match_name
        
        # Priority sort score based purely on confidence / win probability
        confidence = item.get('confidence', item.get('probability', item.get('prob', 50.0)))
        item['sort_confidence'] = float(confidence)
        
        # Extract play odds
        play = str(item.get('play', item.get('predicted_outcome', ''))).lower()
        if 'odds' in item and item['odds']:
            odds = float(item['odds'])
        elif 'home win' in play or play == '1':
            odds = float(item.get('home_odds', 1.50))
        elif 'draw' in play:
            odds = float(item.get('draw_odds', 1.50))
        elif 'away win' in play or play == '2':
            odds = float(item.get('away_odds', 1.50))
        else:
            odds = float(item.get('play_odds', 1.50))
            
        item['play_odds'] = max(odds, 1.05)
        formatted_picks.append(item)

    # Sort strictly by highest confidence / probability score descending
    sorted_picks = sorted(formatted_picks, key=lambda x: x['sort_confidence'], reverse=True)

    target_tickets = [
        ('2_ODDS', 2.0),
        ('4_ODDS', 4.0),
        ('7_ODDS', 7.0),
        ('10_ODDS', 10.0)
    ]

    accumulators = {}
    used_matches = set()  # Global tracker preventing match repetition across ALL accumulators

    for ticket_key, target_odds in target_tickets:
        ticket_legs = []
        combined_odds = 1.0
        
        for p in sorted_picks:
            m_name = p['match_name']
            if m_name in used_matches:
                continue
            
            ticket_legs.append(p)
            used_matches.add(m_name)
            combined_odds *= p['play_odds']
            
            # Stop adding legs once target odds threshold is met
            if combined_odds >= target_odds:
                break
        
        if ticket_legs:
            avg_conf = sum(m['sort_confidence'] for m in ticket_legs) / len(ticket_legs)
            accumulators[ticket_key] = {
                'matches': ticket_legs,
                'odds': round(combined_odds, 2),
                'leg_count': len(ticket_legs),
                'avg_confidence': round(avg_conf, 1)
            }

    return accumulators

# ============================================================
# MATCHING & EVALUATION LOGIC
# ============================================================
def normalize_name(name: str) -> str:
    """Normalizes team/match strings for accurate matching[cite: 5]."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'\b(fc|ac|utd|united|sv|vfb|sc|afc|cd|ud)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name).strip()

def load_validation_results(filepath: str = "validation_results.txt") -> dict:
    """Parses actual match results[cite: 5]."""
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
    """Evaluates prediction outcome conditions against final scores[cite: 5]."""
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

def validate_accumulator_ticket(acc_matches: list, validation_results: dict):
    """Evaluates each leg within an accumulator ticket[cite: 5]."""
    results = []
    all_correct = True
    
    for match in acc_matches:
        match_name = match.get('match_name', match.get('match', f"{match.get('home_team', '')} vs {match.get('away_team', '')}"))
        play = match.get('play', match.get('predicted_outcome', ''))
        
        norm_match = normalize_name(match_name)
        actual = None
        for key, score_data in validation_results.items():
            norm_key = normalize_name(key)
            if norm_key in norm_match or norm_match in norm_key:
                actual = score_data
                break
        
        if actual:
            is_correct = evaluate_prediction(play, actual)
            results.append({
                'match': match_name,
                'play': play,
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'correct': is_correct
            })
            if not is_correct:
                all_correct = False
        else:
            results.append({
                'match': match_name,
                'play': play,
                'actual_score': 'PENDING',
                'correct': False
            })
            all_correct = False
            
    return results, all_correct

def validate_all_predictions(predictions: list, actual_results: dict) -> list:
    """Validates single prediction records[cite: 5]."""
    validated = []
    for pred in predictions:
        match_name = pred.get('match', f"{pred.get('home_team', '')} vs {pred.get('away_team', '')}")
        blueprint_id = pred.get('blueprint_id', pred.get('blueprint', 'Unknown'))
        predicted_play = pred.get('play', pred.get('predicted_outcome', ''))
        
        norm_match = normalize_name(match_name)
        actual = None
        for res_key, score_data in actual_results.items():
            norm_res_key = normalize_name(res_key)
            if norm_res_key in norm_match or norm_match in norm_res_key:
                actual = score_data
                break

        if actual:
            is_correct = evaluate_prediction(predicted_play, actual)
            status = 'WIN' if is_correct else 'LOSS'
            actual_score = f"{actual['home_score']}-{actual['away_score']}"
        else:
            is_correct = False
            status = 'PENDING'
            actual_score = 'N/A'

        validated.append({
            'match': match_name,
            'blueprint': blueprint_id,
            'play': predicted_play,
            'actual_score': actual_score,
            'status': status,
            'is_correct': is_correct
        })
    return validated

# ============================================================
# REPORT BUILDER & ROUTING
# ============================================================
def build_reports(validated_records: list, accumulators: dict, actual_results: dict):
    """Builds formatted outputs for Email and Telegram."""
    total = len(validated_records)
    completed = [r for r in validated_records if r['status'] in ['WIN', 'LOSS']]
    pending = [r for r in validated_records if r['status'] == 'PENDING']
    
    total_completed = len(completed)
    total_wins = sum(1 for r in completed if r['is_correct'])
    overall_acc = (total_wins / total_completed * 100) if total_completed > 0 else 0.0

    # Group metrics by Blueprint
    blueprint_stats = {}
    for r in completed:
        bp = str(r['blueprint'])
        if bp not in blueprint_stats:
            blueprint_stats[bp] = {'total': 0, 'wins': 0}
        blueprint_stats[bp]['total'] += 1
        if r['is_correct']:
            blueprint_stats[bp]['wins'] += 1

    # Validate Accumulator Tickets
    acc_validation = {}
    for acc_name in ['2_ODDS', '4_ODDS', '7_ODDS', '10_ODDS']:
        if acc_name in accumulators:
            acc_data = accumulators[acc_name]
            legs, won = validate_accumulator_ticket(acc_data['matches'], actual_results)
            acc_validation[acc_name] = {
                'legs': legs,
                'won': won,
                'odds': acc_data['odds'],
                'avg_confidence': acc_data.get('avg_confidence', 0)
            }

    # EMAIL REPORT BODY
    email_body = "====================================================\n"
    email_body += " ⚽ SOCCER BLUEPRINT SYSTEM - AUDIT & ACCUMULATORS\n"
    email_body += f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    email_body += "====================================================\n\n"
    email_body += "OVERALL SUMMARY:\n"
    email_body += f"• Total Predictions: {total}\n"
    email_body += f"• Completed Matches: {total_completed}\n"
    email_body += f"• Pending Matches: {len(pending)}\n"
    email_body += f"• System Win Rate: {overall_acc:.2f}% ({total_wins}/{total_completed})\n\n"

    email_body += "----------------------------------------------------\n"
    email_body += "🎯 PROBABILITY ACCUMULATORS (MUTUALLY EXCLUSIVE)\n"
    email_body += "----------------------------------------------------\n"
    if acc_validation:
        for acc_name, acc_res in acc_validation.items():
            status_str = "✅ WON" if acc_res['won'] else "❌ LOST / INCOMPLETE"
            email_body += f"• [{acc_name}] Target Odds: {acc_res['odds']} (Avg Conf: {acc_res['avg_confidence']}%) | Status: {status_str}\n"
            for leg in acc_res['legs']:
                icon = "✓" if leg['correct'] else "✗"
                email_body += f"   - {icon} {leg['match']} | Play: {leg['play']} | Score: {leg['actual_score']}\n"
            email_body += "\n"
    else:
        email_body += "No accumulators generated.\n\n"

    email_body += "----------------------------------------------------\n"
    email_body += "📊 PERFORMANCE BREAKDOWN BY BLUEPRINT\n"
    email_body += "----------------------------------------------------\n"
    if blueprint_stats:
        for bp, stats in sorted(blueprint_stats.items()):
            acc = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            email_body += f"• Blueprint {bp}: {acc:.1f}% Win Rate ({stats['wins']}/{stats['total']})\n"
    else:
        email_body += "No completed blueprint records available.\n"

    email_body += "\n----------------------------------------------------\n"
    email_body += "📋 DETAILED PREDICTION BREAKDOWN\n"
    email_body += "----------------------------------------------------\n"
    for i, r in enumerate(validated_records, 1):
        email_body += f"{i:02d}. [{r['status']}] {r['match']} | BP: {r['blueprint']} | Play: {r['play']} | Score: {r['actual_score']}\n"

    # TELEGRAM REPORT BODY
    top_30 = validated_records[:30]
    top_30_completed = [r for r in top_30 if r['status'] in ['WIN', 'LOSS']]
    top_30_wins = sum(1 for r in top_30_completed if r['is_correct'])
    top_30_acc = (top_30_wins / len(top_30_completed) * 100) if top_30_completed else 0.0

    telegram_body = "⚽ <b>DAILY SYSTEM PERFORMANCE REPORT</b>\n"
    telegram_body += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
    telegram_body += f"📊 <b>Full System Accuracy:</b> {overall_acc:.1f}% ({total_wins}/{total_completed})\n"
    telegram_body += f"🎯 <b>Top 30 Digest Accuracy:</b> {top_30_acc:.1f}% ({top_30_wins}/{len(top_30_completed)})\n\n"
    
    if acc_validation:
        telegram_body += "<b>🎯 Probability Tickets (No Matches Repeated):</b>\n"
        for acc_name in ['2_ODDS', '4_ODDS', '7_ODDS', '10_ODDS']:
            if acc_name in acc_validation:
                res = acc_validation[acc_name]
                icon = "✅" if res['won'] else "❌"
                telegram_body += f"{icon} <b>{acc_name}</b> (@ {res['odds']:.2f} | {len(res['legs'])} legs)\n"
        telegram_body += "\n"

    telegram_body += "<b>Top 10 Picks Digest:</b>\n"
    for i, r in enumerate(top_30[:10], 1):
        icon = "✅" if r['status'] == 'WIN' else ("❌" if r['status'] == 'LOSS' else "⏳")
        telegram_body += f"{i}. {icon} {r['match']} ({r['play']})\n"
        
    telegram_body += "\n📩 <i>Full report with all tickets & blueprint metrics sent to Email.</i>"

    return email_body, telegram_body

def send_email_report(subject: str, body: str):
    """Dispatches complete audit to user email."""
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD or not Config.NOTIFICATION_EMAIL:
        print("⚠️ Email credentials not fully configured. Skipping email send.")
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
        print("✅ Audit report dispatched to Email successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def send_telegram_digest(message: str):
    """Dispatches summary digest to Telegram."""
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token/chat_id not configured. Skipping Telegram send.")
        return
        
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print("✅ Digest dispatched to Telegram successfully.")
        else:
            print(f"⚠️ Telegram send issue: {res.text}")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

# ============================================================
# MAIN EXECUTION ENTRYPOINT
# ============================================================
def main():
    print("\n" + "="*60)
    print("🚀 RUNNING PROBABILITY ACCUMULATOR & VALIDATION PIPELINE")
    print("="*60)
    
    # Step 1: Load Predictions
    if not os.path.exists("predictions.json"):
        print("❌ Error: predictions.json file not found.")
        sys.exit(1)
        
    with open("predictions.json", 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    print(f"📥 Loaded {len(predictions)} total predictions.")

    # Step 2: Build Probability-Based Accumulators (2, 4, 7, 10 odds)
    accumulators = build_accumulators(predictions)
    with open("accumulators.json", "w", encoding="utf-8") as f:
        json.dump(accumulators, f, indent=4)
    print(f"🎯 Generated {len(accumulators)} tickets (2_ODDS, 4_ODDS, 7_ODDS, 10_ODDS) with zero match repetition.")

    # Step 3: Load Actual Scorelines
    actual_results = load_validation_results("validation_results.txt")
    print(f"🌐 Loaded {len(actual_results)} match scores from validation_results.txt.")

    # Step 4: Validate Predictions
    validated_records = validate_all_predictions(predictions, actual_results)
    print("✅ Completed match validation for all single predictions.")

    # Step 5: Build Email & Telegram Reports
    email_body, telegram_body = build_reports(validated_records, accumulators, actual_results)

    # Step 6: Route Email
    print("\n📧 Dispatching Email Report...")
    send_email_report(
        subject=f"Soccer Blueprint Performance & Accumulator Audit - {datetime.now().strftime('%Y-%m-%d')}",
        body=email_body
    )

    # Step 7: Route Telegram Digest
    print("\n📱 Dispatching Telegram Digest...")
    send_telegram_digest(telegram_body)

    # Step 8: Export outcomes to CSV
    pd.DataFrame(validated_records).to_csv("validated_results.csv", index=False)
    print("\n💾 Saved full validated dataset to validated_results.csv")
    print("="*60)
    print("✅ PIPELINE EXECUTION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
