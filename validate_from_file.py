"""
VALIDATION SYSTEM - Validates Blueprint Predictions & Accumulators
"""

import os
import sys
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def clean_match_name(name):
    """Clean match name for comparison"""
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
                score_match = re.search(r'(\d+)-(\d+)', lines[i])
                if score_match:
                    results[match_name] = {
                        'home_score': int(score_match.group(1)),
                        'away_score': int(score_match.group(2))
                    }
        i += 1
    
    print(f"✅ Loaded {len(results)} validation results")
    return results


def check_prediction(play, actual):
    """Check if a prediction was correct"""
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    
    if 'Straight Home Win' in play or 'Home Win' in play:
        return home > away
    elif 'Full Time Draw' in play or 'Draw' in play and 'GG' not in play:
        return home == away
    elif 'Both Teams to Score - YES' in play:
        return home > 0 and away > 0
    elif 'Both Teams to Score - NO' in play:
        return home == 0 or away == 0
    elif 'Over 1.5 Goals' in play:
        return total > 1
    elif 'Under 3.5 FT' in play or '1X & Under 3.5 FT' in play:
        return total < 4
    elif 'Over 2.5 Goals' in play:
        return total > 2
    elif '1X & Over 1.5 Goals' in play:
        return (home >= away) and total > 1
    elif 'Draw or Under 2.5 Goals' in play:
        return (home == away) or total < 3
    elif 'Draw or GG' in play:
        return (home == away) or (home > 0 and away > 0)
    return False


def validate_blueprint_predictions(predictions, validation_results):
    """Validate all blueprint predictions"""
    validated = []
    bp_stats = {}
    
    for pred in predictions:
        match_name = clean_match_name(pred.get('match', ''))
        play = pred.get('play', '')
        blueprint = pred.get('blueprint', '')
        confidence = pred.get('confidence', 0)
        
        actual = validation_results.get(match_name)
        
        if not actual:
            for key in validation_results:
                if match_name in key or key in match_name:
                    actual = validation_results[key]
                    break
        
        if actual:
            is_correct = check_prediction(play, actual)
            validated.append({
                'match': pred.get('match', ''),
                'blueprint': blueprint,
                'play': play,
                'confidence': confidence,
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'is_correct': is_correct
            })
            
            if blueprint not in bp_stats:
                bp_stats[blueprint] = {'total': 0, 'correct': 0}
            bp_stats[blueprint]['total'] += 1
            if is_correct:
                bp_stats[blueprint]['correct'] += 1
    
    return validated, bp_stats


def validate_accumulators(accumulators, validation_results):
    """Validate accumulator performance"""
    acc_results = {}
    
    for acc_name, acc_data in accumulators.items():
        matches = acc_data.get('matches', [])
        total_legs = len(matches)
        correct_legs = 0
        leg_details = []
        
        for match in matches:
            match_name = clean_match_name(match.get('match', ''))
            play = match.get('play', '')
            
            actual = None
            for key in validation_results:
                if match_name in key or key in match_name:
                    actual = validation_results[key]
                    break
            
            if actual:
                is_correct = check_prediction(play, actual)
                if is_correct:
                    correct_legs += 1
                leg_details.append({
                    'match': match.get('match', ''),
                    'play': play,
                    'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                    'correct': is_correct
                })
            else:
                leg_details.append({
                    'match': match.get('match', ''),
                    'play': play,
                    'actual_score': 'NOT FOUND',
                    'correct': False
                })
        
        # Accumulator wins ONLY if ALL legs are correct
        accumulator_won = (correct_legs == total_legs)
        
        acc_results[acc_name] = {
            'total_legs': total_legs,
            'correct_legs': correct_legs,
            'accumulator_won': accumulator_won,
            'odds': acc_data.get('odds', 0),
            'leg_details': leg_details
        }
    
    return acc_results


def generate_report(validated, bp_stats, acc_results):
    """Generate complete performance report"""
    
    # Blueprint statistics
    total = len(validated)
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    report = f"""⚽ JAY SOCCER BLUEPRINTS - PERFORMANCE REPORT
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 BLUEPRINT PREDICTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Total Predictions: {total}
   Correct: {correct}
   Wrong: {total - correct}
   Overall Accuracy: {accuracy:.1f}%

📊 BY BLUEPRINT:
"""
    
    for bp in ['BP1', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7', 'BP8']:
        if bp in bp_stats:
            stats = bp_stats[bp]
            bp_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            bar = "█" * int(bp_acc / 10) + "░" * (10 - int(bp_acc / 10))
            report += f"\n   {bp}: {stats['correct']}/{stats['total']} ({bp_acc:.1f}%) {bar}"
        else:
            report += f"\n   {bp}: 0/0 (N/A) {'░' * 10}"
    
    # Accumulator Performance
    if acc_results:
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎰 ACCUMULATOR PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for acc_name, acc_data in acc_results.items():
            status = "✅ WON" if acc_data['accumulator_won'] else "❌ LOST"
            report += f"""
{acc_name} | Odds: {acc_data['odds']} | {status}
   Legs: {acc_data['correct_legs']}/{acc_data['total_legs']} correct
"""
            for leg in acc_data['leg_details']:
                leg_status = "✅" if leg['correct'] else "❌"
                report += f"   {leg_status} {leg['match'][:40]}\n"
                report += f"      🎯 {leg['play']} | Actual: {leg['actual_score']}\n"
    
    return report


def load_accumulators():
    """Load accumulator data from predictions.json or separate file"""
    # For now, return empty - accumulators would be saved separately
    # This function can be expanded to read accumulator data from main.py output
    return {}


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
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
    print("⚽ VALIDATION SYSTEM - Blueprints & Accumulators")
    print("="*60)
    
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
        print("\n📝 Create validation_results.txt with:")
        print("   Manchester City vs Crystal Palace")
        print("   Premier League")
        print("   1.22 | 7.50 | 10.00")
        print("   RESULT: 3-0 | Home Win")
        return 1
    
    # Validate blueprint predictions
    validated, bp_stats = validate_blueprint_predictions(predictions, validation_results)
    
    # Load and validate accumulators (if available)
    accumulators = load_accumulators()
    acc_results = validate_accumulators(accumulators, validation_results) if accumulators else {}
    
    # Generate report
    report = generate_report(validated, bp_stats, acc_results)
    
    # Print to console
    print("\n" + report)
    
    # Send to Telegram
    send_telegram(report)
    
    # Save report
    with open("performance_report.md", "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to performance_report.md")
    print(f"✅ Report sent to Telegram")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
