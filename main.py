"""
JAY SOCCER BLUEPRINTS - 11 BLUEPRINT SYSTEM
Includes Club Friendlies & Robust CSV/Text Auto-Detection
"""

import os
import sys
import json
import re
import csv
import requests
from datetime import datetime
from itertools import combinations

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ============================================================
# DATABASE & LEAGUE CLASSIFICATIONS
# ============================================================

LEAGUE_GOALS = {
    'premier league': 2.8, 'bundesliga': 3.2, 'la liga': 2.5,
    'serie a': 2.6, 'ligue 1': 2.7, 'eredivisie': 3.1,
    'championship': 2.6, 'league one': 2.9, 'league two': 2.8,
    'brazil': 2.8, 'turkey': 2.6, 'russia': 2.5, 'friendly': 2.9,
    'europa league': 2.8, 'champions league': 2.9
}

HIGH_SCORING_LEAGUES = ['bundesliga', 'eredivisie', 'brazil', 'brasileirao', 'friendly', 'club friendly']
MEDIUM_SCORING_LEAGUES = ['premier league', 'epl', 'ligue 1', 'championship', 'europa league']
LOW_SCORING_LEAGUES = ['la liga', 'serie a', 'turkey', 'russia', 'greece']

BTTS_HIGH_LEAGUES = ['bundesliga', 'eredivisie', 'brazil', 'premier league', 'epl', 'friendly', 'club friendly']
BTTS_LOW_LEAGUES = ['la liga', 'serie a', 'turkey', 'russia']


def get_league_type(league):
    league_lower = league.lower()
    if any(hs in league_lower for hs in HIGH_SCORING_LEAGUES):
        return 'high'
    elif any(ms in league_lower for ms in MEDIUM_SCORING_LEAGUES):
        return 'medium'
    else:
        return 'low'

# ============================================================
# 11 BLUEPRINTS (Labels 1-11)
# ============================================================

def check_blueprint_1(home, away):
    """#1: Elite Home Banker - Home 1.20-1.29, Away ≥10.0"""
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return {'blueprint': '1', 'play': 'Straight Home Win', 'confidence': 95}
    return None

def check_blueprint_2(home, away):
    """#2: Primary Favorite - Home 1.30-1.36, Away ≥9.0"""
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return {'blueprint': '2', 'play': 'Home Win', 'confidence': 90}
    return None

def check_blueprint_3(home, away):
    """#3: Moderate Favorite Safety - Home 1.30-1.36, Away 7.0-8.99"""
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return {'blueprint': '3', 'play': '1X & Over 1.5 Goals', 'confidence': 85}
    return None

def check_blueprint_4(home):
    """#4: Goal Engine - Home 1.72-1.80"""
    if 1.72 <= home <= 1.80:
        return {'blueprint': '4', 'play': 'Over 1.5 Goals', 'confidence': 75}
    return None

def check_blueprint_5(home):
    """#5: Defensive Trap - Home 1.90-2.02"""
    if 1.90 <= home <= 2.02:
        return {'blueprint': '5', 'play': '1X & Under 3.5 FT', 'confidence': 70}
    return None

def check_blueprint_6(draw, league):
    """#6: Strong Draw (Low Scoring) - Draw 2.75-2.95"""
    if 2.75 <= draw <= 2.95:
        return {'blueprint': '6', 'play': 'Draw or Under 2.5 Goals', 'confidence': 68}
    return None

def check_blueprint_7(draw, league):
    """#7: Strong Draw (Medium Scoring) - Draw 2.96-3.20"""
    if 2.96 <= draw <= 3.20:
        return {'blueprint': '7', 'play': 'Draw or Over 2.5 Goals', 'confidence': 65}
    return None

def check_blueprint_8(draw, league):
    """#8: Strong Draw (High Scoring) - Draw 3.21-3.60"""
    if 3.21 <= draw <= 3.60:
        league_type = get_league_type(league)
        if league_type == 'high':
            return {'blueprint': '8', 'play': 'Draw or GG (Draw OR Both Teams to Score)', 'confidence': 68}
        return {'blueprint': '8', 'play': 'Draw or GG', 'confidence': 65}
    return None

def check_blueprint_9(home, league):
    """#9: BTTS Defensive - Home 1.40-1.55"""
    if 1.40 <= home <= 1.55:
        league_lower = league.lower()
        if any(bl in league_lower for bl in BTTS_LOW_LEAGUES):
            return {'blueprint': '9', 'play': 'Both Teams to Score - NO', 'confidence': 55}
    return None

