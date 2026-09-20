"""
ACCUMULATOR VALIDATION - Track performance of 2,4,7,10 odds accumulators
"""

import os
import json
import re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def load_validation_results():
    """Load actual results from results.txt"""
    if not os.path.exists("results.txt"):
        return {}
    
    results = {}
    with open("results.txt", 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if ' vs ' in line and 'RESULT:' not in line:
            match_name = line
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


def validate_prediction(play, actual):
    """Check if a prediction was correct"""
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    
    if 'Home Win' in play:
        return home > away
    elif 'Draw' in play:
        return home == away
    elif 'Both Teams to Score' in play:
        return home > 0 and away > 0
    elif 'Over 1.5' in play:
        return total > 1
    elif 'Under 3.5' in play:
        return total < 4
    elif 'Over 2.5' in play:
        return total > 2
    elif 'Draw or Under 2.5' in play:
        return (home == away) or total < 3
    elif 'Draw or GG' in play:
        return (home == away) or (home > 0 and away > 0)
    return False


def validate_accumulator(acc_matches, validation_results):
    """Validate all legs of an accumulator"""
    results = []
    all_correct = True
    
    for match in acc_matches:
        match_name = match.get('match', '')
        play = match.get('play', '')
        
        actual = None
        for key in validation_results:
            if match_name.lower() in key.lower() or key.lower() in match_name.lower():
                actual = validation_results[key]
                break
        
        if actual:
            is_correct = validate_prediction(play, actual)
            results.append({
                'match': match_name,
                'play': play,
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'correct': is_correct
            })
            if not is_correct:
                all_correct = False
        else:
            results.append({
                'match': match_name,
                'play': play,
                'actual_score': 'NOT FOUND',
                'correct': False
            })
            all_correct = False
    
    return results, all_correct


def main():
    print("\n" + "="*60)
    print("⚽ ACCUMULATOR VALIDATION")
    print("="*60)
    
    # Load predictions
    if not os.path.exists("predictions.json"):
        print("❌ No predictions.json found")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    # Load validation results
    validation_results = load_validation_results()
    
    if not validation_results:
        print("❌ No results.txt found")
        print("\n📝 Create results.txt with:")
        print("   Match Name")
        print("   League")
        print("   Odds line")
        print("   RESULT: 2-1 | Home Win")
        return 1
    
    print(f"✅ Loaded {len(predictions)} predictions")
    print(f"✅ Loaded {len(validation_results)} validation results")
    
    # This would need accumulator data from main.py
    # For now, print instructions
    print("\n📊 To validate accumulators:")
    print("   1. The accumulator picks are in your Telegram message")
    print("   2. Compare each leg with actual results in results.txt")
    print("   3. Track which accumulators won")
    
    print("\n✅ Accumulator validation ready")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
