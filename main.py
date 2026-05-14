"""
JAY SOCCER BLUEPRINTS - COMPLETE SYSTEM
8 Blueprints | Smart Accumulators | Telegram Integration
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"

# League quality database
LEAGUE_DATABASE = {
    'premier league': {'quality': 1.0, 'goals_avg': 2.8},
    'bundesliga': {'quality': 1.0, 'goals_avg': 3.2},
    'la liga': {'quality': 1.0, 'goals_avg': 2.5},
    'serie a': {'quality': 1.0, 'goals_avg': 2.6},
    'ligue 1': {'quality': 1.0, 'goals_avg': 2.7},
    'championship': {'quality': 0.9, 'goals_avg': 2.6},
    'eredivisie': {'quality': 0.95, 'goals_avg': 3.1},
    'primeira liga': {'quality': 0.9, 'goals_avg': 2.7},
}

# Approved leagues for BP6 (Draw predictions)
APPROVED_BP6_LEAGUES = [
    'premier league', 'bundesliga', 'la liga', 'serie a', 'ligue 1',
    'championship', 'eredivisie', 'primeira liga'
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_league_quality(league_name):
    """Get league quality score"""
    league_lower = league_name.lower()
    for key, data in LEAGUE_DATABASE.items():
        if key in league_lower:
            return data['quality'], data['goals_avg']
    return 0.6, 2.5

def is_approved_for_bp6(league_name):
    """Check if league is approved for BP6"""
    league_lower = league_name.lower()
    for approved in APPROVED_BP6_LEAGUES:
        if approved in league_lower:
            return True
    return False

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
# 8 BLUEPRINTS
# ============================================================

def analyze_match(match):
    home = match.get('home_odds', 0)
    draw = match.get('draw_odds', 0)
    away = match.get('away_odds', 0)
    league = match.get('league', 'Unknown')
    
    quality, goals_avg = get_league_quality(league)
    
    # BP1: Elite Home Banker
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return {
            'blueprint': 'BP1', 'play': 'Straight Home Win',
            'confidence': int(95 * quality), 'risk': 'Ultra-Low',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP2: Primary Favorite
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return {
            'blueprint': 'BP2', 'play': 'Home Win',
            'confidence': int(90 * quality), 'risk': 'Low',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP3: Moderate Favorite Safety
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return {
            'blueprint': 'BP3', 'play': '1X & Over 1.5 Goals',
            'confidence': int(85 * quality), 'risk': 'Low-Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP4: Goal Engine
    if 1.72 <= home <= 1.80:
        boost = 1.1 if goals_avg >= 3.0 else 1.0
        return {
            'blueprint': 'BP4', 'play': 'Over 1.5 Goals',
            'confidence': int(75 * quality * boost), 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP5: Defensive Trap
    if 1.90 <= home <= 2.02:
        return {
            'blueprint': 'BP5', 'play': '1X & Under 3.5 FT',
            'confidence': int(70 * quality), 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP6: Draw (Only for approved leagues)
    if 2.75 <= draw <= 3.39 and is_approved_for_bp6(league):
        if goals_avg >= 3.0:
            play = 'Draw or GG (Draw OR Both Teams to Score)'
            conf = int(68 * quality)
        elif goals_avg <= 2.3:
            play = 'Draw or Under 2.5 Goals'
            conf = int(72 * quality)
        else:
            play = 'Full Time Draw'
            conf = int(55 * quality)
        return {
            'blueprint': 'BP6', 'play': play,
            'confidence': conf, 'risk': 'Medium',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP7: BTTS Value Spot
    if 1.40 <= home <= 1.69:
        if goals_avg >= 3.0:
            play = 'Both Teams to Score - YES'
            conf = int(75 * quality)
        else:
            play = 'Both Teams to Score - NO'
            conf = int(65 * quality)
        return {
            'blueprint': 'BP7', 'play': play,
            'confidence': conf, 'risk': 'Low-Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP8: High-Scoring Signals
    if 3.60 <= draw <= 3.75 and goals_avg >= 2.7:
        return {
            'blueprint': 'BP8', 'play': 'Over 2.5 Goals',
            'confidence': int(60 * quality), 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    return None

# ============================================================
# BUILD ACCUMULATORS
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
    # Set odds for each prediction
    for p in predictions:
        if 'Home Win' in p['play']:
            p['odds'] = p['home_odds']
        elif 'Draw' in p['play']:
            p['odds'] = p['draw_odds']
        else:
            p['odds'] = 1.50
    
    # Sort by confidence
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    
    # Filter high quality (confidence >= 60)
    quality_picks = [p for p in sorted_picks if p['confidence'] >= 60]
    
    if len(quality_picks) < 2:
        quality_picks = sorted_picks[:10]
    
    accumulators = {}
    used = set()
    
    def get_unused(pool):
        return [p for p in pool if p['match'] not in used]
    
    # 2_ODDS
    pool = get_unused(quality_picks)
    for n in [2, 3]:
        for combo in combinations(pool[:6], n):
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
    
    # 4_ODDS
    pool = get_unused(quality_picks)
    for combo in combinations(pool[:10], 4):
        total = 1
        for m in combo:
            total *= m['odds']
        if 3.5 <= total <= 5.0:
            accumulators['4_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 7_ODDS
    pool = get_unused(quality_picks)
    for combo in combinations(pool[:12], 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 10_ODDS
    pool = get_unused(quality_picks)
    for n in [5, 6]:
        for combo in combinations(pool[:15], n):
            total = 1
            for m in combo:
                total *= m['odds']
            if 9.0 <= total <= 12.0:
                accumulators['10_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                break
        if '10_ODDS' in accumulators:
            break
    
    return accumulators

# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
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
    print("8 BLUEPRINTS | SMART ACCUMULATORS")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # DELETE OLD CACHE - FIXES PROBLEM 2
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old predictions.json cache")
    
    matches = parse_matches()
    if not matches:
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    # Analyze matches
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed blueprints")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    
    # Display predictions
    for i, p in enumerate(predictions[:15], 1):
        print(f"   {i}. {p['blueprint']}: {p['match'][:50]}")
        print(f"      🎯 {p['play']} | Conf: {p['confidence']}%")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Build Telegram message - FIXES PROBLEM 3
    message = f"""⚽ JAY SOCCER BLUEPRINTS - PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BLUEPRINT PICKS ({len(predictions)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Add individual picks (THIS WAS MISSING BEFORE)
    for p in predictions[:15]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} {p['blueprint']}: {p['match'][:45]}\n   🎯 {p['play']} | Conf: {p['confidence']}%"
    
    # Add accumulators
    if accumulators:
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 SMART ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            for m in acc['matches']:
                message += f"   • {m['match'][:45]}\n"
                message += f"     🎯 {m['play']}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!"
    
    # Send to Telegram
    send_telegram(message)
    
    # Save predictions
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ SYSTEM COMPLETE")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Matches analyzed: {len(matches)}")
    print(f"   Predictions made: {len(predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    print(f"   Telegram: {'Sent' if TELEGRAM_TOKEN else 'Not configured'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
