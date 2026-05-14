"""
VALIDATION SYSTEM - Updated with Match Name Normalization
Reads results from validation_results.txt and matches with predictions
"""

import os
import sys
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def normalize_match_name(name):
    """Remove special characters and normalize match names for comparison"""
    # Remove **, *, and other markdown symbols
    name = name.replace('**', '').replace('*', '').strip()
    # Convert to lowercase for case-insensitive matching
    name = name.lower()
    # Remove extra spaces
    name = ' '.join(name.split())
    return name


def parse_validation_file(filepath="validation_results.txt"):
    """Parse multi-line validation file with normalized match names"""
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return {}
    
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f.readlines()]
    
    results = {}
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Find match name (must contain 'vs' and not be a RESULT line)
        if ' vs ' in line and 'RESULT:' not in line:
            match_name = normalize_match_name(line)
            i += 1
            
            # Skip league line and odds lines until RESULT
            while i < len(lines) and 'RESULT:' not in lines[i]:
                i += 1
            
            # Parse RESULT line
            if i < len(lines) and 'RESULT:' in lines[i]:
                result_line = lines[i]
                # Extract score (e.g., "3-0" from "RESULT: 3-0 | Home Win")
                score_match = re.search(r'(\d+)-(\d+)', result_line)
                if score_match:
                    home_score = int(score_match.group(1))
                    away_score = int(score_match.group(2))
                    results[match_name] = {
                        'home_score': home_score,
                        'away_score': away_score,
                        'raw_result': result_line
                    }
        i += 1
    
    print(f"✅ Loaded {len(results)} validation results")
    return results


def validate_predictions(predictions, validation_results):
    """Compare predictions with actual results using normalized names"""
    
    validated = []
    matched = 0
    not_found = []
    
    for pred in predictions:
        pred_match_raw = pred.get('match', '')
        pred_match = normalize_match_name(pred_match_raw)
        pred_play = pred.get('play', '')
        pred_confidence = pred.get('confidence', 0)
        pred_blueprint = pred.get('blueprint', '')
        
        # Try exact match first
        actual = validation_results.get(pred_match)
        
        # Try partial match if not found
        if not actual:
            for key in validation_results:
                if pred_match in key or key in pred_match:
                    actual = validation_results[key]
                    break
        
        if actual:
            matched += 1
            home_score = actual['home_score']
            away_score = actual['away_score']
            total_goals = home_score + away_score
            
            # Determine if prediction was correct
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
                is_correct = (total_goals > 1)
            elif 'Under 3.5' in pred_play:
                is_correct = (total_goals < 4)
            elif 'Over 2.5' in pred_play:
                is_correct = (total_goals > 2)
            elif 'Draw or GG' in pred_play:
                is_correct = (home_score == away_score) or (home_score > 0 and away_score > 0)
            elif 'Draw or Under 2.5' in pred_play:
                is_correct = (home_score == away_score) or (total_goals < 3)
            elif '1X & Over 1.5' in pred_play:
                is_correct = (home_score >= away_score) and (total_goals > 1)
            elif '1X & Under 3.5' in pred_play:
                is_correct = (home_score >= away_score) and (total_goals < 4)
            
            validated.append({
                'match': pred_match_raw,
                'blueprint': pred_blueprint,
                'predicted_play': pred_play,
                'confidence': pred_confidence,
                'actual_score': f"{home_score}-{away_score}",
                'is_correct': is_correct
            })
            
            status = "✅" if is_correct else "❌"
            print(f"   {status} {pred_match_raw[:50]} → {home_score}-{away_score}")
        else:
            not_found.append(pred_match_raw)
            # Only print first 10 not found to avoid clutter
            if len(not_found) <= 10:
                print(f"   ⚠️ NOT FOUND: {pred_match_raw[:50]}")
    
    if len(not_found) > 10:
        print(f"   ... and {len(not_found) - 10} more not found")
    
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
    
    return report


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


def main():
    print("\n" + "="*60)
    print("⚽ VALIDATION SYSTEM - Updated")
    print("Normalized match name matching")
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
        print("\n📝 Expected format:")
        print("   Manchester City vs Crystal Palace")
        print("   Premier League")
        print("   1.32 | 6.13 | 9.14")
        print("   RESULT: 3-0 | Home Win")
        return 1
    
    print(f"✅ Loaded {len(validation_results)} validation results")
    
    # Validate
    print("\n🔍 Comparing predictions with results...")
    validated = validate_predictions(predictions, validation_results)
    
    if validated:
        # Generate report
        report = generate_report(validated)
        
        # Calculate stats
        total = len(validated)
        correct = sum(1 for v in validated if v['is_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
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
        print(f"✅ Report sent to Telegram")
    else:
        print("\n❌ No matches could be validated")
        print("\n💡 Tip: Make sure match names in validation_results.txt")
        print("   match the names in predictions.json")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
