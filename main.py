cat > main.py << 'EOF'
"""
JAY SOCCER BLUEPRINTS - KEY MATCHES ONLY
Focus on high-quality leagues for better accuracy
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
# ONLY THESE LEAGUES WILL BE SCANNED (QUALITY OVER QUANTITY)
# ============================================================

KEY_LEAGUES = [
    'premier league', 'bundesliga', 'la liga', 'serie a', 'ligue 1',
    'eredivisie', 'primeira liga', 'championship', 'belgian pro league',
    'scottish premiership', 'turkish super lig', 'russian premier league',
    'mls', 'argentina', 'brazil', 'mexico', 'japan', 'korea', 'australia',
    'swiss super league', 'austrian bundesliga', 'greek superleague',
    'danish superliga', 'swedish allsvenskan', 'norwegian eliteserien'
]

def is_key_league(league_name):
    """Check if league is in key leagues list"""
    if not league_name:
        return False
    league_lower = league_name.lower()
    for key in KEY_LEAGUES:
        if key in league_lower:
            return True
    return False

# ============================================================
# LEAGUE GOAL AVERAGES
# ============================================================

LEAGUE_GOALS = {
    'premier league': 2.8, 'bundesliga': 3.2, 'la liga': 2.5,
    'serie a': 2.6, 'ligue 1': 2.7, 'eredivisie': 3.1,
    'championship': 2.6, 'mls': 2.8, 'brazil': 2.5,
}

def get_league_goals(league):
    league_lower = league.lower()
    for key, avg in LEAGUE_GOALS.items():
        if key in league_lower:
            return avg
    return 2.5

# ============================================================
# PARSE INPUT FILE - ONLY KEY LEAGUES
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
    skipped = 0
    
    print(f"\n📊 Scanning for key leagues only...")
    
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
        
        # SKIP if not a key league
        if not is_key_league(match['league']):
            skipped += 1
            # Skip odds line
            if i < len(lines) and '|' in lines[i]:
                i += 1
            continue
        
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
        print(f"   ✅ {match['match'][:40]} - {match['league']}")
    
    print(f"\n📊 Key leagues found: {len(matches)} matches")
    print(f"   Skipped (non-key leagues): {skipped} matches")
    return matches

# ============================================================
# 8 BLUEPRINTS
# ============================================================

def analyze_match(match):
    home = match.get('home_odds', 0)
    draw = match.get('draw_odds', 0)
    away = match.get('away_odds', 0)
    league = match.get('league', 'Unknown')
    
    league_goals = get_league_goals(league)
    
    # BP1
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return {'blueprint': 'BP1', 'play': 'Straight Home Win', 'confidence': 95, 'odds': home, 'match': match['match'], 'league': league}
    
    # BP2
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return {'blueprint': 'BP2', 'play': 'Home Win', 'confidence': 90, 'odds': home, 'match': match['match'], 'league': league}
    
    # BP3
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return {'blueprint': 'BP3', 'play': '1X & Over 1.5 Goals', 'confidence': 85, 'odds': home, 'match': match['match'], 'league': league}
    
    # BP4
    if 1.72 <= home <= 1.80:
        return {'blueprint': 'BP4', 'play': 'Over 1.5 Goals', 'confidence': 75, 'odds': home, 'match': match['match'], 'league': league}
    
    # BP5
    if 1.90 <= home <= 2.02:
        return {'blueprint': 'BP5', 'play': '1X & Under 3.5 FT', 'confidence': 70, 'odds': home, 'match': match['match'], 'league': league}
    
    # BP6
    if 2.75 <= draw <= 3.39:
        if league_goals >= 3.0:
            return {'blueprint': 'BP6', 'play': 'Draw or GG (Draw OR Both Teams to Score)', 'confidence': 68, 'odds': draw, 'match': match['match'], 'league': league}
        else:
            return {'blueprint': 'BP6', 'play': 'Draw or Under 2.5 Goals', 'confidence': 65, 'odds': draw, 'match': match['match'], 'league': league}
    
    # BP7
    if 1.40 <= home <= 1.69:
        if league_goals >= 3.0:
            return {'blueprint': 'BP7', 'play': 'Both Teams to Score - YES', 'confidence': 75, 'odds': home, 'match': match['match'], 'league': league}
        else:
            return {'blueprint': 'BP7', 'play': 'Both Teams to Score - NO', 'confidence': 65, 'odds': home, 'match': match['match'], 'league': league}
    
    # BP8
    if 3.60 <= draw <= 3.75 and league_goals >= 2.7:
        return {'blueprint': 'BP8', 'play': 'Over 2.5 Goals', 'confidence': 60, 'odds': draw, 'match': match['match'], 'league': league}
    
    return None

# ============================================================
# BUILD ACCUMULATORS
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
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
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS - KEY MATCHES ONLY")
    print("Higher accuracy by focusing on quality leagues")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
    
    matches = parse_matches()
    if not matches:
        print("\n❌ No key league matches found!")
        print("\n📋 Key leagues being scanned:")
        for league in KEY_LEAGUES[:15]:
            print(f"   - {league.title()}")
        return 1
    
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed blueprints")
        return 1
    
    print(f"\n✅ {len(predictions)} predictions from key leagues")
    
    accumulators = build_accumulators(predictions)
    
    message = f"""⚽ JAY SOCCER BLUEPRINTS - KEY MATCHES
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PREDICTIONS ({len(predictions)} from top leagues)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for p in predictions[:20]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} {p['blueprint']}: {p['match'][:45]}\n   🎯 {p['play']} | {p['confidence']}%"
    
    if accumulators:
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            for i, m in enumerate(acc['matches'], 1):
                message += f"   {i}. {m['match'][:45]}\n"
                message += f"      🎯 {m['play']}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!"
    
    send_telegram(message)
    
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n✅ Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF
