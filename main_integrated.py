"""
Main Integrated System - Enhanced Jay Soccer Blueprints
7-Step Pipeline: Blueprint → Form Enhancement → AI Validation → Accumulator Building
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations

# Import local modules
from team_database import TeamDatabase
from ai_analyzer_enhanced import EnhancedAIAnalyzer
from blueprint_engine import BlueprintEngine
from accumulator_builder import build_accumulators

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"

# ============================================================
# STEP 1: PARSE INPUT MATCHES
# ============================================================

def parse_matches():
    """Parse matches from input file"""
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
# STEP 2: BLUEPRINT CLASSIFICATION
# ============================================================

def classify_with_blueprints(matches):
    """Classify matches using BlueprintEngine"""
    engine = BlueprintEngine()
    predictions = []
    
    for match in matches:
        result = engine.classify(match)
        if result:
            predictions.append(result)
    
    return predictions


# ============================================================
# STEP 3: FORM DATA ENHANCEMENT
# ============================================================

def enhance_with_form_data(predictions):
    """Enhance predictions with team form data"""
    db = TeamDatabase()
    
    if db.matches_df is None or db.matches_df.empty:
        print("⚠️ No match data available for form analysis")
        # Return predictions with empty context
        for p in predictions:
            p['team_context'] = {}
        return predictions
    
    enhanced = []
    for p in predictions:
        try:
            context = db.get_match_context({
                'home_team': p.get('home_team', ''),
                'away_team': p.get('away_team', ''),
                'league': p.get('league', '')
            })
            p['team_context'] = context
            enhanced.append(p)
        except Exception as e:
            print(f"⚠️ Error enriching {p.get('match', '')}: {str(e)}")
            p['team_context'] = {}
            enhanced.append(p)
    
    return enhanced


# ============================================================
# STEP 4: AI VALIDATION & ENHANCEMENT
# ============================================================

def validate_with_ai(predictions):
    """Validate predictions with Enhanced AI Analyzer"""
    db = TeamDatabase()
    analyzer = EnhancedAIAnalyzer(team_db=db)
    
    analyzed = analyzer.analyze_batch(predictions)
    
    # Print summary
    summary = analyzer.get_summary(analyzed)
    print(f"\n📊 AI ANALYSIS SUMMARY:")
    print(f"   Total matches: {summary.get('total_matches', 0)}")
    print(f"   Average confidence: {summary.get('avg_confidence', 0)}%")
    print(f"   High confidence (>=80%): {summary.get('high_confidence', 0)}")
    print(f"   Validated picks: {summary.get('validated', 0)}")
    
    if summary.get('decisions'):
        print(f"   AI Decisions breakdown:")
        for decision, count in summary['decisions'].items():
            print(f"      {decision}: {count}")
    
    return analyzed


# ============================================================
# STEP 5: BUILD SMART ACCUMULATORS
# ============================================================

def build_smart_accumulators(predictions):
    """Build accumulators using quality-driven selection"""
    accumulators = build_accumulators(predictions)
    return accumulators


# ============================================================
# STEP 6: GENERATE OUTPUTS
# ============================================================

def save_outputs(predictions, accumulators):
    """Save predictions and accumulators to JSON"""
    
    # Save enhanced predictions
    with open("predictions_enhanced.json", "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"✅ Saved {len(predictions)} predictions to predictions_enhanced.json")
    
    # Save enhanced accumulators
    with open("accumulators_enhanced.json", "w") as f:
        json.dump(accumulators, f, indent=2)
    print(f"✅ Saved {len(accumulators)} accumulators to accumulators_enhanced.json")


# ============================================================
# STEP 7: TELEGRAM NOTIFICATION
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


def build_telegram_message(predictions, accumulators):
    """Build comprehensive Telegram message"""
    # Sort predictions by AI confidence
    top_picks = sorted(predictions, key=lambda x: x.get('ai_confidence', 0), reverse=True)[:15]
    
    message = f"""⚽ JAY SOCCER BLUEPRINTS - ENHANCED AI PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'━'*50}

