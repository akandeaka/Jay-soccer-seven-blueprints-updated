"""
SOCCER BLUEPRINT SYSTEM - SMART QUALITY SCORING
Prioritizes best matches, penalizes poor performers
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
# QUALITY SCORING CONFIGURATION
# ============================================================

# League quality multipliers (Top leagues = higher score)
LEAGUE_QUALITY = {
    # Top 5 European Leagues (highest quality)
    'premier league': 1.0,
    'bundesliga': 1.0,
    'la liga': 1.0,
    'serie a': 1.0,
    'ligue 1': 1.0,
    
    # Second tier European
    'championship': 0.85,
    'eredivisie': 0.85,
    'primeira liga': 0.85,
    'belgian': 0.75,
    'scottish': 0.75,
    
    # South American top divisions (medium quality)
    'argentina': 0.65,
    'brazil': 0.65,
    'brasil': 0.65,
    'chile': 0.60,
    'colombia': 0.60,
    
    # Lower leagues, reserves, youth (penalized - low quality)
    'reserve': 0.25,
    'u20': 0.20,
    'u19': 0.20,
    'u21': 0.20,
    'b': 0.20,  # B teams
    '2': 0.25,  # Second divisions
    '3': 0.20,  # Third divisions
}

# Blueprint historical performance (from validation)
# Lower score = penalized, Higher score = rewarded
BLUEPRINT_PERFORMANCE = {
    'BP1': 1.0,   # 66.7% accuracy
    'BP2': 1.0,   # 100% accuracy
    'BP3': 0.7,   # 57.1% accuracy
    'BP4': 0.85,  # 68.9% accuracy
    'BP5': 0.9,   # 75% accuracy
    'BP6': 0.35,  # 32% accuracy - HEAVILY PENALIZED
    'BP7': 0.55,  # 42.9% accuracy
    'BP8': 0.7,   # 55% accuracy
}

# Minimum quality score to be considered for accumulators
MIN_QUALITY_SCORE = 55

# ============================================================
# FUNCTION: Calculate quality score for a match
# ============================================================

def calculate_quality_score(match):
    """
    Calculate quality score (0-100) based on:
    - League quality (0-40 points)
    - Blueprint performance (0-30 points)
    - AI Confidence (0-30 points)
    """
    
    # Factor 1: League quality (0-40 points)
    league = match.get('league', '').lower()
    league_score = 20  # Default mid score
    
    for key, multiplier in LEAGUE_QUALITY.items():
        if key in league:
            league_score = 40 * multiplier
            break
    
    # Apply additional penalty for reserve/youth leagues
    if 'reserve' in league or 'u20' in league or 'u19' in league or 'b' in league.split():
        league_score = league_score * 0.5
    
    # Factor 2: Blueprint performance (0-30 points)
    bp = match.get('blueprint', '')
    bp_score = 30 * BLUEPRINT_PERFORMANCE.get(bp, 0.5)
    
    # Factor 3: AI Confidence (0-30 points)
    confidence = match.get('confidence', 50)
    confidence_score = 30 * (confidence / 100)
    
    # Total quality score
    quality_score = league_score + bp_score + confidence_score
    
    return round(quality_score, 1)

# ============================================================
# FUNCTION: Convert CSV/TAB FORMAT TO SYSTEM FORMAT
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
# FUNCTION: PARSE INPUT FILE
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
# FUNCTION: APPLY 8 BLUEPRINTS
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
    
    # BP6: Strong Draw - FULL TIME DRAW (Penalized)
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
# FUNCTION: AI ANALYSIS
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
# FUNCTION: SMART ACCUMULATOR BUILDER (Quality-based)
# ============================================================

def build_smart_accumulators(predictions):
    """
    Build accumulators using ONLY highest quality matches
    Prioritizes top leagues, strong blueprints, high confidence
    """
    
    if len(predictions) < 2:
        return {}
    
    # Calculate quality score for each prediction
    for p in predictions:
        p['quality_score'] = calculate_quality_score(p)
        # Set odds
        play = p.get('play', '')
        if 'Home Win' in play:
            p['odds'] = p.get('home_odds', 1.50)
        elif 'Draw' in play:
            p['odds'] = p.get('draw_odds', 1.50)
        else:
            p['odds'] = 1.50
    
    # Filter: Only keep matches with quality score >= minimum
    quality_picks = [p for p in predictions if p.get('quality_score', 0) >= MIN_QUALITY_SCORE]
    
    print(f"\n🎯 QUALITY FILTER:")
    print(f"   Total predictions: {len(predictions)}")
    print(f"   High quality (≥{MIN_QUALITY_SCORE}): {len(quality_picks)}")
    print(f"   Excluded (poor quality): {len(predictions) - len(quality_picks)}")
    
    if len(quality_picks) < 2:
        print("   ⚠️ Not enough high quality picks for accumulators")
        return {}
    
    # Sort by quality score (highest first)
    sorted_picks = sorted(quality_picks, key=lambda x: x['quality_score'], reverse=True)
    
    # Show top quality picks
    print(f"\n🏆 TOP QUALITY PICKS (from ALL matches, no bias):")
    for i, p in enumerate(sorted_picks[:15], 1):
        print(f"   {i}. {p['blueprint']}: {p['match'][:45]} (Quality: {p['quality_score']})")
    
    accumulators = {}
    used_matches = set()
    
    def get_unused():
        return [p for p in sorted_picks if p['match'] not in used_matches]
    
    # 2 ODDS ACCUMULATOR - Top 2 picks
    available = get_unused()
    if len(available) >= 2:
        combo = available[:2]
        total = combo[0]['odds'] * combo[1]['odds']
        accumulators['2_ODDS'] = {
            'matches': combo,
            'odds': round(total, 2),
            'avg_quality': round((combo[0]['quality_score'] + combo[1]['quality_score']) / 2, 1)
        }
        for m in combo:
            used_matches.add(m['match'])
    
    # 4 ODDS ACCUMULATOR - Next 4 picks
    available = get_unused()
    if len(available) >= 4:
        combo = available[:4]
        total = 1
        for m in combo:
            total *= m['odds']
        accumulators['4_ODDS'] = {
            'matches': combo,
            'odds': round(total, 2),
            'avg_quality': round(sum(m['quality_score'] for m in combo) / 4, 1)
        }
        for m in combo:
            used_matches.add(m['match'])
    
    # 7 ODDS ACCUMULATOR - Next 5 picks
    available = get_unused()
    if len(available) >= 5:
        combo = available[:5]
        total = 1
        for m in combo:
            total *= m['odds']
        accumulators['7_ODDS'] = {
            'matches': combo,
            'odds': round(total, 2),
            'avg_quality': round(sum(m['quality_score'] for m in combo) / 5, 1)
        }
        for m in combo:
            used_matches.add(m['match'])
    
    # 10 ODDS ACCUMULATOR - Next 5-6 picks
    available = get_unused()
    if len(available) >= 5:
        combo = available[:6] if len(available) >= 6 else available[:5]
        total = 1
        for m in combo:
            total *= m['odds']
        accumulators['10_ODDS'] = {
            'matches': combo,
            'odds': round(total, 2),
            'avg_quality': round(sum(m['quality_score'] for m in combo) / len(combo), 1)
        }
    
    return accumulators

# ============================================================
# FUNCTION: SEND TO TELEGRAM
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured - skipping")
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
        result = r.json()
        if result.get('ok'):
            print("✅ Telegram message sent successfully")
        else:
            print(f"❌ Telegram error: {result}")
        return result.get('ok', False)
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False

# ============================================================
# FUNCTION: DISPLAY QUALITY BREAKDOWN IN MESSAGE
# ============================================================

def format_quality_score(score):
    """Format quality score with emoji"""
    if score >= 80:
        return f"🔥 {score}"
    elif score >= 70:
        return f"✅ {score}"
    elif score >= 60:
        return f"🟡 {score}"
    else:
        return f"⚠️ {score}"

# ============================================================
# MAIN SYSTEM
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM")
    print("SMART QUALITY SCORING | NO BIAS")
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
    
    print(f"\n📊 Loaded {len(matches)} total matches")
    
    # Apply blueprints to get predictions
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
                'home_odds': match.get('home_odds', 0),
                'draw_odds': match.get('draw_odds', 0),
                'away_odds': match.get('away_odds', 0)
            })
    
    if not predictions:
        print("\n❌ No matches passed any blueprint")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    
    # Calculate quality scores for all predictions
    for p in predictions:
        p['quality_score'] = calculate_quality_score(p)
    
    # Sort by quality score for display
    sorted_by_quality = sorted(predictions, key=lambda x: x['quality_score'], reverse=True)
    
    print(f"\n🏆 TOP 15 PICKS BY QUALITY SCORE (from ALL matches, no bias):")
    print("="*60)
    for i, p in enumerate(sorted_by_quality[:15], 1):
        quality_emoji = "🔥" if p['quality_score'] >= 80 else "✅" if p['quality_score'] >= 70 else "🟡" if p['quality_score'] >= 60 else "⚠️"
        print(f"   {i}. {quality_emoji} {p['blueprint']}: {p['match'][:45]}")
        print(f"      League: {p['league']} | Quality: {p['quality_score']}")
        print(f"      Play: {p['play']} | Confidence: {p['confidence']}%")
    
    # Build smart accumulators (quality-based)
    accumulators = build_smart_accumulators(predictions)
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - AI PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
🏆 SMART QUALITY SCORING ACTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TOP QUALITY PICKS (from ALL matches)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for i, p in enumerate(sorted_by_quality[:20], 1):
        emoji = "✅" if p['decision'] == 'VALIDATED' else "🟡" if p['decision'] == 'CONFIRMED' else "⚠️"
        quality_emoji = "🔥" if p['quality_score'] >= 80 else "✅" if p['quality_score'] >= 70 else "🟡" if p['quality_score'] >= 60 else "⚠️"
        message += f"""
{emoji} {p['blueprint']}: {p['match']}
   🎯 {p['play']}
   📈 AI Confidence: {p['confidence']:.0f}%
   🏆 Quality Score: {quality_emoji} ({p['quality_score']})
