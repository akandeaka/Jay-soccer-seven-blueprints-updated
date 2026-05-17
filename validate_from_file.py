"""
VALIDATION SYSTEM - Validates Both Predictions AND Accumulators
Shows actual results for each accumulator leg
"""

import os
import sys
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def clean_match_name(name):
    name = name.replace('**', '').replace('*', '').strip()
    return name.lower()


def parse_validation_file(filepath="validation_results.txt"):
    """Parse validation results file"""
    if not os.path.exists(filepath):
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
    
    return results


def check_prediction(play, actual):
    """Check if a prediction was correct"""
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    
    if 'Home Win' in play or 'Straight Home Win' in play:
        return home > away
    elif 'Full Time Draw' in play:
        return home == away
    elif 'Both Teams to Score - YES' in play:
        return home > 0 and away > 0
    elif 'Both Teams to Score - NO' in play:
        return home == 0 or away == 0
    elif 'Over 1.5' in play:
        return total > 1
    elif 'Under 3.5' in play:
        return total < 4
    elif 'Over 2.5' in play:
        return total > 2
    elif '1X & Over 1.5' in play:
        return (home >= away) and total > 1
    elif '1X & Under 3.5' in play:
        return (home >= away) and total < 4
    elif 'Draw or Under 2.5' in play:
        return (home == away) or total < 3
    elif 'Draw or GG' in play:
        return (home == away) or (home > 0 and away > 0)
    return False


def get_short_play(play):
    """Convert play to short format"""
    if '1X & Over 1.5' in play:
        return '1X & O1.5'
    elif '1X & Under 3.5' in play:
        return '1X & U3.5'
    elif 'Over 1.5' in play:
        return 'O1.5'
    elif 'Under 3.5' in play:
        return 'U3.5'
    elif 'Both Teams to Score - YES' in play:
        return 'BTTS YES'
    elif 'Both Teams to Score - NO' in play:
        return 'BTTS NO'
    elif 'Draw or Under 2.5' in play:
        return 'Draw/U2.5'
    elif 'Draw or GG' in play:
        return 'Draw/GG'
    elif 'Home Win' in play:
        return 'Home Win'
    return play[:15]


def validate_accumulator_legs(accumulators, validation_results):
    """Validate each accumulator leg and return results"""
    acc_results = {}
    
    for acc_name, acc_data in accumulators.items():
        legs = []
        all_correct = True
        
        for match in acc_data.get('matches', []):
            match_name = clean_match_name(match.get('match', ''))
            play = match.get('play', '')
            
            actual = None
            for key in validation_results:
                if match_name in key or key in match_name:
                    actual = validation_results[key]
                    break
            
            if actual:
                is_correct = check_prediction(play, actual)
                legs.append({
                    'match': match.get('match', ''),
                    'play': play,
                    'short_play': get_short_play(play),
                    'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                    'correct': is_correct
                })
                if not is_correct:
                    all_correct = False
            else:
                legs.append({
                    'match': match.get('match', ''),
                    'play': play,
                    'short_play': get_short_play(play),
                    'actual_score': 'NOT FOUND',
                    'correct': False
                })
                all_correct = False
        
        acc_results[acc_name] = {
            'odds': acc_data.get('odds', 0),
            'legs': legs,
            'all_correct': all_correct,
            'correct_count': sum(1 for l in legs if l['correct']),
            'total_count': len(legs)
        }
    
    return acc_results


def load_accumulators():
    """Load accumulators from accumulators.json"""
    if not os.path.exists("accumulators.json"):
        return {}
    
    with open("accumulators.json", 'r') as f:
        return json.load(f)


def main():
    print("\n" + "="*60)
    print("⚽ VALIDATION - PREDICTIONS & ACCUMULATORS")
    print("="*60)
    
    # Load predictions
    if not os.path.exists("predictions.json"):
        print("❌ No predictions.json found")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    # Load validation results
    validation_results = parse_validation_file("validation_results.txt")
    
    if not validation_results:
        print("❌ No validation_results.txt found")
        return 1
    
    # Load accumulators
    accumulators = load_accumulators()
    
    # Validate top 30 predictions
    sorted_preds = sorted(predictions, key=lambda x: x.get('confidence', 0), reverse=True)
    top_30 = sorted_preds[:30]
    
    validated_preds = []
    for pred in top_30:
        match_name = clean_match_name(pred.get('match', ''))
        play = pred.get('play', '')
        
        actual = None
        for key in validation_results:
            if match_name in key or key in match_name:
                actual = validation_results[key]
                break
        
        if actual:
            is_correct = check_prediction(play, actual)
            validated_preds.append({
                'match': pred.get('match', ''),
                'play': play,
                'short_play': get_short_play(play),
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'correct': is_correct
            })
    
    # Validate accumulators
    acc_validation = validate_accumulator_legs(accumulators, validation_results)
    
    # Build report
    report = f"""🏁 *SETTLEMENT REPORT*
📅 {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *TOP 30 PREDICTIONS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for v in validated_preds:
        status = "✅" if v['correct'] else "❌"
        report += f"\n{status} *{v['match'][:45]}*\n"
        report += f"   🎯 {v['short_play']}\n"
        report += f"   🏁 Score: {v['actual_score']}\n"
    
    if acc_validation:
        report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 *ACCUMULATOR RESULTS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for acc_name, acc_data in acc_validation.items():
            total_correct = acc_data['correct_count']
            total_legs = acc_data['total_count']
            status = "✅ WON" if acc_data['all_correct'] else "❌ LOST"
            report += f"\n*{acc_name}* | Odds: {acc_data['odds']} | {status} ({total_correct}/{total_legs})\n"
            
            for leg in acc_data['legs']:
                leg_status = "✅" if leg['correct'] else "❌"
                report += f"\n   {leg_status} *{leg['match'][:40]}*\n"
                report += f"      🎯 {leg['short_play']}\n"
                report += f"      🏁 Score: {leg['actual_score']}\n"
    
    # Summary
    correct_preds = sum(1 for v in validated_preds if v['correct'])
    total_preds = len(validated_preds)
    pred_accuracy = (correct_preds / total_preds * 100) if total_preds > 0 else 0
    
    report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 *SUMMARY*\n"
    report += f"✅ Predictions: {correct_preds}/{total_preds} ({pred_accuracy:.1f}%)\n"
    
    for acc_name, acc_data in acc_validation.items():
        if acc_data['all_correct']:
            report += f"✅ {acc_name}: WON @ {acc_data['odds']}\n"
        else:
            report += f"❌ {acc_name}: LOST ({acc_data['correct_count']}/{acc_data['total_count']})\n"
    
    # Print to console
    print("\n" + report)
    
    # Send to Telegram
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            r = requests.post(url, json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': report,
                'parse_mode': 'Markdown'
            }, timeout=30)
            print("\n✅ Report sent to Telegram")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