📊 PREDICTIONS ({len(predictions)})
{'━'*50}
"""
    
    for p in top_picks:
        emoji = p.get('ai_decision', '').split()[0]  # Get emoji from decision
        bp = p.get('blueprint', '')
        match = p.get('match', '')[:45]
        play = p.get('play', '')
        confidence = p.get('ai_confidence', 0)
        
        message += f"\n{emoji} {bp}: {match}\n"
        message += f"   🎯 {play}\n"
        message += f"   📈 Confidence: {confidence}%\n"
    
    if accumulators:
        message += f"\n{'━'*50}\n🎰 ACCUMULATORS\n{'━'*50}\n"
        
        for acc_type, acc_data in accumulators.items():
            odds = acc_data.get('odds', 'N/A')
            quality = acc_data.get('avg_quality', 0)
            message += f"\n{acc_type}: {odds} odds | Quality: {quality:.0f}/100\n"
            
            for i, match in enumerate(acc_data.get('matches', [])[:3], 1):
                match_str = match.get('match', '')[:40]
                message += f"   {i}. {match_str}\n"
    
    message += f"\n{'━'*50}\n⚠️ Bet responsibly!"
    
    return message


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Execute integrated 7-step pipeline"""
    
    print("\n" + "="*70)
    print("⚽ JAY SOCCER BLUEPRINTS - INTEGRATED SYSTEM")
    print("7-Step Pipeline: Classification → Form → AI → Accumulators")
    print("="*70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Clean cache
    for cache_file in ["predictions_enhanced.json", "accumulators_enhanced.json"]:
        if os.path.exists(cache_file):
            os.remove(cache_file)
    
    # ========================================================
    # STEP 1: PARSE INPUT
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 1: PARSING INPUT MATCHES")
    print("─"*70)
    
    matches = parse_matches()
    if not matches:
        print("❌ No matches found")
        return 1
    
    print(f"✅ Loaded {len(matches)} matches from {INPUT_FILE}")
    for i, m in enumerate(matches[:3], 1):
        print(f"   {i}. {m['match'][:50]}")
    
    # ========================================================
    # STEP 2: BLUEPRINT CLASSIFICATION
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 2: BLUEPRINT CLASSIFICATION")
    print("─"*70)
    
    predictions = classify_with_blueprints(matches)
    if not predictions:
        print("❌ No matches passed blueprint classification")
        return 1
    
    print(f"✅ Classified {len(predictions)} matches into blueprints")
    
    # Count by blueprint
    bp_count = {}
    for p in predictions:
        bp = p.get('blueprint', 'Unknown')
        bp_count[bp] = bp_count.get(bp, 0) + 1
    
    for bp, count in sorted(bp_count.items()):
        print(f"   {bp}: {count} predictions")
    
    # ========================================================
    # STEP 3: FORM DATA ENHANCEMENT
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 3: FORM DATA ENHANCEMENT")
    print("─"*70)
    
    predictions = enhance_with_form_data(predictions)
    
    # Count predictions with form data
    with_form_data = sum(1 for p in predictions if p.get('team_context'))
    print(f"✅ Enhanced {with_form_data}/{len(predictions)} predictions with form data")
    
    if with_form_data > 0:
        sample = next(p for p in predictions if p.get('team_context'))
        ctx = sample.get('team_context', {})
        if ctx:
            print(f"\n   Sample enhancement:")
            print(f"      Match: {sample.get('match', '')[:45]}")
            print(f"      Home form score: {ctx.get('home_team_form_score', 'N/A')}")
            print(f"      Away form score: {ctx.get('away_team_form_score', 'N/A')}")
            print(f"      Expected goals: {ctx.get('expected_goals', 'N/A')}")
    
    # ========================================================
    # STEP 4: AI VALIDATION & ENHANCEMENT
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 4: AI VALIDATION & ENHANCEMENT")
    print("─"*70)
    
    predictions = validate_with_ai(predictions)
    
    # ========================================================
    # STEP 5: BUILD SMART ACCUMULATORS
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 5: BUILD SMART ACCUMULATORS")
    print("─"*70)
    
    accumulators = build_smart_accumulators(predictions)
    print(f"✅ Built {len(accumulators)} accumulators")
    
    # ========================================================
    # STEP 6: SAVE OUTPUTS
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 6: SAVE OUTPUTS")
    print("─"*70)
    
    save_outputs(predictions, accumulators)
    
    # ========================================================
    # STEP 7: TELEGRAM NOTIFICATION
    # ========================================================
    print("\n" + "─"*70)
    print("STEP 7: TELEGRAM NOTIFICATION")
    print("─"*70)
    
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        message = build_telegram_message(predictions, accumulators)
        if send_telegram(message):
            print("✅ Telegram notification sent")
        else:
            print("❌ Failed to send Telegram notification")
    else:
        print("⚠️ Telegram not configured (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
    
    # ========================================================
    # FINAL SUMMARY
    # ========================================================
    print("\n" + "="*70)
    print("✅ INTEGRATED PIPELINE COMPLETE")
    print("="*70)
    print(f"📊 Results:")
    print(f"   Matches processed: {len(matches)}")
    print(f"   Predictions made: {len(predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    print(f"\n📁 Output files:")
    print(f"   • predictions_enhanced.json")
    print(f"   • accumulators_enhanced.json")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
