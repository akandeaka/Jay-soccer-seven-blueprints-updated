"""
SOCCER BLUEPRINT SYSTEM - 8 BLUEPRINTS
BP6: Full Time Draw (X)
READS ONLY FROM input_matches.txt
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

# High scoring leagues for BP7 and BP8
HIGH_SCORING_LEAGUES = [
    'bundesliga', 'eredivisie', 'premier league', 
    'epl', 'serie a', 'ligue 1', 'la liga'
]

# ============================================================
# FUNCTION 1: CONVERT CSV/TAB FORMAT TO SYSTEM FORMAT
# ============================================================

def convert_csv_format():
    """Convert CSV/tab format to system format if needed"""
    
    with open(INPUT_FILE, 'r') as f:
        content = f.read()
    
    # Check if it's in CSV/tab format (has tabs and no '|')
    if '\t' in content and '|' not in content:
        print("\n📋 Detected CSV/tab format - converting...")
        lines = content.split('\n')
        data_lines = [l for l in lines[1:] if l.strip() and '\t' in l]
        
        output = []
        for line in data_lines:
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                output.append(parts[0].strip())
                output.append(parts[1].strip())
                output.append(f"{parts[2].strip()} | {parts[3].strip()} | {parts[4].strip()}")
                output.append('')
        
        with open(INPUT_FILE, 'w') as f:
            f.write('\n'.join(output))
        
        print(f"✅ Converted {len(output)//4} matches to correct format")
        return True
    
    return False

# ============================================================
# FUNCTION 2: PARSE INPUT FILE
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
        # Find match name (must contain 'vs')
        if ' vs ' not in lines[i]:
            i += 1
            continue
        
        match = {'match': lines[i]}
        i += 1
        
        # League name
        if i < len(lines) and '|' not in lines[i]:
            match['league'] = lines[i]
            i += 1
        else:
            match['league'] = 'Unknown'
        
        # Odds (Home | Draw | Away)
        if i < len(lines) and '|' in lines[i]:
            odds = re.findall(r'(\d+\.\d+)', lines[i])
            if len(odds) >= 3:
                match['home_odds'] = float(odds[0])
                match['draw_odds'] = float(odds[1])
                match['away_odds'] = float(odds[2])
            else:
                i += 1
                continue
            i += 1
        else:
            i += 1
            continue
        
        matches.append(match)
    
    return matches

# ============================================================
# FUNCTION 3: APPLY 8 BLUEPRINTS
# ============================================================

def apply_blueprints(match):
    """Apply all 8 blueprints to a match"""
    
    home = match.get('home_odds', 0)
    draw = match.get('draw_odds', 0)
    away = match.get('away_odds', 0)
    league = match.get('league', '').lower()
    
    is_high_scoring = any(hl in league for hl in HIGH_SCORING_LEAGUES)
    
    # BP1: Elite Home Banker
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return ('BP1', 'Straight Home Win', 95)
    
    # BP2: Primary Favorite
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return ('BP2', 'Home Win', 90)
    
    # BP3: Moderate Favorite Safety
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return ('BP3', '1X & Over 1.5 Goals', 85)
    
    # BP4: Goal Engine
    if 1.72 <= home <= 1.80:
        return ('BP4', 'Over 1.5 Goals', 75 if is_high_scoring else 65)
    
    # BP5: Defensive Trap
    if 1.90 <= home <= 2.02:
        return ('BP5', '1X & Under 3.5 FT', 70)
    
    # BP6: Strong Draw - FULL TIME DRAW
    if 2.75 <= draw <= 3.39:
        return ('BP6', 'Full Time Draw (X)', 50)
    
    # BP7: BTTS Value Spot
    if 1.40 <= home <= 1.69:
        if is_high_scoring:
            return ('BP7', 'Both Teams to Score - YES', 75)
        else:
            return ('BP7', 'Both Teams to Score - NO', 65)
    
    # BP8: High-Scoring Signals
    if 3.60 <= draw <= 3.75 and is_high_scoring:
        return ('BP8', 'HT 0.5 / Over 2.5 Goals', 60)
    
    return None

# ============================================================
# FUNCTION 4: AI ANALYSIS
# ============================================================

def ai_analyze(match, bp_result):
    """AI validates or suggests alternative"""
    
    bp, play, conf = bp_result
    
    if conf >= 75:
        return conf, "VALIDATED", play
    elif conf >= 60:
        return conf, "CONFIRMED", play
    else:
        return conf, "ALTERNATIVE", play

# ============================================================
# FUNCTION 5: BUILD ACCUMULATORS
# ============================================================

def build_accumulators(predictions):
    """Build accumulators at 2, 4, 7, 10 odds targets"""
    
    if len(predictions) < 2:
        return {}
    
    # Set odds for each prediction
    for p in predictions:
        play = p['play']
        if 'Home Win' in play:
            p['odds'] = p['home_odds']
        elif 'Draw' in play:
            p['odds'] = p['draw_odds']
        else:
            p['odds'] = 1.50
    
    accumulators = {}
    
    def build_accumulators(predictions):
    """
    Build accumulators at 2, 4, 7, 10 odds targets
    EACH ACCUMULATOR HAS UNIQUE MATCHES - NO DUPLICATES ACROSS ACCUMULATORS
    """
    
    if len(predictions) < 2:
        return {}
    
    # Set odds for each prediction
    for p in predictions:
        play = p['play']
        if 'Home Win' in play:
            p['odds'] = p['home_odds']
        elif 'Draw' in play:
            p['odds'] = p['draw_odds']
        else:
            p['odds'] = 1.50
    
    # Sort by confidence (highest first)
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    
    accumulators = {}
    used_matches = set()  # Track which matches are already used
    
    # Helper function to get unused picks
    def get_unused_picks(limit=None):
        available = [p for p in sorted_picks if p['match'] not in used_matches]
        if limit:
            return available[:limit]
        return available
    
    # 2 ODDS ACCUMULATOR (2-3 matches)
    available = get_unused_picks(10)
    for n in [2, 3]:
        for combo in combinations(available, n):
            total = 1
            for m in combo:
                total *= m['odds']
            if 1.8 <= total <= 2.5:
                accumulators['2_ODDS'] = {'matches': combo, 'odds': round(total, 2)}
                # Mark these matches as used
                for m in combo:
                    used_matches.add(m['match'])
                break
        if '2_ODDS' in accumulators:
            break
    
    # 4 ODDS ACCUMULATOR (4 matches) - using remaining picks
    available = get_unused_picks(12)
    for combo in combinations(available, 4):
        total = 1
        for m in combo:
            total *= m['odds']
        if 3.5 <= total <= 5.0:
            accumulators['4_ODDS'] = {'matches': combo, 'odds': round(total, 2)}
            for m in combo:
                used_matches.add(m['match'])
            break
    
    # 7 ODDS ACCUMULATOR (5 matches) - using remaining picks
    available = get_unused_picks(15)
    for combo in combinations(available, 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': combo, 'odds': round(total, 2)}
            for m in combo:
                used_matches.add(m['match'])
            break
    
    # 10 ODDS ACCUMULATOR (5-6 matches) - using remaining picks
    available = get_unused_picks(20)
    for n in [5, 6]:
        if len(available) >= n:
            for combo in combinations(available, n):
                total = 1
                for m in combo:
                    total *= m['odds']
                if 9.0 <= total <= 12.0:
                    accumulators['10_ODDS'] = {'matches': combo, 'odds': round(total, 2)}
                    for m in combo:
                        used_matches.add(m['match'])
                    break
        if '10_ODDS' in accumulators:
            break
    
    return accumulators
# ============================================================
# FUNCTION 6: SEND TO TELEGRAM
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured - skipping")
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

# ============================================================
# MAIN SYSTEM
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM")
    print("8 BLUEPRINTS | BP6: FULL TIME DRAW")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Delete old cache
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old cache")
    
    # Convert CSV format if needed
    if os.path.exists(INPUT_FILE):
        convert_csv_format()
    
    # Parse matches
    matches = parse_matches()
    
    if not matches:
        print("\n❌ No matches found in input_matches.txt")
        print("\n📝 Expected format:")
        print("   Team A vs Team B")
        print("   League Name")
        print("   1.55 | 4.20 | 5.50")
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    # Apply blueprints
    predictions = []
    for match in matches:
        bp_result = apply_blueprints(match)
        if bp_result:
            bp, play, conf = bp_result
            ai_conf, ai_decision, ai_play = ai_analyze(match, bp_result)
            
            predictions.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': bp,
                'play': ai_play,
                'confidence': ai_conf,
                'decision': ai_decision,
                'home_odds': match['home_odds'],
                'draw_odds': match['draw_odds'],
                'away_odds': match['away_odds']
            })
    
    if not predictions:
        print("\n❌ No matches passed any blueprint")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints:")
    for p in predictions:
        print(f"   {p['blueprint']}: {p['match']} - {p['play']} ({p['confidence']:.0f}%) - {p['decision']}")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - AI PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 AI ANALYZED PICKS
"""
    
    for p in predictions[:15]:
        emoji = "✅" if p['decision'] == 'VALIDATED' else "🟡" if p['decision'] == 'CONFIRMED' else "⚠️"
        message += f"""
{emoji} {p['blueprint']}: {p['match']}
   🎯 {p['play']}
   📈 AI Confidence: {p['confidence']:.0f}%
   🔍 Decision: {p['decision']}
"""
    
    if accumulators:
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATOR PICKS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            target = name.split('_')[0]
            message += f"\n{name} (Target: {target} odds)\nTotal Odds: {acc['odds']}\n"
            for i, m in enumerate(acc['matches'][:3], 1):
                message += f"   {i}. {m['match'][:35]}...\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Always bet responsibly!\n📊 AI predictions for informational purposes only."
    
    # Send to Telegram
    send_telegram(message)
    
    # Save results
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ SYSTEM EXECUTION COMPLETE")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Matches read: {len(matches)}")
    print(f"   Matches passed: {len(predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
