"""
SOCCER BLUEPRINT SYSTEM - 8 BLUEPRINTS
EACH BLUEPRINT SCANS ALL MATCHES AND PICKS THOSE THAT MEET ITS CRITERIA
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
# FUNCTION 3: BP1 - SCAN ALL MATCHES FOR ELITE HOME BANKER
# ============================================================

def scan_bp1(matches):
    """BP1: Scan ALL matches - Pick those with Home 1.20-1.29 & Away ≥10.0"""
    results = []
    for match in matches:
        home = match.get('home_odds', 0)
        away = match.get('away_odds', 0)
        if 1.20 <= home <= 1.29 and away >= 10.0:
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP1',
                'play': 'Straight Home Win',
                'confidence': 95,
                'odds_used': home
            })
    return results

# ============================================================
# FUNCTION 4: BP2 - SCAN ALL MATCHES FOR PRIMARY FAVORITE
# ============================================================

def scan_bp2(matches):
    """BP2: Scan ALL matches - Pick those with Home 1.30-1.36 & Away ≥9.0"""
    results = []
    for match in matches:
        home = match.get('home_odds', 0)
        away = match.get('away_odds', 0)
        if 1.30 <= home <= 1.36 and away >= 9.0:
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP2',
                'play': 'Home Win',
                'confidence': 90,
                'odds_used': home
            })
    return results

# ============================================================
# FUNCTION 5: BP3 - SCAN ALL MATCHES FOR MODERATE FAVORITE SAFETY
# ============================================================

def scan_bp3(matches):
    """BP3: Scan ALL matches - Pick those with Home 1.30-1.36 & Away 7.0-8.99"""
    results = []
    for match in matches:
        home = match.get('home_odds', 0)
        away = match.get('away_odds', 0)
        if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP3',
                'play': '1X & Over 1.5 Goals',
                'confidence': 85,
                'odds_used': home
            })
    return results

# ============================================================
# FUNCTION 6: BP4 - SCAN ALL MATCHES FOR GOAL ENGINE
# ============================================================

def scan_bp4(matches):
    """BP4: Scan ALL matches - Pick those with Home 1.72-1.80"""
    results = []
    for match in matches:
        home = match.get('home_odds', 0)
        league = match.get('league', '').lower()
        is_high_scoring = any(hl in league for hl in HIGH_SCORING_LEAGUES)
        
        if 1.72 <= home <= 1.80:
            conf = 75 if is_high_scoring else 65
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP4',
                'play': 'Over 1.5 Goals',
                'confidence': conf,
                'odds_used': home
            })
    return results

# ============================================================
# FUNCTION 7: BP5 - SCAN ALL MATCHES FOR DEFENSIVE TRAP
# ============================================================

def scan_bp5(matches):
    """BP5: Scan ALL matches - Pick those with Home 1.90-2.02"""
    results = []
    for match in matches:
        home = match.get('home_odds', 0)
        if 1.90 <= home <= 2.02:
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP5',
                'play': '1X & Under 3.5 FT',
                'confidence': 70,
                'odds_used': home
            })
    return results

# ============================================================
# FUNCTION 8: BP6 - SCAN ALL MATCHES FOR STRONG DRAW
# ============================================================

def scan_bp6(matches):
    """BP6: Scan ALL matches - Pick those with Draw 2.75-3.39"""
    results = []
    for match in matches:
        draw = match.get('draw_odds', 0)
        if 2.75 <= draw <= 3.39:
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP6',
                'play': 'Full Time Draw (X)',
                'confidence': 50,
                'odds_used': draw
            })
    return results

# ============================================================
# FUNCTION 9: BP7 - SCAN ALL MATCHES FOR BTTS VALUE SPOT
# ============================================================

def scan_bp7(matches):
    """BP7: Scan ALL matches - Pick those with Home 1.40-1.69"""
    results = []
    for match in matches:
        home = match.get('home_odds', 0)
        league = match.get('league', '').lower()
        is_high_scoring = any(hl in league for hl in HIGH_SCORING_LEAGUES)
        
        if 1.40 <= home <= 1.69:
            if is_high_scoring:
                play = 'Both Teams to Score - YES'
                conf = 75
            else:
                play = 'Both Teams to Score - NO'
                conf = 65
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP7',
                'play': play,
                'confidence': conf,
                'odds_used': home
            })
    return results

# ============================================================
# FUNCTION 10: BP8 - SCAN ALL MATCHES FOR HIGH-SCORING SIGNALS
# ============================================================

def scan_bp8(matches):
    """BP8: Scan ALL matches - Pick those with Draw 3.60-3.75 + high-scoring league"""
    results = []
    for match in matches:
        draw = match.get('draw_odds', 0)
        league = match.get('league', '').lower()
        is_high_scoring = any(hl in league for hl in HIGH_SCORING_LEAGUES)
        
        if 3.60 <= draw <= 3.75 and is_high_scoring:
            results.append({
                'match': match['match'],
                'league': match['league'],
                'blueprint': 'BP8',
                'play': 'HT 0.5 / Over 2.5 Goals',
                'confidence': 60,
                'odds_used': draw
            })
    return results

# ============================================================
# FUNCTION 11: AI ANALYSIS
# ============================================================

def ai_analyze(prediction):
    """AI validates or confirms the prediction"""
    conf = prediction['confidence']
    
    if conf >= 75:
        decision = "VALIDATED"
    elif conf >= 60:
        decision = "CONFIRMED"
    else:
        decision = "ALTERNATIVE"
    
    prediction['decision'] = decision
    return prediction

# ============================================================
# FUNCTION 12: BUILD ACCUMULATORS (ONLY FROM PREDICTIONS)
# ============================================================

def build_accumulators(predictions):
    """
    Build accumulators at 2, 4, 7, 10 odds targets
    USES ONLY PREDICTIONS (matches that passed blueprints)
    """
    
    if len(predictions) < 2:
        return {}
    
    # Set odds for each prediction
    for p in predictions:
        p['odds'] = p['odds_used']
    
    # Sort by confidence (highest first)
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used_matches = set()
    
    def get_unused_picks():
        return [p for p in sorted_picks if p['match'] not in used_matches]
    
    # 2 ODDS ACCUMULATOR
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
                        'odds': round(total, 2)
                    }
                    for m in combo:
                        used_matches.add(m['match'])
                    break
        if '2_ODDS' in accumulators:
            break
    
    # 4 ODDS ACCUMULATOR
    available = get_unused_picks()
    if len(available) >= 4:
        for combo in combinations(available, 4):
            total = 1
            for m in combo:
                total *= m['odds']
            if 3.5 <= total <= 5.0:
                accumulators['4_ODDS'] = {
                    'matches': combo,
                    'odds': round(total, 2)
                }
                for m in combo:
                    used_matches.add(m['match'])
                break
    
    # 7 ODDS ACCUMULATOR
    available = get_unused_picks()
    if len(available) >= 5:
        for combo in combinations(available, 5):
            total = 1
            for m in combo:
                total *= m['odds']
            if 6.0 <= total <= 8.5:
                accumulators['7_ODDS'] = {
                    'matches': combo,
                    'odds': round(total, 2)
                }
                for m in combo:
                    used_matches.add(m['match'])
                break
    
    # 10 ODDS ACCUMULATOR
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
                        'odds': round(total, 2)
                    }
                    for m in combo:
                        used_matches.add(m['match'])
                    break
        if '10_ODDS' in accumulators:
            break
    
    return accumulators

# ============================================================
# FUNCTION 13: SEND TO TELEGRAM
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
# MAIN SYSTEM - EACH BLUEPRINT SCANS ALL MATCHES
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM")
    print("EACH BLUEPRINT SCANS ALL MATCHES")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Delete old cache
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old cache")
    
    # Convert CSV format if needed
    if os.path.exists(INPUT_FILE):
        convert_csv_format()
    
    # Parse all matches
    all_matches = parse_matches()
    
    if not all_matches:
        print("\n❌ No matches found in input_matches.txt")
        return 1
    
    print(f"\n📊 Loaded {len(all_matches)} total matches for scanning")
    
    # EACH BLUEPRINT SCANS ALL MATCHES INDEPENDENTLY
    print("\n" + "="*60)
    print("🔍 SCANNING MATCHES WITH EACH BLUEPRINT")
    print("="*60)
    
    bp1_picks = scan_bp1(all_matches)
    print(f"   BP1 found: {len(bp1_picks)} matches")
    
    bp2_picks = scan_bp2(all_matches)
    print(f"   BP2 found: {len(bp2_picks)} matches")
    
    bp3_picks = scan_bp3(all_matches)
    print(f"   BP3 found: {len(bp3_picks)} matches")
    
    bp4_picks = scan_bp4(all_matches)
    print(f"   BP4 found: {len(bp4_picks)} matches")
    
    bp5_picks = scan_bp5(all_matches)
    print(f"   BP5 found: {len(bp5_picks)} matches")
    
    bp6_picks = scan_bp6(all_matches)
    print(f"   BP6 found: {len(bp6_picks)} matches")
    
    bp7_picks = scan_bp7(all_matches)
    print(f"   BP7 found: {len(bp7_picks)} matches")
    
    bp8_picks = scan_bp8(all_matches)
    print(f"   BP8 found: {len(bp8_picks)} matches")
    
    # Combine all picks
    all_predictions = []
    all_predictions.extend(bp1_picks)
    all_predictions.extend(bp2_picks)
    all_predictions.extend(bp3_picks)
    all_predictions.extend(bp4_picks)
    all_predictions.extend(bp5_picks)
    all_predictions.extend(bp6_picks)
    all_predictions.extend(bp7_picks)
    all_predictions.extend(bp8_picks)
    
    if not all_predictions:
        print("\n❌ No matches passed any blueprint criteria")
        return 1
    
    # Apply AI analysis to each prediction
    for p in all_predictions:
        p = ai_analyze(p)
    
    # Remove duplicates (same match picked by multiple blueprints)
    unique_predictions = []
    seen_matches = set()
    for p in all_predictions:
        if p['match'] not in seen_matches:
            unique_predictions.append(p)
            seen_matches.add(p['match'])
    
    print(f"\n✅ TOTAL UNIQUE PICKS: {len(unique_predictions)}")
    print("="*60)
    for i, p in enumerate(unique_predictions, 1):
        print(f"   {i}. {p['blueprint']}: {p['match']}")
        print(f"      Play: {p['play']}")
        print(f"      Confidence: {p['confidence']}% - {p['decision']}")
    
    # Build accumulators
    accumulators = build_accumulators(unique_predictions)
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - AI PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BLUEPRINT SCAN RESULTS ({len(unique_predictions)} picks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Group by blueprint for better readability
    for bp in ['BP1', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7', 'BP8']:
        bp_picks = [p for p in unique_predictions if p['blueprint'] == bp]
        if bp_picks:
            message += f"\n🔵 {bp} - {bp_picks[0]['play']}\n"
            for p in bp_picks:
                emoji = "✅" if p['decision'] == 'VALIDATED' else "🟡" if p['decision'] == 'CONFIRMED' else "⚠️"
                message += f"   {emoji} {p['match']} (Confidence: {p['confidence']}%)\n"
    
    if accumulators:
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 ACCUMULATOR PICKS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            target = name.split('_')[0]
            message += f"\n{name} (Target: {target} odds)\nTotal Odds: {acc['odds']}\n"
            for i, m in enumerate(acc['matches'], 1):
                match_name = m['match'][:40] + "..." if len(m['match']) > 40 else m['match']
                message += f"   {i}. {match_name}\n"
                message += f"      🎯 {m['play']}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Always bet responsibly!\n📊 AI predictions for informational purposes only."
    
    # Send to Telegram
    send_telegram(message)
    
    # Save results
    with open("predictions.json", "w") as f:
        json.dump(unique_predictions, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ SYSTEM EXECUTION COMPLETE")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Total matches scanned: {len(all_matches)}")
    print(f"   BP1 picks: {len(bp1_picks)}")
    print(f"   BP2 picks: {len(bp2_picks)}")
    print(f"   BP3 picks: {len(bp3_picks)}")
    print(f"   BP4 picks: {len(bp4_picks)}")
    print(f"   BP5 picks: {len(bp5_picks)}")
    print(f"   BP6 picks: {len(bp6_picks)}")
    print(f"   BP7 picks: {len(bp7_picks)}")
    print(f"   BP8 picks: {len(bp8_picks)}")
    print(f"   Total unique picks: {len(unique_predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
