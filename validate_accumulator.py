cat > validate_accumulator.py << 'EOF'
"""
Validate Accumulator Results
Compares accumulator picks with actual results
Updates blueprint performance for dynamic learning
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
# FUNCTION: Load accumulator picks from predictions.json
# ============================================================

def load_accumulator_picks(predictions_file="predictions.json"):
    """Load accumulator picks from predictions.json"""
    
    if not os.path.exists(predictions_file):
        print(f"❌ {predictions_file} not found")
        return None
    
    with open(predictions_file, 'r') as f:
        predictions = json.load(f)
    
    # Check if predictions have accumulator info
    # In your system, accumulators are built in main.py output
    return predictions

# ============================================================
# FUNCTION: Parse validation results
# ============================================================

def parse_validation_results(results_file="validation_results.txt"):
    """Parse validation results file"""
    
    if not os.path.exists(results_file):
        print(f"❌ {results_file} not found")
        return {}
    
    results = {}
    
    with open(results_file, 'r') as f:
        content = f.read()
    
    # Find all RESULT lines
    pattern = r'([A-Za-z\s]+)\s+RESULT:\s*(\d+)-(\d+)\s*\|\s*([^\n]+)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        match_name = match[0].strip()
        home_score = int(match[1])
        away_score = int(match[2])
        outcome = match[3].strip()
        
        results[match_name] = {
            'home_score': home_score,
            'away_score': away_score,
            'outcome': outcome
        }
    
    print(f"✅ Loaded {len(results)} validation results")
    return results

# ============================================================
# FUNCTION: Validate a single prediction
# ============================================================

def validate_prediction(prediction, actual_result):
    """Check if prediction was correct"""
    
    predicted_play = prediction.get('play', '')
    home_score = actual_result['home_score']
    away_score = actual_result['away_score']
    total_goals = home_score + away_score
    
    is_correct = False
    
    # Home Win predictions
    if 'Straight Home Win' in predicted_play or 'Home Win' in predicted_play:
        is_correct = (home_score > away_score)
    
    # Draw predictions
    elif 'Full Time Draw' in predicted_play or 'Draw/Draw' in predicted_play:
        is_correct = (home_score == away_score)
    
    # Draw & Under 2.5
    elif 'Draw & Under 2.5' in predicted_play:
        is_correct = (home_score == away_score and total_goals < 3)
    
    # Over 1.5 Goals
    elif 'Over 1.5 Goals' in predicted_play:
        is_correct = (total_goals > 1)
    
    # Over 2.5 Goals
    elif 'Over 2.5 Goals' in predicted_play:
        is_correct = (total_goals > 2)
    
    # Under 3.5 FT
    elif 'Under 3.5 FT' in predicted_play:
        is_correct = (total_goals < 4)
    
    # BTTS predictions
    elif 'Both Teams to Score - YES' in predicted_play:
        is_correct = (home_score > 0 and away_score > 0)
    
    elif 'Both Teams to Score - NO' in predicted_play:
        is_correct = (home_score == 0 or away_score == 0)
    
    # 1X & Over 1.5
    elif '1X & Over 1.5' in predicted_play:
        home_not_lost = (home_score >= away_score)
        is_correct = home_not_lost and total_goals > 1
    
    # 1X & Under 3.5
    elif '1X & Under 3.5' in predicted_play:
        home_not_lost = (home_score >= away_score)
        is_correct = home_not_lost and total_goals < 4
    
    # Draw/Draw (Half Time Draw + Full Time Draw)
    elif 'Draw/Draw' in predicted_play:
        # This requires half-time data - assume full time draw for now
        is_correct = (home_score == away_score)
    
    return is_correct

# ============================================================
# FUNCTION: Validate all accumulator picks
# ============================================================

def validate_accumulator_picks(predictions, actual_results):
    """Validate all picks and return statistics"""
    
    validated = []
    bp_stats = {}
    
    for pred in predictions:
        match_name = pred.get('match', '')
        bp = pred.get('blueprint', 'Unknown')
        play = pred.get('play', '')
        confidence = pred.get('confidence', 0)
        
        # Find matching result
        actual = None
        for result_match in actual_results:
            if match_name.lower() in result_match.lower() or result_match.lower() in match_name.lower():
                actual = actual_results[result_match]
                break
        
        if actual:
            is_correct = validate_prediction(pred, actual)
            
            validated.append({
                'match': match_name,
                'blueprint': bp,
                'predicted_play': play,
                'confidence': confidence,
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'is_correct': is_correct
            })
            
            # Update blueprint statistics
            if bp not in bp_stats:
                bp_stats[bp] = {'total': 0, 'correct': 0}
            bp_stats[bp]['total'] += 1
            if is_correct:
                bp_stats[bp]['correct'] += 1
            
            status = "✅" if is_correct else "❌"
            print(f"   {status} {bp}: {match_name[:40]} → {actual['home_score']}-{actual['away_score']}")
        else:
            print(f"   ⚠️ Not found: {match_name}")
    
    return validated, bp_stats

# ============================================================
# FUNCTION: Update blueprint performance file
# ============================================================

def update_blueprint_performance(bp_stats):
    """Save updated blueprint performance for dynamic learning"""
    
    # Load existing performance if any
    perf_file = "blueprint_performance.json"
    existing = {}
    
    if os.path.exists(perf_file):
        with open(perf_file, 'r') as f:
            existing = json.load(f)
    
    # Update with new stats
    for bp, stats in bp_stats.items():
        if bp not in existing:
            existing[bp] = {'total': 0, 'correct': 0}
        existing[bp]['total'] += stats['total']
        existing[bp]['correct'] += stats['correct']
    
    # Calculate success rates
    for bp in existing:
        if existing[bp]['total'] > 0:
            existing[bp]['success_rate'] = existing[bp]['correct'] / existing[bp]['total']
    
    # Save
    with open(perf_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"\n✅ Updated blueprint performance in {perf_file}")
    
    # Display current rates
    print("\n📊 CURRENT BLUEPRINT SUCCESS RATES:")
    for bp, stats in sorted(existing.items()):
        rate = stats.get('success_rate', 0) * 100
        print(f"   {bp}: {stats['correct']}/{stats['total']} ({rate:.1f}%)")

# ============================================================
# FUNCTION: Generate accumulator report
# ============================================================

def generate_accumulator_report(validated, bp_stats):
    """Generate performance report for accumulators"""
    
    total = len(validated)
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    report = f"""⚽ ACCUMULATOR VALIDATION REPORT
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OVERALL ACCURACY: {accuracy:.1f}% ({correct}/{total})

