"""
Main System - 8 Blueprints with Accumulator Validation
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations
from blueprint_engine import BlueprintEngine

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"

# ============================================================
# PARSE INPUT FILE
# ============================================================

def parse_matches():
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ {INPUT_FILE} not found!")
        return []
    
    with open(INPUT_FILE, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return []
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    matches = []
    i = 0
    
    while i < len(lines):
        if ' vs ' not in lines[i]:
            i += 1
            continue
        
        match = {'match': lines[i]}
        i += 1
        
        if i < len(lines) and '|' not in lines[i]:
            match['league'] = lines[i]
            i += 1
        else:
            match['league'] = 'Unknown'
        
        if i < len(lines) and '|' in lines[i]:
            odds = re.findall(r'(\d+\.\d+)', lines[i])
            if len(odds) >= 3:
                match['home_odds'] = float(odds[0])
                match['draw_odds'] = float(odds[1])
                match['away_odds'] = float(odds[2])
            i += 1
        else:
            i += 1
            continue
        
        matches.append(match)
    
    return matches

# ============================================================
# BUILD ACCUMULATORS
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
    for p in predictions:
        play = p.get('play', '')
        if 'Home Win' in play:
            p['odds'] = p.get('home_odds', 1.50)
        elif 'Draw' in play:
            p['odds'] = p.get('draw_odds', 1.50)
        else:
            p['odds'] = 1.50
    
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used = set()
    
    def get_unused():
        return [p for p in sorted_picks if p['match'] not in used]
    
    # 2 ODDS
    available = get_unused()
    for combo in combinations(available[:6], 2):
        total = combo[0]['odds'] * combo[1]['odds']
        if 1.8 <= total <= 2.5:
            accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 4 ODDS
    available = get_unused()
    for combo in combinations(available[:8], 4):
        total = 1
        for m in combo:
            total *= m['odds']
        if 3.5 <= total <= 5.0:
            accumulators['4_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            break
    
    # 7 ODDS
    available = get_unused()
    for combo in combinations(available[:10], 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            break
    
    return accumulators

# ============================================================
# VALIDATE ACCUMULATORS AGAINST RESULTS
# ============================================================

def validate_accumulator(accumulator, validation_results):
    """Check if accumulator picks were successful"""
    results = []
    for match in accumulator['matches']:
        match_name = match['match']
        predicted_play = match['play']
        
        actual = validation_results.get(match_name)
        if actual:
            is_correct = False
            home, away = actual['home_score'], actual['away_score']
            
            if 'Home Win' in predicted_play:
                is_correct = (home > away)
            elif 'Draw' in predicted_play:
                is_correct = (home == away)
            elif 'Both Teams to Score' in predicted_play:
                is_correct = (home > 0 and away > 0)
            elif 'Over 1.5' in predicted_play:
                is_correct = (home + away > 1)
            elif 'Under 3.5' in predicted_play:
                is_correct = (home + away < 4)
            elif 'Over 2.5' in predicted_play:
                is_correct = (home + away > 2)
            
            results.append({
                'match': match_name,
                'predicted': predicted_play,
                'actual': f"{home}-{away}",
                'correct': is_correct
            })
    
    return results

# ============================================================
# LOAD VALIDATION RESULTS
# ============================================================

def load_validation_results():
    """Load actual results from validation_results.txt"""
    if not os.path.exists("validation_results.txt"):
        return {}
    
    results = {}
    with open("validation_results.txt", 'r') as f:
        for line in f:
            if 'RESULT:' in line:
                parts = line.strip().split('|')
                match = parts[0].replace('RESULT:', '').strip()
                score = parts[1].strip()
                if '-' in score:
                    home, away = score.split('-')
                    results[match] = {'home_score': int(home), 'away_score': int(away)}
    return results

# ============================================================
# SEND TO TELEGRAM
# ============================================================

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}, timeout=30)
        return r.json().get('ok', False)
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM (UPDATED)")
    print("BP6: Draw or GG / Draw or Under 2.5")
    print("BP8: Over 2.5 Goals with 0-0 odds validation")
    print("="*60)
    
    # Delete cache
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
    
    # Parse matches
    matches = parse_matches()
    if not matches:
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    # Apply blueprints
    engine = BlueprintEngine()
    predictions = []
    for match in matches:
        result = engine.classify(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed any blueprint")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Load validation results (if available)
    validation_results = load_validation_results()
    
    # Build message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PICKS ({len(predictions)})
"""
    
    for p in predictions[:15]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} {p['blueprint']}: {p['match']}\n   🎯 {p['play']} | Confidence: {p['confidence']}%"
    
    if accumulators:
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            
            # Show each match with validation if available
            for m in acc['matches']:
                match_name = m['match'][:40]
                message += f"   • {match_name}\n"
                message += f"     🎯 {m['play']}\n"
                
                # SHOW VALIDATION RESULT IF AVAILABLE
                if validation_results and match_name in validation_results:
                    actual = validation_results[match_name]
                    actual_score = f"{actual['home_score']}-{actual['away_score']}"
                    
                    # Determine if prediction was correct
                    is_correct = False
                    if 'Home Win' in m['play']:
                        is_correct = (actual['home_score'] > actual['away_score'])
                    elif 'Draw' in m['play']:
                        is_correct = (actual['home_score'] == actual['away_score'])
                    elif 'Both Teams to Score' in m['play']:
                        is_correct = (actual['home_score'] > 0 and actual['away_score'] > 0)
                    elif 'Over 1.5' in m['play']:
                        is_correct = (actual['home_score'] + actual['away_score'] > 1)
                    elif 'Under 3.5' in m['play']:
                        is_correct = (actual['home_score'] + actual['away_score'] < 4)
                    elif 'Over 2.5' in m['play']:
                        is_correct = (actual['home_score'] + actual['away_score'] > 2)
                    
                    status = "✅" if is_correct else "❌"
                    message += f"     {status} Actual: {actual_score}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!"
    
    # Send to Telegram
    send_telegram(message)
    
    # Save
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n✅ Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
