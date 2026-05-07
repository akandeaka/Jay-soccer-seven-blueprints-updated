"""
SOCCER BLUEPRINT SYSTEM - 8 BLUEPRINTS
BP6: Full Time Draw (X)
READS ONLY FROM input_matches.txt
ACCUMULATORS USE ONLY PREDICTIONS (MATCHES THAT PASSED BLUEPRINTS)
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
    
    try:
        with open(INPUT_FILE, 'r') as f:
            content = f.read()
    except:
        return False
    
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
        
        print(f"✅ Converted {len(output)//4} matches")
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
        return ('BP1', 'Straight Home Win', 95, home)
    
    # BP2: Primary Favorite
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return ('BP2', 'Home Win', 90, home)
    
    # BP3: Moderate Favorite Safety
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return ('BP3', '1X & Over 1.5 Goals', 85, home)
    
    # BP4: Goal Engine
    if 1.72 <= home <= 1.80:
        conf = 75 if is_high_scoring else 65
        return ('BP4', 'Over 1.5 Goals', conf, home)
    
    # BP5: Defensive Trap
    if 1.90 <= home <= 2.02:
        return ('BP5', '1X & Under 3.5 FT', 70, home)
    
    # BP6: Strong Draw - FULL TIME DRAW
    if 2.75 <= draw <= 3.39:
        return ('BP6', 'Full Time Draw (X)', 50, draw)
    
    # BP7: BTTS Value Spot
    if 1.40 <= home <= 1.69:
        if is_high_scoring:
            return ('BP7', 'Both Teams to Score - YES', 75, home)
        else:
            return ('BP7', 'Both Teams to Score - NO', 65, home)
    
    # BP8: High-Scoring Signals
    if 3.60 <= draw <= 3.75 and is_high_scoring:
        return ('BP8', 'HT 0.5 / Over 2.5 Goals', 60, draw)
    
    return None

# ============================================================
# FUNCTION 4: AI ANALYSIS
# ============================================================

def ai_analyze(match, bp_result):
    """AI validates or suggests alternative"""
    bp, play, conf, odds_used = bp_result
    
    if conf >= 75:
        return conf, "VALIDATED", play, odds_used
    elif conf >= 60:
        return conf, "CONFIRMED", play, odds_used
    else:
        return conf, "ALTERNATIVE", play, odds_used

# ============================================================
# FUNCTION 5: BUILD ACCUMULATORS (ONLY FROM PREDICTIONS)
# ============================================================

def build_accumulators(predictions):
    """
    Build accumulators at 2, 4, 7, 10 odds targets
    USES ONLY PREDICTIONS (matches that passed blueprints)
    NO DUPLICATE MATCHES ACROSS ACCUMULATORS
    """
    
    if len(predictions) < 2:
        print("\n⚠️ Not enough predictions to build accumulators (need at least 2)")
        return {}
    
    print(f"\n🔨 Building accumulators from {len(predictions)} predictions:")
    
    # Set odds for each prediction based on the play
    for p in predictions:
        play = p['play']
        if 'Home Win' in play:
            p['odds'] = p.get('home_odds', 1.50)
        elif 'Draw' in play:
            p['odds'] = p.get('draw_odds', 1.50)
        else:
            p['odds'] = 1.50
        print(f"   {p['blueprint']}: {p['match']} - {p['play']} (Odds: {p['odds']})")
    
    # Sort by confidence (highest first)
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used_matches = set()
    
    def get_unused_picks():
        return [p for p in sorted_picks if p['match'] not in used_matches]
    
    # 2 ODDS ACCUMULATOR (2-3 matches)
    available = get_unused_picks()
    for n in [2, 3]:
        if len(available) >= n:
            for combo in combinations(available, n):
                total = 1
                for m in combo:
                    total *= m['odds']
                if 1.8 <= total <= 2.5:
                    accumulators['2_ODDS'] = {
                        'matches': combo, 
                        'odds': round(total, 2),
                        'plays': [m['play'] for m in combo]
                    }
                    for m in combo:
                        used_matches.add(m['match'])
                    print(f"\n   ✅ 2_ODDS built with {len(combo)} matches @ {round(total, 2)} odds")
                    break
        if '2_ODDS' in accumulators:
            break
    
    # 4 ODDS ACCUMULATOR (4 matches)
    available = get_unused_picks()
    if len(available) >= 4:
        for combo in combinations(available, 4):
            total = 1
            for m in combo:
                total *= m['odds']
            if 3.5 <= total <= 5.0:
                accumulators['4_ODDS'] = {
                    'matches': combo, 
                    'odds': round(total, 2),
                    'plays': [m['play'] for m in combo]
                }
                for m in combo:
                    used_matches.add(m['match'])
                print(f"   ✅ 4_ODDS built with 4 matches @ {round(total, 2)} odds")
                break
    
    # 7 ODDS ACCUMULATOR (5 matches)
    available = get_unused_picks()
    if len(available) >= 5:
        for combo in combinations(available, 5):
            total = 1
            for m in combo:
                total *= m['odds']
            if 6.0 <= total <= 8.5:
                accumulators['7_ODDS'] = {
                    'matches': combo, 
                    'odds': round(total, 2),
                    'plays': [m['play'] for m in combo]
                }
                for m in combo:
                    used_matches.add(m['match'])
                print(f"   ✅ 7_ODDS built with 5 matches @ {round(total, 2)} odds")
                break
    
    # 10 ODDS ACCUMULATOR (5-6 matches)
    available = get_unused_picks()
    for n in [5, 6]:
        if len(available) >= n:
            for combo in combinations(available, n):
                total = 1
                for m in combo:
                    total *= m['odds']
                if 9.0 <= total <= 12.0:
                    accumulators['10_ODDS'] = {
                        'matches': combo, 
                        'odds': round(total, 2),
                        'plays': [m['play'] for m in combo]
                    }
                    for m in combo:
                        used_matches.add(m['match'])
                    print(f"   ✅ 10_ODDS built with {n} matches @ {round(total, 2)} odds")
                    break
        if '10_ODDS' in accumulators:
            break
    
    if not accumulators:
        print("   ⚠️ No accumulators could be built from predictions")
    
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
    print("ACCUMULATORS USE ONLY PREDICTIONS")
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
    
    print(f"\n📊 Loaded {len(matches)} total matches from input file")
    
    # Apply blueprints to get predictions
    predictions = []
    for match in matches:
        bp_result = apply_blueprints(match)
        if bp_result:
            bp, play, conf, odds_used = bp_result
            ai_conf, ai_decision, ai_play, ai_odds = ai_analyze(match, bp_result)
            
            predictions.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': bp,
                'play': ai_play,
                'confidence': ai_conf,
                'decision': ai_decision,
                'odds_used': ai_odds,
                'home_odds': match.get('home_odds', 0),
                'draw_odds': match.get('draw_odds', 0),
                'away_odds': match.get('away_odds', 0)
            })
    
    if not predictions:
        print("\n❌ No matches passed any blueprint")
        return 1
    
    # Display predictions (THESE ARE THE ONLY MATCHES FOR ACCUMULATORS)
    print(f"\n✅ {len(predictions)} matches passed blueprints (THESE ARE YOUR SYSTEM PICKS):")
    print("="*60)
    for i, p in enumerate(predictions, 1):
        print(f"   {i}. {p['blueprint']}: {p['match']}")
        print(f"      Play: {p['play']}")
        print(f"      Confidence: {p['confidence']:.0f}%")
        print(f"      Decision: {p['decision']}")
    print("="*60)
    
    # Build accumulators (ONLY from predictions)
    accumulators = build_accumulators(predictions)
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - AI PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 AI ANALYZED PICKS ({len(predictions)} matches)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for p in predictions[:20]:
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
            for i, m in enumerate(acc['matches'], 1):
                # Truncate long match names
                match_name = m['match'][:40] + "..." if len(m['match']) > 40 else m['match']
                message += f"   {i}. {match_name}\n"
                message += f"      🎯 {m['play']}\n"
    
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
    print(f"   Total matches in input file: {len(matches)}")
    print(f"   Matches that passed blueprints: {len(predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    
    if accumulators:
        print(f"\n📈 ACCUMULATORS BUILT FROM PREDICTIONS ONLY:")
        for name, acc in accumulators.items():
            print(f"   {name}: {len(acc['matches'])} matches @ {acc['odds']} odds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
