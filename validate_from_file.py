"""
VALIDATION SYSTEM - Multi-Line Mode (Your Original Format)
"""

import os
import sys
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def parse_validation_file(filepath="validation_results.txt"):
    """Parse multi-line validation file"""
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return {}
    
    with open(filepath, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return {}
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    results = {}
    i = 0
    
    while i < len(lines):
        # Find match name (must contain 'vs')
        if ' vs ' not in lines[i]:
            i += 1
            continue
        
        match_name = lines[i]
        i += 1
        
        # Skip league line
        if i < len(lines) and '|' not in lines[i] and 'RESULT:' not in lines[i]:
            i += 1
        
        # Skip odds lines until RESULT
        while i < len(lines) and 'RESULT:' not in lines[i]:
            i += 1
        
        # Parse RESULT line
        if i < len(lines) and 'RESULT:' in lines[i]:
            result_text = lines[i].replace('RESULT:', '').strip()
            score_match = re.search(r'(\d+)-(\d+)', result_text)
            if score_match:
                home_score = int(score_match.group(1))
                away_score = int(score_match.group(2))
                results[match_name] = {
                    'home_score': home_score,
                    'away_score': away_score
                }
            i += 1
        else:
            i += 1
    
    print(f"✅ Loaded {len(results)} validation results")
    return results


def validate_predictions(predictions, validation_results):
    """Compare predictions with actual results"""
    
    validated = []
    matched = 0
    
    for pred in predictions:
        pred_match = pred.get('match', '').replace('**', '').strip()
        pred_play = pred.get('play', '')
        pred_confidence = pred.get('confidence', 0)
        pred_blueprint = pred.get('blueprint', '')
        
        # Try exact match
        actual = validation_results.get(pred_match)
        
        # Try partial match if not found
        if not actual:
            for key in validation_results:
                if pred_match.lower() in key.lower() or key.lower() in pred_match.lower():
                    actual = validation_results[key]
                    break
        
        if actual:
            matched += 1
            home_score = actual['home_score']
            away_score = actual['away_score']
            
            # Determine if correct
            is_correct = False
            
            if 'Home Win' in pred_play:
                is_correct = (home_score > away_score)
            elif 'Draw' in pred_play:
                is_correct = (home_score == away_score)
            elif 'Both Teams to Score' in pred_play:
                if 'YES' in pred_play.upper():
                    is_correct = (home_score > 0 and away_score > 0)
                else:
                    is_correct = (home_score == 0 or away_score == 0)
            elif 'Over 1.5' in pred_play:
                is_correct = (home_score + away_score > 1)
            elif 'Under 3.5' in pred_play:
                is_correct = (home_score + away_score < 4)
            elif 'Over 2.5' in pred_play:
                is_correct = (home_score + away_score > 2)
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
                'is_correct': is_correct
            })
            print(f"   {'✅' if is_correct else '❌'} {pred_match[:50]} → {home_score}-{away_score}")
        else:
            print(f"   ⚠️ NOT FOUND: {pred_match[:50]}")
    
    print(f"\n📊 Matched: {matched}/{len(predictions)}")
    return validated


def generate_report(validated):
    """Generate performance report"""
    
    total = len(validated)
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    bp_stats = {}
    for v in validated:
        bp = v['blueprint']
        if bp not in bp_stats:
            bp_stats[bp] = {'total': 0, 'correct': 0}
        bp_stats[bp]['total'] += 1
        if v['is_correct']:
            bp_stats[bp]['correct'] += 1
    
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
    
    return report


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
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


def main():
    print("\n" + "="*60)
    print("⚽ VALIDATION SYSTEM")
    print("="*60)
    
    if not os.path.exists("predictions.json"):
        print("❌ No predictions.json found")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    validation_results = parse_validation_file("validation_results.txt")
    
    if not validation_results:
        print("❌ No validation results found")
        return 1
    
    print("\n🔍 Comparing predictions...")
    validated = validate_predictions(predictions, validation_results)
    
    if validated:
        report = generate_report(validated)
        send_telegram(report)
        
        with open("validation_report.md", "w") as f:
            f.write(report)
        
        total = len(validated)
        correct = sum(1 for v in validated if v['is_correct'])
        print(f"\n📊 RESULTS: {correct}/{total} ({correct/total*100:.1f}%)")
    else:
        print("\n❌ No matches could be validated")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
