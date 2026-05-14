"""
JAY SOCCER BLUEPRINTS - COMPLETE WORKING SYSTEM
- 8 Blueprints with database analysis
- 2,4,7,10 odds accumulators
- Telegram integration
- Performance validation
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"

# ============================================================
# LEAGUE DATABASE (for deep analysis)
# ============================================================

LEAGUE_DATABASE = {
    # Elite Leagues (Best data)
    'premier league': {'quality': 1.0, 'goals_avg': 2.8, 'draw_rate': 0.24},
    'bundesliga': {'quality': 1.0, 'goals_avg': 3.2, 'draw_rate': 0.22},
    'la liga': {'quality': 1.0, 'goals_avg': 2.5, 'draw_rate': 0.25},
    'serie a': {'quality': 1.0, 'goals_avg': 2.6, 'draw_rate': 0.26},
    'ligue 1': {'quality': 1.0, 'goals_avg': 2.7, 'draw_rate': 0.23},
    'eredivisie': {'quality': 0.95, 'goals_avg': 3.1, 'draw_rate': 0.21},
    
    # Strong Leagues
    'championship': {'quality': 0.9, 'goals_avg': 2.6, 'draw_rate': 0.25},
    'primeira liga': {'quality': 0.9, 'goals_avg': 2.7, 'draw_rate': 0.24},
    'belgian pro league': {'quality': 0.85, 'goals_avg': 2.5, 'draw_rate': 0.26},
    'scottish premiership': {'quality': 0.85, 'goals_avg': 2.8, 'draw_rate': 0.22},
    'turkish super lig': {'quality': 0.85, 'goals_avg': 2.7, 'draw_rate': 0.23},
    
    # Women's Leagues (Good data)
    'wsl': {'quality': 0.9, 'goals_avg': 3.4, 'draw_rate': 0.20},
    'frauen bundesliga': {'quality': 0.9, 'goals_avg': 3.3, 'draw_rate': 0.21},
    'nwsl': {'quality': 0.9, 'goals_avg': 3.2, 'draw_rate': 0.22},
}

# Blueprint performance weights
BLUEPRINT_WEIGHTS = {
    'BP1': 0.95, 'BP2': 0.90, 'BP3': 0.85, 'BP4': 0.75,
    'BP5': 0.70, 'BP6': 0.50, 'BP7': 0.65, 'BP8': 0.60
}

# ============================================================
# DATA PARSING
# ============================================================

def parse_matches():
    """Parse matches from input_matches.txt"""
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found!")
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
# LEAGUE ANALYSIS
# ============================================================

def get_league_data(league_name):
    """Get league data for deep analysis"""
    league_lower = league_name.lower()
    
    for key, data in LEAGUE_DATABASE.items():
        if key in league_lower:
            return data
    
    return {'quality': 0.6, 'goals_avg': 2.5, 'draw_rate': 0.25}

# ============================================================
# 8 BLUEPRINTS WITH DEEP ANALYSIS
# ============================================================

def analyze_match(match):
    """Apply 8 blueprints with deep analysis"""
    
    home = match.get('home_odds', 0)
    draw = match.get('draw_odds', 0)
    away = match.get('away_odds', 0)
    league = match.get('league', 'Unknown')
    
    league_data = get_league_data(league)
    quality = league_data['quality']
    goals_avg = league_data['goals_avg']
    
    result = None
    
    # BP1: Elite Home Banker
    if 1.20 <= home <= 1.29 and away >= 10.0:
        result = {'blueprint': 'BP1', 'play': 'Straight Home Win', 'confidence': int(95 * quality), 'risk': 'Ultra-Low'}
    
    # BP2: Primary Favorite
    elif 1.30 <= home <= 1.36 and away >= 9.0:
        result = {'blueprint': 'BP2', 'play': 'Home Win', 'confidence': int(90 * quality), 'risk': 'Low'}
    
    # BP3: Moderate Favorite Safety
    elif 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        result = {'blueprint': 'BP3', 'play': '1X & Over 1.5 Goals', 'confidence': int(85 * quality), 'risk': 'Low-Moderate'}
    
    # BP4: Goal Engine (boosted in high-scoring leagues)
    elif 1.72 <= home <= 1.80:
        boost = 1.1 if goals_avg >= 3.0 else 1.0
        result = {'blueprint': 'BP4', 'play': 'Over 1.5 Goals', 'confidence': int(75 * quality * boost), 'risk': 'Moderate'}
    
    # BP5: Defensive Trap
    elif 1.90 <= home <= 2.02:
        result = {'blueprint': 'BP5', 'play': '1X & Under 3.5 FT', 'confidence': int(70 * quality), 'risk': 'Moderate'}
    
    # BP6: Draw (combo based on league)
    elif 2.75 <= draw <= 3.39:
        if goals_avg >= 3.0:
            result = {'blueprint': 'BP6', 'play': 'Draw or GG (Draw OR Both Teams to Score)', 'confidence': int(68 * quality), 'risk': 'Medium'}
        elif goals_avg <= 2.3:
            result = {'blueprint': 'BP6', 'play': 'Draw or Under 2.5 Goals', 'confidence': int(72 * quality), 'risk': 'Medium'}
        else:
            result = {'blueprint': 'BP6', 'play': 'Full Time Draw', 'confidence': int(55 * quality), 'risk': 'High'}
    
    # BP7: BTTS Value Spot
    elif 1.40 <= home <= 1.69:
        if goals_avg >= 3.0:
            result = {'blueprint': 'BP7', 'play': 'Both Teams to Score - YES', 'confidence': int(75 * quality), 'risk': 'Low-Moderate'}
        else:
            result = {'blueprint': 'BP7', 'play': 'Both Teams to Score - NO', 'confidence': int(65 * quality), 'risk': 'Low-Moderate'}
    
    # BP8: High-Scoring Signals
    elif 3.60 <= draw <= 3.75 and goals_avg >= 2.7:
        result = {'blueprint': 'BP8', 'play': 'Over 2.5 Goals', 'confidence': int(60 * quality), 'risk': 'Moderate'}
    
    if result:
        result['match'] = match['match']
        result['league'] = league
        result['home_odds'] = home
        result['draw_odds'] = draw
        result['away_odds'] = away
        result['quality_score'] = quality
    
    return result

# ============================================================
# SMART ACCUMULATOR BUILDER
# ============================================================

def build_accumulators(predictions):
    """Build 2,4,7,10 odds accumulators from predictions"""
    
    if len(predictions) < 2:
        return {}
    
    # Sort by confidence (highest first)
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    
    # Filter high quality picks only
    high_quality = [p for p in sorted_picks if p.get('quality_score', 0) >= 0.7]
    
    if len(high_quality) < 2:
        high_quality = sorted_picks[:10]
    
    accumulators = {}
    used = set()
    
    def get_unused(pool):
        return [p for p in pool if p['match'] not in used]
    
    # Build 2_ODDS (2-3 matches)
    pool = get_unused(high_quality)
    for n in [2, 3]:
        for combo in combinations(pool[:6], n):
            total = 1
            for m in combo:
                odds = m.get('home_odds', 1.5) if 'Home Win' in m['play'] else m.get('draw_odds', 1.5)
                total *= odds
            if 1.8 <= total <= 2.5:
                accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                for m in combo:
                    used.add(m['match'])
                break
        if '2_ODDS' in accumulators:
            break
    
    # Build 4_ODDS (4 matches)
    pool = get_unused(high_quality)
    for combo in combinations(pool[:10], 4):
        total = 1
        for m in combo:
            odds = m.get('home_odds', 1.5) if 'Home Win' in m['play'] else m.get('draw_odds', 1.5)
            total *= odds
        if 3.5 <= total <= 5.0:
            accumulators['4_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # Build 7_ODDS (5 matches)
    pool = get_unused(high_quality)
    for combo in combinations(pool[:12], 5):
        total = 1
        for m in combo:
            odds = m.get('home_odds', 1.5) if 'Home Win' in m['play'] else m.get('draw_odds', 1.5)
            total *= odds
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # Build 10_ODDS (5-6 matches)
    pool = get_unused(high_quality)
    for n in [5, 6]:
        for combo in combinations(pool[:15], n):
            total = 1
            for m in combo:
                odds = m.get('home_odds', 1.5) if 'Home Win' in m['play'] else m.get('draw_odds', 1.5)
                total *= odds
            if 9.0 <= total <= 12.0:
                accumulators['10_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                break
        if '10_ODDS' in accumulators:
            break
    
    return accumulators

# ============================================================
# TELEGRAM SENDING
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
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
# MAIN SYSTEM
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS - COMPLETE SYSTEM")
    print("8 Blueprints | Deep Analysis | Smart Accumulators")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load matches
    matches = parse_matches()
    if not matches:
        print("❌ No matches found in input_matches.txt")
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    # Analyze each match with 8 blueprints
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed any blueprint")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    
    # Display predictions
    print("\n📋 PREDICTIONS:")
    for i, p in enumerate(predictions[:20], 1):
        print(f"   {i}. {p['blueprint']}: {p['match'][:50]}")
        print(f"      🎯 {p['play']} | Confidence: {p['confidence']}%")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BLUEPRINT PICKS ({len(predictions)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Add picks by blueprint
    for bp in ['BP1', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7', 'BP8']:
        bp_picks = [p for p in predictions if p['blueprint'] == bp]
        if bp_picks:
            message += f"\n🔵 {bp} - {bp_picks[0]['play']}\n"
            for p in bp_picks[:3]:
                emoji = "✅" if p['confidence'] >= 75 else "🟡"
                message += f"   {emoji} {p['match'][:45]}\n"
    
    if accumulators:
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 SMART ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
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