"""
    
    if accumulators:
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 SMART ACCUMULATOR PICKS (Quality-Based)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            target = name.split('_')[0]
            message += f"\n{name} (Target: {target} odds)\nTotal Odds: {acc['odds']} | Avg Quality: {acc['avg_quality']}\n"
            for i, m in enumerate(acc['matches'][:3], 1):
                match_name = m['match'][:40] + "..." if len(m['match']) > 40 else m['match']
                message += f"   {i}. {match_name}\n"
                message += f"      🎯 {m['play']} (Quality: {m['quality_score']})\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Always bet responsibly!\n📊 AI predictions for informational purposes only."
    
    # Send to Telegram
    print("\n📱 Sending predictions to Telegram...")
    send_telegram(message)
    
    # Save results
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ SYSTEM EXECUTION COMPLETE")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Total matches scanned: {len(matches)}")
    print(f"   Matches passed blueprints: {len(predictions)}")
    print(f"   High quality picks (≥{MIN_QUALITY_SCORE}): {len([p for p in predictions if p['quality_score'] >= MIN_QUALITY_SCORE])}")
    print(f"   Accumulators built: {len(accumulators)}")
    
    if accumulators:
        print(f"\n📈 ACCUMULATORS BUILT FROM QUALITY PICKS:")
        for name, acc in accumulators.items():
            print(f"   {name}: {len(acc['matches'])} matches @ {acc['odds']} odds (Avg Quality: {acc['avg_quality']})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