def check_blueprint_10(home, league):
    """#10: BTTS Attacking - Home 1.56-1.75"""
    if 1.56 <= home <= 1.75:
        league_lower = league.lower()
        if any(bh in league_lower for bh in BTTS_HIGH_LEAGUES):
            return {'blueprint': '10', 'play': 'Both Teams to Score - YES', 'confidence': 70}
        return {'blueprint': '10', 'play': 'Both Teams to Score - YES', 'confidence': 65}
    return None

def check_blueprint_11(draw, league):
    """#11: High-Scoring Signals - Draw 3.60-3.75 + high league"""
    if 3.60 <= draw <= 3.75:
        league_type = get_league_type(league)
        if league_type == 'high':
            return {'blueprint': '11', 'play': 'Over 2.5 Goals', 'confidence': 60}
        return {'blueprint': '11', 'play': 'Over 2.5 Goals', 'confidence': 60}
    return None


def analyze_match(match):
    home = match.get('home_odds', 0)
    draw = match.get('draw_odds', 0)
    away = match.get('away_odds', 0)
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
        result['odds'] = result.get('odds', home if home > 0 else draw)
        result['home_odds'] = home
        result['draw_odds'] = draw
        result['away_odds'] = away
        return result
    
    return None

# ============================================================
# UNIVERSAL PARSER
# ============================================================

def parse_matches():
    # Hardcode targeted file path
    target_file = "input_matches.txt"
    
    if not os.path.exists(target_file):
        print(f"\n❌ Input file '{target_file}' not found in root directory!")
        return []
    
    print(f"📂 Found input file: {target_file}")
    
    with open(target_file, 'r', encoding='utf-8-sig') as f:
        content = f.read().strip()
        
    if not content:
        print(f"❌ '{target_file}' is empty!")
        return []

    # Clean appended text/errors from content if present
    content = content.split("The system did not generate")[0].strip()
    matches = []

    # 1. PARSE AS CSV (If commas exist and headers match)
    if ',' in content and any(h in content.lower() for h in ['team a', 'home odds', 'team_a', 'home_odds']):
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        reader = csv.DictReader(lines)
        for row in reader:
            try:
                cleaned_row = {(k.strip().lower() if k else ''): (v.strip() if v else '') for k, v in row.items() if k}
                
                team_a = cleaned_row.get('team a') or cleaned_row.get('team_a') or cleaned_row.get('home team') or ''
                team_b = cleaned_row.get('team b') or cleaned_row.get('team_b') or cleaned_row.get('away team') or ''
                league = cleaned_row.get('league', 'Unknown')
                
                if not team_a or not team_b:
                    continue
                
                def parse_odd(val):
                    match = re.search(r'(\d+\.\d+|\d+)', str(val))
                    return float(match.group(1)) if match else 0.0

                home_odds = parse_odd(cleaned_row.get('home odds') or cleaned_row.get('home_odds'))
                draw_odds = parse_odd(cleaned_row.get('draw odds') or cleaned_row.get('draw_odds'))
                away_odds = parse_odd(cleaned_row.get('away odds') or cleaned_row.get('away_odds'))
                    
                matches.append({
                    'match': f"{team_a} vs {team_b}",
                    'home_team': team_a,
                    'away_team': team_b,
                    'league': league,
                    'home_odds': home_odds,
                    'draw_odds': draw_odds,
                    'away_odds': away_odds
                })
            except Exception:
                continue
        return matches

    # 2. PARSE AS PIPE/LINE TEXT FORMAT
    lines = [l.strip() for l in content.split('\n') if l.strip()]
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
# ACCUMULATOR BUILDER & MAIN EXECUTION
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
    for p in predictions:
        p['odds'] = p.get('odds', 1.50)
    
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used = set()
    
    available = [p for p in sorted_picks if p['match'] not in used]
    for combo in combinations(available[:8], 2):
        total = combo[0]['odds'] * combo[1]['odds']
        if 1.8 <= total <= 2.5:
            accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
            
    return accumulators


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return False
    
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
    print("⚽ JAY SOCCER BLUEPRINTS - 11 BLUEPRINT SYSTEM")
    print("Blueprints 1-11 | GitHub Database | 2,4,7,10 Accumulators")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    matches = parse_matches()
    if not matches:
        print("❌ No matches found or failed to parse input.")
        return 0
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
            print(f"   ✅ #{result['blueprint']}: {result['match'][:45]} - {result['play']} ({result['confidence']}%)")
    
    if not predictions:
        print("❌ No matches passed any blueprint criteria today.")
        return 0
    
    print(f"\n✅ {len(predictions)} predictions made")
    
    accumulators = build_accumulators(predictions)
    
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n✅ Execution finished successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
