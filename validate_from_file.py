"""
VALIDATION SYSTEM - Manual File Mode
Improved matching to handle different formats
"""

import os
import sys
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def normalize_match_name(match_name):
    """Remove special characters and normalize match names for comparison"""
    # Remove ** and other markdown
    name = match_name.replace('**', '').replace('*', '').strip()
    # Convert to lowercase
    name = name.lower()
    return name


def parse_validation_file(filepath="validation_results.txt"):
    """Parse validation file with results"""
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return {}
    
    results = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Look for RESULT: pattern
            if 'RESULT:' in line:
                parts = line.split('RESULT:')
                match_part = parts[0].strip()
                result_part = parts[1].strip() if len(parts) > 1 else ''
                
                # Normalize match name
                match_name = normalize_match_name(match_part)
                
                # Parse score from result part
                score_match = re.search(r'(\d+)-(\d+)', result_part)
                if score_match:
                    home_score = int(score_match.group(1))
                    away_score = int(score_match.group(2))
                    
                    results[match_name] = {
                        'home_score': home_score,
                        'away_score': away_score,
                        'original_match': match_part
                    }
    
    print(f"✅ Loaded {len(results)} validation results")
    return results


def validate_predictions(predictions, validation_results):
    """Compare predictions with actual results - improved matching"""
    
    validated = []
    matched = 0
    not_found = []
    
    for pred in predictions:
        pred_match = pred.get('match', '')
        pred_match_norm = normalize_match_name(pred_match)
        pred_play = pred.get('play', '')
        pred_confidence = pred.get('confidence', 0)
        pred_blueprint = pred.get('blueprint', '')
        
        # Try exact match first
        actual = validation_results.get(pred_match_norm)
        
        # If not found, try partial match
        if not actual:
            for key, value in validation_results.items():
                if pred_match_norm in key or key in pred_match_norm:
                    actual = value
                    break
        
        if actual:
            matched += 1
            home_score = actual['home_score']
            away_score = actual['away_score']
            
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
                'actual_result': actual.get('original_match', ''),
                'is_correct': is_correct
            })
            status = "✅" if is_correct else "❌"
            print(f"   {status} {pred_match[:50]} → {home_score}-{away_score}")
        else:
            not_found.append(pred_match)
            print(f"   ⚠️ NOT FOUND: {pred_match[:50]}")
    
    print(f"\n📊 MATCH SUMMARY:")
    print(f"   Matched: {matched}/{len(predictions)}")
    print(f"   Not found: {len(not_found)}")
    
    return validated


def generate_report(validated):
    """Generate performance report"""
    
    total = len(validated)
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Group by blueprint
    bp_stats = {}
    for v in validated:
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


def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured - skipping")
        return False
    
    if len(message) > 4096:
        message = message[:4000] + "\n\n... (truncated)"
    
    import requests
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
        print("   Canberra Olympic vs O'Connor Knights RESULT: 2-1 | Home Win")
        print("   Anyang vs Gimcheon Sangmu RESULT: 1-1 | Draw")
        print("")
        return 1
    
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
