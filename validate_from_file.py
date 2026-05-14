"""
VALIDATION SYSTEM - Clean Report Format
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
    name = ' '.join(name.split())
    return name.lower()


def parse_validation_file(filepath="validation_results.txt"):
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
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    
    if 'Home Win' in play or 'Straight Home Win' in play:
        return home > away
    elif 'Full Time Draw' in play or (play == 'Draw' and 'GG' not in play):
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
    elif 'Draw or Under 2.5 Goals' in play:
        return (home == away) or total < 3
    elif 'Draw or GG' in play:
        return (home == away) or (home > 0 and away > 0)
    return False


def get_prediction_short_name(play):
    """Convert full play name to short readable format"""
    if 'Over 1.5 Goals' in play:
        return 'Over 1.5 Goals'
    elif 'Under 3.5 FT' in play or '1X & Under 3.5 FT' in play:
        return 'Under 3.5 Goals'
    elif 'Over 2.5 Goals' in play:
        return 'Over 2.5 Goals'
    elif 'Straight Home Win' in play or 'Home Win' in play:
        return 'Home Win'
    elif 'Full Time Draw' in play:
        return 'Draw'
    elif 'Draw or Under 2.5 Goals' in play:
        return 'Draw or Under 2.5'
    elif 'Both Teams to Score - YES' in play:
        return 'BTTS - YES'
    elif 'Both Teams to Score - NO' in play:
        return 'BTTS - NO'
    return play[:20]


def get_odd_from_prediction(pred):
    """Extract odds from prediction"""
    if 'Home Win' in pred.get('play', ''):
        return pred.get('home_odds', 0)
    elif 'Draw' in pred.get('play', ''):
        return pred.get('draw_odds', 0)
    return 0


def main():
    print("\n" + "="*60)
    print("⚽ VALIDATION SYSTEM - CLEAN REPORT")
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
    
    # Validate each prediction
    results = []
    for pred in predictions:
        match_name = clean_match_name(pred.get('match', ''))
        play = pred.get('play', '')
        
        actual = None
        for key in validation_results:
            if match_name in key or key in match_name:
                actual = validation_results[key]
                break
        
        if actual:
            is_correct = check_prediction(play, actual)
            results.append({
                'match': pred.get('match', ''),
                'play': play,
                'odds': get_odd_from_prediction(pred),
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'correct': is_correct
            })
    
    if not results:
        print("❌ No matches validated")
        return 1
    
    # Calculate statistics
    correct = sum(1 for r in results if r['correct'])
    total = len(results)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Build clean report
    report = f"""🏁 *YESTERDAY'S SETTLEMENT REPORT*
📅 Date: {(datetime.now() - __import__('datetime').timedelta(days=1)).strftime('%Y-%m-%d')}
───────────────────

"""
    
    for r in results:
        status = "✅" if r['correct'] else "❌"
        odd_text = f" @ {r['odds']}" if r['odds'] > 0 else ""
        report += f"""{status} *{r['match'][:50]}*
🔹 Bet: {get_prediction_short_name(r['play'])}{odd_text}
🏁 Score: {r['actual_score']}

"""
    
    report += f"""───────────────────
📊 *SUMMARY*
✅ Wins: {correct}
❌ Losses: {total - correct}
📈 Accuracy: {accuracy:.1f}%"""
    
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
    
    # Save report
    with open("settlement_report.md", "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to settlement_report.md")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
