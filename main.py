"""
JAY SOCCER BLUEPRINTS - UPDATED BP6
BP6: Draw or GG / Draw or Under 2.5 Goals (NO Full Time Draw)
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"

# ============================================================
# BP6 DECISION MATRIX - UPDATED (NO Full Time Draw)
# ============================================================

def determine_bp6_play(draw_odds, league, home_team, away_team):
    """BP6: Draw or GG / Draw or Under 2.5 - NO Full Time Draw"""
    
    if not (2.75 <= draw_odds <= 3.39):
        return None
    
    league_lower = league.lower()
    
    # High scoring leagues (Bundesliga, Eredivisie, Premier League) -> Draw or GG
    if 'bundesliga' in league_lower or 'eredivisie' in league_lower or 'premier' in league_lower or 'epl' in league_lower:
        return ('Draw or GG (Draw OR Both Teams to Score)', 68)
    
    # All other leagues -> Draw or Under 2.5 Goals
    else:
        return ('Draw or Under 2.5 Goals', 65)


def determine_bp7_play(home_odds, league):
    """BP7: BTTS Value Spot"""
    if not (1.40 <= home_odds <= 1.69):
        return None
    
    league_lower = league.lower()
    
    if 'bundesliga' in league_lower or 'eredivisie' in league_lower:
        return ('Both Teams to Score - YES', 75)
    else:
        return ('Both Teams to Score - NO', 65)


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
        teams = lines[i].split(' vs ')
        match['home_team'] = teams[0].strip()
        match['away_team'] = teams[1].strip() if len(teams) > 1 else ''
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
    home_team = match.get('home_team', '')
    away_team = match.get('away_team', '')
    
    # BP1: Elite Home Banker
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return {
            'blueprint': 'BP1', 'play': 'Straight Home Win',
            'confidence': 95, 'risk': 'Ultra-Low',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP2: Primary Favorite
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return {
            'blueprint': 'BP2', 'play': 'Home Win',
            'confidence': 90, 'risk': 'Low',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP3: Moderate Favorite Safety
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return {
            'blueprint': 'BP3', 'play': '1X & Over 1.5 Goals',
            'confidence': 85, 'risk': 'Low-Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP4: Goal Engine
    if 1.72 <= home <= 1.80:
        return {
            'blueprint': 'BP4', 'play': 'Over 1.5 Goals',
            'confidence': 75, 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP5: Defensive Trap
    if 1.90 <= home <= 2.02:
        return {
            'blueprint': 'BP5', 'play': '1X & Under 3.5 FT',
            'confidence': 70, 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP6: Strong Draw - UPDATED (NO Full Time Draw)
    bp6_result = determine_bp6_play(draw, league, home_team, away_team)
    if bp6_result:
        play, confidence = bp6_result
        return {
            'blueprint': 'BP6', 'play': play,
            'confidence': confidence, 'risk': 'Medium',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP7: BTTS Value Spot
    bp7_result = determine_bp7_play(home, league)
    if bp7_result:
        play, confidence = bp7_result
        return {
            'blueprint': 'BP7', 'play': play,
            'confidence': confidence, 'risk': 'Low-Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP8: High-Scoring Signals
    if 3.60 <= draw <= 3.75:
        league_lower = league.lower()
        if 'bundesliga' in league_lower or 'eredivisie' in league_lower or 'premier' in league_lower:
            return {
                'blueprint': 'BP8', 'play': 'Over 2.5 Goals',
                'confidence': 60, 'risk': 'Moderate',
                'match': match['match'], 'league': league,
                'home_odds': home, 'draw_odds': draw, 'away_odds': away
            }
    
    return None


# ============================================================
# ACCUMULATOR BUILDER
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
    for p in predictions:
        if 'Home Win' in p['play']:
            p['odds'] = p['home_odds']
        elif 'Draw' in p['play']:
            p['odds'] = p['draw_odds']
        else:
            p['odds'] = 1.50
    
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used = set()
    
    def get_unused():
        return [p for p in sorted_picks if p['match'] not in used]
    
    available = get_unused()
    for combo in combinations(available[:6], 2):
        total = combo[0]['odds'] * combo[1]['odds']
        if 1.8 <= total <= 2.5:
            accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            break
    
    return accumulators


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


def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS - UPDATED")
    print("BP6: Draw or GG / Draw or Under 2.5 (NO Full Time Draw)")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old cache")
    
    matches = parse_matches()
    if not matches:
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed blueprints")
        return 1
    
    print(f"\n✅ {len(predictions)} predictions")
    
    accumulators = build_accumulators(predictions)
    
    message = f"""⚽ JAY SOCCER BLUEPRINTS - PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PICKS ({len(predictions)})
"""
    
    for p in predictions[:15]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} {p['blueprint']}: {p['match'][:45]}\n   🎯 {p['play']} | Conf: {p['confidence']}%"
    
    if accumulators:
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            for m in acc['matches']:
                message += f"   • {m['match'][:45]}\n"
                message += f"     🎯 {m['play']}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!"
    
    send_telegram(message)
    
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
