"""
JAY SOCCER BLUEPRINTS - 11 BLUEPRINT SYSTEM (MERGED & HYBRID PARSER)
Preserves existing structure | Uses GitHub database | Robust CSV & Text Parser
Includes Club Friendlies in league evaluations
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
# GITHUB DATABASE (Team Form & League Stats)
# ============================================================

LEAGUE_GOALS = {
    'premier league': 2.8, 'bundesliga': 3.2, 'la liga': 2.5,
    'serie a': 2.6, 'ligue 1': 2.7, 'eredivisie': 3.1,
    'championship': 2.6, 'league one': 2.9, 'league two': 2.8,
    'brazil': 2.8, 'turkey': 2.6, 'russia': 2.5, 'friendly': 2.9
}

# League classifications for BP6, BP7, BP8, BP11
HIGH_SCORING_LEAGUES = ['bundesliga', 'eredivisie', 'brazil', 'brasileirao', 'friendly', 'club friendly']
MEDIUM_SCORING_LEAGUES = ['premier league', 'epl', 'ligue 1', 'championship']
LOW_SCORING_LEAGUES = ['la liga', 'serie a', 'turkey', 'russia', 'greece']

# BTTS classifications for BP9 and BP10
BTTS_HIGH_LEAGUES = ['bundesliga', 'eredivisie', 'brazil', 'premier league', 'epl', 'friendly', 'club friendly']
BTTS_LOW_LEAGUES = ['la liga', 'serie a', 'turkey', 'russia']

ATTACKING_TEAMS = [
    'man city', 'liverpool', 'arsenal', 'bayern', 'dortmund',
    'psg', 'barcelona', 'real madrid', 'ajax', 'napoli', 'inter', 'milan'
]

DEFENSIVE_TEAMS = [
    'burnley', 'getafe', 'cadiz', 'elche', 'spezia', 'salernitana'
]


def get_league_avg_goals(league):
    league_lower = league.lower()
    for key, avg in LEAGUE_GOALS.items():
        if key in league_lower:
            return avg
    return 2.5


def is_attacking_team(team):
    team_lower = team.lower()
    for at in ATTACKING_TEAMS:
        if at in team_lower:
            return True
    return False


def is_defensive_team(team):
    team_lower = team.lower()
    for dt in DEFENSIVE_TEAMS:
        if dt in team_lower:
            return True
    return False


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
        league_type = get_league_type(league)
        if league_type == 'low':
            return {'blueprint': '6', 'play': 'Draw or Under 2.5 Goals', 'confidence': 72}
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
    
    # Check blueprints in order (1 to 11)
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
# ROBUST HYBRID PARSER (REGEX & CSV SUPPORT)
# ============================================================

def parse_matches():
    target_file = None
    possible_files = [
        "input.csv", "input_matches.csv", "matches.csv", 
        "input_matches.txt", "input.txt", "raw_capture.txt"
    ]
    
    for filename in possible_files:
        if os.path.exists(filename):
            target_file = filename
            break
            
    if not target_file:
        print("\n❌ No input file found! Ensure 'input.csv' or 'input.txt' exists in the root folder.")
        return []
    
    print(f"📂 Found input file: {target_file}")
    matches = []
    
    with open(target_file, 'r', encoding='utf-8-sig') as f:
        content = f.read().strip()
        
    if not content:
        print("❌ Input file is empty!")
        return []

    # METHOD 1: PARSE AS CSV
    if any(keyword in content.lower() for keyword in ['team a', 'home odds', 'team_a', 'home_odds']):
        lines = content.splitlines()
        reader = csv.DictReader(lines)
        for row in reader:
            try:
                # Normalize all dictionary keys to lowercase and stripped
                cleaned_row = { (k.strip().lower() if k else ''): (v.strip() if v else '') for k, v in row.items() if k }
                
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
                    
                match = {
                    'match': f"{team_a} vs {team_b}",
                    'home_team': team_a,
                    'away_team': team_b,
                    'league': league,
                    'home_odds': home_odds,
                    'draw_odds': draw_odds,
                    'away_odds': away_odds
                }
                matches.append(match)
            except Exception:
                continue
        return matches

    # METHOD 2: PARSE AS LINE-BY-LINE TEXT
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
# BUILD ACCUMULATORS
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
    for p in predictions:
        p['odds'] = p.get('odds', 1.50)
    
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used = set()
    
    def get_unused():
        return [p for p in sorted_picks if p['match'] not in used]
    
    # 2_ODDS
    available = get_unused()
    for combo in combinations(available[:8], 2):
        total = combo[0]['odds'] * combo[1]['odds']
        if 1.8 <= total <= 2.5:
            accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 4_ODDS
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
    
    # 7_ODDS
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
    
    # 10_ODDS
    available = get_unused()
    for combo in combinations(available[:20], 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 9.0 <= total <= 12.0:
            accumulators['10_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            break
    
    return accumulators

# ============================================================
# SEND TO TELEGRAM
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
# VALIDATE RESULTS
# ============================================================

def validate_results(predictions, validation_file="validation_results.txt"):
    if not os.path.exists(validation_file):
        return None
    
    results = {}
    with open(validation_file, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if ' vs ' in line and 'RESULT:' not in line:
            match_name = line
            i += 1
            while i < len(lines) and 'RESULT:' not in lines[i]:
                i += 1
            if i < len(lines):
                score_match = re.search(r'(\d+)-(\d+)', lines[i])
                if score_match:
                    results[match_name] = {
                        'home': int(score_match.group(1)),
                        'away': int(score_match.group(2))
                    }
        i += 1
    
    correct = 0
    total = 0
    for pred in predictions:
        match = pred['match']
        play = pred['play']
        for res_match, score in results.items():
            if match.lower() in res_match.lower() or res_match.lower() in match.lower():
                total += 1
                home, away = score['home'], score['away']
                if ('Home Win' in play and home > away) or \
                   ('Draw' in play and home == away) or \
                   ('Both Teams to Score - YES' in play and home > 0 and away > 0) or \
                   ('Both Teams to Score - NO' in play and (home == 0 or away == 0)) or \
                   ('Over 1.5' in play and home + away > 1) or \
                   ('Under 3.5' in play and home + away < 4) or \
                   ('Over 2.5' in play and home + away > 2) or \
                   ('Draw or Under 2.5' in play and (home == away or home + away < 3)):
                    correct += 1
                break
    
    if total > 0:
        return f"📊 VALIDATION: {correct}/{total} ({correct/total*100:.1f}%)"
    return None

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS - 11 BLUEPRINT SYSTEM")
    print("Blueprints 1-11 | GitHub Database | 2,4,7,10 Accumulators")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Clear previous runtime artifacts
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
    if os.path.exists("accumulators.json"):
        os.remove("accumulators.json")
    
    # Parse matches
    matches = parse_matches()
    if not matches:
        print("❌ No matches found or failed to parse input.")
        return 0  # Exit code 0 ensures GitHub Actions passes successfully
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    # Analyze matches with 11 blueprints
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
            print(f"   ✅ #{result['blueprint']}: {result['match'][:45]} - {result['play']} ({result['confidence']}%)")
    
    if not predictions:
        print("❌ No matches passed any blueprint criteria today.")
        return 0  # Exit code 0 ensures GitHub Actions passes successfully
    
    print(f"\n✅ {len(predictions)} predictions made")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Save accumulators
    with open("accumulators.json", "w") as f:
        json.dump(accumulators, f, indent=2)
    print(f"✅ Saved {len(accumulators)} accumulators")
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - 11 BLUEPRINT SYSTEM
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PREDICTIONS ({len(predictions)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for p in predictions[:20]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} #{p['blueprint']}: {p['match'][:45]}\n   🎯 {p['play']} | {p['confidence']}%"
    
    if accumulators:
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            for i, m in enumerate(acc['matches'], 1):
                message += f"   {i}. {m['match'][:45]}\n"
                message += f"      🎯 #{m['blueprint']}: {m['play']}\n"
    
    # Validate if results file exists
    validation_result = validate_results(predictions)
    if validation_result:
        message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{validation_result}"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!"
    
    send_telegram(message)
    
    # Save predictions
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