📊 BLUEPRINT PERFORMANCE:
"""
    
    for bp, stats in bp_stats.items():
        bp_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        report += f"   {bp}: {stats['correct']}/{stats['total']} ({bp_acc:.1f}%)\n"
    
    report += "\n📝 DETAILED RESULTS:\n"
    for v in validated[:20]:
        status = "✅" if v['is_correct'] else "❌"
        report += f"{status} {v['blueprint']}: {v['match'][:35]} → {v['actual_score']}\n"
    
    return report

# ============================================================
# FUNCTION: Send to Telegram
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
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

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ ACCUMULATOR VALIDATION SYSTEM")
    print("Validates picks against actual results")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load predictions
    predictions = load_accumulator_picks("predictions.json")
    
    if not predictions:
        print("❌ No predictions found. Run main.py first.")
        return 1
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Load validation results
    actual_results = parse_validation_results("validation_results.txt")
    
    if not actual_results:
        print("\n❌ No validation_results.txt found!")
        print("\n📝 Please create validation_results.txt with format:")
        print("   Brighton vs Wolves RESULT: 3-0 | Home Win")
        return 1
    
    # Validate picks
    print("\n🔍 Validating predictions against results...")
    validated, bp_stats = validate_accumulator_picks(predictions, actual_results)
    
    # Update blueprint performance
    update_blueprint_performance(bp_stats)
    
    # Generate report
    report = generate_accumulator_report(validated, bp_stats)
    
    # Display summary
    total = len(validated)
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Total validated: {total}")
    print(f"   Correct: {correct}")
    print(f"   Wrong: {total - correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    # Send to Telegram
    send_telegram(report)
    
    # Save report
    with open("accumulator_validation_report.md", "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to accumulator_validation_report.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF
