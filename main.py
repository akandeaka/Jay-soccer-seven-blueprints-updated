"""
Main System - 8 Blueprints with Accumulator Validation
Includes: 2_ODDS, 4_ODDS, 7_ODDS, 10_ODDS
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations
from blueprint_engine import BlueprintEngine

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"


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


def build_accumulators(predictions):
    """Build 2_ODDS, 4_ODDS, 7_ODDS, 10_ODDS"""
    
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
    
    # 2 ODDS (2-3 matches)
    available = get_unused()
    for n in [2, 3]:
        for combo in combinations(available[:8], n):
            total = 1
            for m in combo:
                total *= m['odds']
            if 1.8 <= total <= 2.5:
                accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                for m in combo:
                    used.add(m['match'])
                break
        if '2_ODDS' in accumulators:
            break
    
    # 4 ODDS (4 matches)
    available = get_unused()
    for combo in combinations(available[:12], 4):
        total = 1
        for m in combo:
            total *= m['odds']
        if 3.5 <= total <= 5.0:
            accumulators['4_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 7 ODDS (5 matches)
    available = get_unused()
    for combo in combinations(available[:15], 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 10 ODDS (5-6 matches)
    available = get_unused()
    for n in [5, 6]:
        for combo in combinations(available[:20], n):
            total = 1
            for m in combo:
                total *= m['odds']
            if 9.0 <= total <= 12.0:
                accumulators['10_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                break
        if '10_ODDS' in accumulators:
            break
    
    return accumulators


def load_validation_results():
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
                    home, away = score.split('-')
                    results[match] = {
                        'home_score': int(home.strip()),
                        'away_score': int(away.strip())
                    }
    return results


def check_prediction(play, actual):
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    
    if 'Home Win' in play:
        return home > away
    elif 'Draw' in play:
        return home == away
    elif 'Both Teams to Score' in play:
        return home > 0 and away > 0
    elif 'Over 1.5' in play:
        return total > 1
    elif 'Under 3.5' in play:
        return total < 4
    elif 'Over 2.5' in play:
        return total > 2
    elif 'Draw or GG' in play:
        return (home == away) or (home > 0 and away > 0)
    elif 'Draw or Under 2.5' in play:
        return (home == away) or total < 3
    return False


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
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


def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM")
    print("BP8: Over 2.5 Goals (0-0 odds > 20)")
    print("2_ODDS | 4_ODDS | 7_ODDS | 10_ODDS")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old cache")
    
    matches = parse_matches()
    if not matches:
        print("\n❌ No matches found in input_matches.txt")
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    engine = BlueprintEngine()
    predictions = []
    for match in matches:
        result = engine.classify(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed blueprints")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    for p in predictions:
        print(f"   {p['blueprint']}: {p['match']} - {p['play']} ({p['confidence']}%)")
    
    accumulators = build_accumulators(predictions)
    validation = load_validation_results()
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PICKS ({len(predictions)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for p in predictions[:15]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} {p['blueprint']}: {p['match']}\n   🎯 {p['play']} | Conf: {p['confidence']}%\n"
    
    if accumulators:
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            for m in acc['matches']:
                match_name = m['match'][:45]
                message += f"   • {match_name}\n"
                message += f"     🎯 {m['play']}\n"
                
                if validation and match_name in validation:
                    actual = validation[match_name]
                    score = f"{actual['home_score']}-{actual['away_score']}"
                    correct = check_prediction(m['play'], actual)
                    status = "✅" if correct else "❌"
                    message += f"     {status} Actual: {score}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!"
    
    send_telegram(message)
    
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
