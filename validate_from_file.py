"""
VALIDATION SYSTEM - Compare predictions with actual results
"""

import os
import sys
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def clean_match_name(name):
    """Remove special characters for matching"""
    name = name.replace('**', '').replace('*', '').strip()
    name = ' '.join(name.split())
    return name.lower()


def parse_validation_file(filepath="validation_results.txt"):
    """Parse validation results file"""
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return {}
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    results = {}
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if ' vs ' in line and 'RESULT:' not in line:
            match_name = clean_match_name(line)
            i += 1
            
            while i < len(lines) and 'RESULT:' not in lines[i]:
                i += 1
            
            if i < len(lines) and 'RESULT:' in lines[i]:
                result_line = lines[i]
                score_match = re.search(r'(\d+)-(\d+)', result_line)
                if score_match:
                    results[match_name] = {
                        'home_score': int(score_match.group(1)),
                        'away_score': int(score_match.group(2))
                    }
        i += 1
    
    print(f"✅ Loaded {len(results)} validation results")
    return results


def validate_predictions(predictions, validation_results):
    """Compare predictions with actual results"""
    
    validated = []
    matched = 0
    
    for pred in predictions:
        pred_match = clean_match_name(pred.get('match', ''))
        pred_play = pred.get('play', '')
        pred_blueprint = pred.get('blueprint', '')
        pred_confidence = pred.get('confidence', 0)
        
        actual = validation_results.get(pred_match)
        
        if actual:
            matched += 1
            home = actual['home_score']
            away = actual['away_score']
            total = home + away
            
            # Determine if correct
            is_correct = False
            
            if 'Home Win' in pred_play:
                is_correct = (home > away)
            elif 'Draw' in pred_play:
                is_correct = (home == away)
            elif 'Both Teams to Score' in pred_play:
                is_correct = (home > 0 and away > 0) if 'YES' in pred_play else (home == 0 or away == 0)
            elif 'Over 1.5' in pred_play:
                is_correct = (total > 1)
            elif 'Under 3.5' in pred_play:
                is_correct = (total < 4)
            elif 'Over 2.5' in pred_play:
                is_correct = (total > 2)
            elif 'Draw or GG' in pred_play:
                is_correct = (home == away) or (home > 0 and away > 0)
            elif 'Draw or Under 2.5' in pred_play:
                is_correct = (home == away) or (total < 3)
            
            validated.append({
                'match': pred['match'],
                'blueprint': pred_blueprint,
                'predicted_play': pred_play,
                'confidence': pred_confidence,
                'actual_score': f"{home}-{away}",
                'is_correct': is_correct
            })
            
            status = "✅" if is_correct else "❌"
            print(f"   {status} {pred['match'][:50]} → {home}-{away}")
        else:
            if matched < 5:
                print(f"   ⚠️ NOT FOUND: {pred['match'][:50]}")
    
    print(f"\n📊 Matched: {matched}/{len(predictions)}")
    return validated


def generate_report(validated):
    total = len(validated)
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    bp_stats = {}
    for v in validated:
        bp = v['blueprint']
        bp_stats.setdefault(bp, {'total': 0, 'correct': 0})
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
        print("❌ No predictions.json found. Run main.py first.")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    validation_results = parse_validation_file("validation_results.txt")
    
    if not validation_results:
        print("❌ No validation_results.txt found")
        return 1
    
    print("\n🔍 Validating predictions...")
    validated = validate_predictions(predictions, validation_results)
    
    if validated:
        report = generate_report(validated)
        send_telegram(report)
        
        with open("validation_report.md", "w") as f:
            f.write(report)
        
        total = len(validated)
        correct = sum(1 for v in validated if v['is_correct'])
        print(f"\n📊 ACCURACY: {correct}/{total} ({correct/total*100:.1f}%)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
