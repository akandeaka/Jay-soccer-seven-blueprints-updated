"""
Main System - 8 Blueprints with Accumulator Validation
COMPLETE WORKING VERSION
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
    """Read matches from input_matches.txt"""
    
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ {INPUT_FILE} not found!")
        return []
    
    with open(INPUT_FILE, 'r') as f:
        content = f.read().strip()
    
    if not content:
        print(f"\n❌ {INPUT_FILE} is empty!")
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
    """Build accumulators from predictions"""
    
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
            for m in combo:
                used.add(m['match'])
            break
    
    # 7 ODDS
    available = get_unused()
    for combo in combinations(available[:10], 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    return accumulators

# ============================================================
# LOAD VALIDATION RESULTS (for accumulator validation)
# ============================================================

def load_validation_results():
    """Load actual results from validation_results.txt"""
    
    if not os.path.exists("validation_results.txt"):
        return {}
    
    results = {}
    with open("validation_results.txt", 'r') as f:
        for line in f:
            line = line.strip()
            if 'RESULT:' in line:
                parts = line.split('|')
                match = parts[0].replace('RESULT:', '').strip()
                score = parts[1].strip() if len(parts) > 1 else ''
                if '-' in score:
                    home_score, away_score = score.split('-')
                    results[match] = {
                        'home_score': int(home_score.strip()),
                        'away_score': int(away_score.strip())
                    }
    return results

# ============================================================
# CHECK IF PREDICTION WAS CORRECT
# ============================================================

def is_prediction_correct(predicted_play, actual):
    """Check if a prediction was correct"""
    
    home = actual['home_score']
    away = actual['away_score']
    total_goals = home + away
    
    if 'Home Win' in predicted_play:
        return home > away
    elif 'Draw' in predicted_play:
        return home == away
    elif 'Both Teams to Score - YES' in predicted_play:
        return home > 0 and away > 0
    elif 'Both Teams to Score - NO' in predicted_play:
        return home == 0 or away == 0
    elif 'Over 1.5' in predicted_play:
        return total_goals > 1
    elif 'Under 3.5' in predicted_play:
        return total_goals < 4
    elif 'Over 2.5' in predicted_play:
        return total_goals > 2
    elif '1X & Over 1.5' in predicted_play:
        return (home >= away) and total_goals > 1
    elif '1X & Under 3.5' in predicted_play:
        return (home >= away) and total_goals < 4
    elif 'Draw or GG' in predicted_play:
        return (home == away) or (home > 0 and away > 0)
    elif 'Draw or Under 2.5' in predicted_play:
        return (home == away) or total_goals < 3
    
    return False

# ============================================================
# SEND TO TELEGRAM
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured - skipping")
        return False
    
    if len(message) > 4096:
        message = message[:4000] + "\n\n... (truncated)"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=30)
        return r.json().get('ok', False)
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM")
    print("8 BLUEPRINTS | ACCUMULATOR VALIDATION")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Delete old cache
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old cache")
    
    # Parse matches
    matches = parse_matches()
    
    if not matches:
        print("\n❌ No matches found in input_matches.txt")
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
        print("\n❌ No matches passed any blueprint")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Load validation results (for showing accumulator results)
    validation_results = load_validation_results()
    has_validation = len(validation_results) > 0
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BLUEPRINT PICKS ({len(predictions)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Add individual picks
    for p in predictions[:20]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡" if p['confidence'] >= 60 else "⚠️"
        message += f"""
{emoji} {p['blueprint']}: {p['match']}
   🎯 {p['play']}
   📈 Confidence: {p['confidence']}%
"""
    
    # Add accumulators with validation results
    if accumulators:
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATOR PICKS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            
            for match in acc['matches']:
                match_name = match['match'][:45]
                match_play = match['play']
                message += f"   • {match_name}\n"
                message += f"     🎯 {match_play}\n"
                
                # Show validation result if available
                if has_validation and match_name in validation_results:
                    actual = validation_results[match_name]
                    actual_score = f"{actual['home_score']}-{actual['away_score']}"
                    correct = is_prediction_correct(match_play, actual)
                    status = "✅" if correct else "❌"
                    message += f"     {status} Actual: {actual_score}\n"
                elif has_validation:
                    message += f"     ⚠️ Result not found\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Always bet responsibly!\n📊 AI predictions for informational purposes only."
    
    # Send to Telegram
    send_telegram(message)
    
    # Save predictions
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ SYSTEM EXECUTION COMPLETE")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Matches read: {len(matches)}")
    print(f"   Matches passed: {len(predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    if has_validation:
        print(f"   Validation results loaded: {len(validation_results)} matches")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
