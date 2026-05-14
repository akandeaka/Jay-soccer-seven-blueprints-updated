"""
VALIDATION SYSTEM - Manual File Mode
Reads results from validation_results.txt
"""

import os
import sys
import json
import re
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ============================================================
# FUNCTION: Parse validation file
# ============================================================

def parse_validation_file(filepath="validation_results.txt"):
    """Parse validation file with results"""
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return []
    
    with open(filepath, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return []
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    results = []
    i = 0
    
    while i < len(lines):
        if ' vs ' not in lines[i]:
            i += 1
            continue
        
        match = {'match': lines[i]}
        i += 1
        
        # League
        if i < len(lines) and '|' not in lines[i] and 'RESULT' not in lines[i]:
            match['league'] = lines[i]
            i += 1
        else:
            match['league'] = 'Unknown'
        
        # Skip odds lines if present
        while i < len(lines) and 'RESULT' not in lines[i]:
            i += 1
        
        # RESULT line
        if i < len(lines) and 'RESULT:' in lines[i]:
            result_text = lines[i].replace('RESULT:', '').strip()
            parts = result_text.split('|')
            if len(parts) >= 1:
                score_part = parts[0].strip()
                score_match = re.search(r'(\d+)-(\d+)', score_part)
                if score_match:
                    match['home_score'] = int(score_match.group(1))
                    match['away_score'] = int(score_match.group(2))
                
                if len(parts) > 1:
                    match['result'] = parts[1].strip()
                else:
                    if match['home_score'] > match['away_score']:
                        match['result'] = 'Home Win'
                    elif match['home_score'] < match['away_score']:
                        match['result'] = 'Away Win'
                    else:
                        match['result'] = 'Draw'
            i += 1
        else:
            i += 1
            continue
        
        results.append(match)
    
    return results

# ============================================================
# FUNCTION: Validate predictions
# ============================================================

def validate_predictions(predictions, validation_results):
    """Compare predictions with actual results"""
    
    validated = []
    
    for pred in predictions:
        pred_match = pred.get('match', '')
        pred_play = pred.get('play', '')
        pred_confidence = pred.get('confidence', 0)
        pred_blueprint = pred.get('blueprint', '')
        
        # Find matching result
        actual = None
        for res in validation_results:
            if pred_match.lower() == res['match'].lower():
                actual = res
                break
        
        if actual:
            home_score = actual.get('home_score', 0)
            away_score = actual.get('away_score', 0)
            
            # Determine if prediction was correct
            is_correct = False
            
            if 'Home Win' in pred_play:
                is_correct = (home_score > away_score)
            elif 'Draw' in pred_play:
                is_correct = (home_score == away_score)
            elif 'Both Teams to Score' in pred_play:
                if 'YES' in pred_play.upper():
                    is_correct = (home_score > 0 and away_score > 0)
                elif 'NO' in pred_play.upper():
                    is_correct = (home_score == 0 or away_score == 0)
            elif 'Over 1.5' in pred_play:
                is_correct = (home_score + away_score > 1)
            elif 'Under 3.5' in pred_play:
                is_correct = (home_score + away_score < 4)
            elif 'Over 2.5' in pred_play:
                is_correct = (home_score + away_score > 2)
            elif '1X & Over 1.5' in pred_play:
                home_not_lost = (home_score >= away_score)
                is_correct = home_not_lost and (home_score + away_score > 1)
            elif '1X & Under 3.5' in pred_play:
                home_not_lost = (home_score >= away_score)
                is_correct = home_not_lost and (home_score + away_score < 4)
            elif 'Draw or GG' in pred_play:
                is_correct = (home_score == away_score) or (home_score > 0 and away_score > 0)
            elif 'Draw or Under 2.5' in pred_play:
                is_correct = (home_score == away_score) or (home_score + away_score < 3)
            
            validated.append({
                'match': pred_match,
                'blueprint': pred_blueprint,
                'predicted_play': pred_play,
                'confidence': pred_confidence,
                'actual_score': f"{home_score}-{away_score}",
                'actual_result': actual.get('result', 'Unknown'),
                'is_correct': is_correct
            })
            print(f"   {'✅' if is_correct else '❌'} {pred_match}: {pred_play} → {home_score}-{away_score}")
        else:
            validated.append({
                'match': pred_match,
                'blueprint': pred_blueprint,
                'predicted_play': pred_play,
                'confidence': pred_confidence,
                'actual_score': 'NOT_FOUND',
                'actual_result': 'NOT_FOUND',
                'is_correct': False
            })
            print(f"   ⚠️ NOT FOUND: {pred_match}")
    
    return validated

# ============================================================
# FUNCTION: Generate report
# ============================================================

def generate_report(validated):
    """Generate performance report"""
    
    total = len([v for v in validated if v['actual_score'] != 'NOT_FOUND'])
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Group by blueprint
    bp_stats = {}
    for v in validated:
        if v['actual_score'] != 'NOT_FOUND':
            bp = v['blueprint']
            if bp not in bp_stats:
                bp_stats[bp] = {'total': 0, 'correct': 0}
            bp_stats[bp]['total'] += 1
            if v['is_correct']:
                bp_stats[bp]['correct'] += 1
    
    # Build report
    report = f"""⚽ JAY SOCCER BLUEPRINTS - VALIDATION REPORT
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OVERALL STATISTICS
   Total Validated: {total}
   Correct: {correct}
   Wrong: {total - correct}
   Accuracy: {accuracy:.1f}%

📊 BY BLUEPRINT
"""
    
    for bp in sorted(bp_stats.keys()):
        stats = bp_stats[bp]
        bp_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        report += f"   {bp}: {stats['correct']}/{stats['total']} ({bp_acc:.1f}%)\n"
    
    return report, accuracy, correct, total

# ============================================================
# FUNCTION: Send to Telegram
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured - skipping")
        return False
    
    import requests
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
    print("⚽ VALIDATION SYSTEM - Manual File Mode")
    print("Reads results from validation_results.txt")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load predictions
    if not os.path.exists("predictions.json"):
        print("❌ No predictions.json found. Run main.py first.")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Load validation results
    validation_results = parse_validation_file("validation_results.txt")
    
    if not validation_results:
        print("\n❌ No validation_results.txt found!")
        print("\n📝 Please create validation_results.txt with this format:")
        print("")
        print("   Brighton vs Wolves")
        print("   Premier League")
        print("   2.10 | 3.40 | 3.30")
        print("   Over 2.5: 1.75 | Under 2.5: 2.05")
        print("   BTTS Yes: 1.65 | BTTS No: 2.15")
        print("   RESULT: 3-0 | Home Win")
        print("")
        return 1
    
    print(f"✅ Loaded {len(validation_results)} validation results")
    
    # Validate
    print("\n🔍 Comparing predictions with results...")
    validated = validate_predictions(predictions, validation_results)
    
    # Generate report
    report, accuracy, correct, total = generate_report(validated)
    
    print(f"\n📊 RESULTS:")
    print(f"   Validated: {total} matches")
    print(f"   Correct: {correct}")
    print(f"   Wrong: {total - correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    # Send to Telegram
    send_telegram(report)
    
    # Save report
    with open("validation_report.md", "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to validation_report.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
