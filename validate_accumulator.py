"""
ACCUMULATOR VALIDATION - Track performance of 2,4,7,10 odds accumulators
Run after matches are complete
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
    """Parse validation results"""
    
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


def check_prediction(prediction, actual):
    """Check if a single prediction was correct"""
    play = prediction.get('play', '')
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    
    if 'Home Win' in play:
        return home > away
    elif 'Draw' in play:
        return home == away
    elif 'Both Teams to Score' in play:
        return (home > 0 and away > 0) if 'YES' in play else (home == 0 or away == 0)
    elif 'Over 1.5' in play:
        return total > 1
    elif 'Under 3.5' in play:
        return total < 4
    elif 'Over 2.5' in play:
        return total > 2
    elif 'Draw or GG' in play:
        return (home == away) or (home > 0 and away > 0)
    elif 'Draw or Under 2.5' in play:
        return (home == away) or total < 3
    return False


def validate_accumulator(acc_matches, validation_results):
    """Validate all legs of an accumulator"""
    results = []
    all_correct = True
    
    for match in acc_matches:
        match_name = clean_match_name(match.get('match', ''))
        actual = validation_results.get(match_name)
        
        if actual:
            is_correct = check_prediction(match, actual)
            results.append({
                'match': match.get('match', 'Unknown'),
                'play': match.get('play', 'Unknown'),
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'correct': is_correct
            })
            if not is_correct:
                all_correct = False
        else:
            results.append({
                'match': match.get('match', 'Unknown'),
                'play': match.get('play', 'Unknown'),
                'actual_score': 'NOT FOUND',
                'correct': False
            })
            all_correct = False
    
    return results, all_correct


def main():
    print("\n" + "="*60)
    print("⚽ ACCUMULATOR PERFORMANCE VALIDATION")
    print("="*60)
    
    # This would need accumulator data from main.py
    # For now, create a template
    print("\n📋 To track accumulator performance:")
    print("   1. After main.py runs, note the accumulator picks")
    print("   2. After matches, run validation")
    print("   3. Compare which accumulators won\n")
    
    # Load predictions
    if not os.path.exists("predictions.json"):
        print("❌ No predictions.json found")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Load validation results
    validation_results = parse_validation_file("validation_results.txt")
    
    if validation_results:
        print(f"✅ Loaded {len(validation_results)} validation results")
        print("\n🔍 Validating predictions...")
        
        # Validate each prediction
        correct = 0
        for pred in predictions:
            match_name = clean_match_name(pred.get('match', ''))
            actual = validation_results.get(match_name)
            if actual:
                if check_prediction(pred, actual):
                    correct += 1
        
        print(f"\n📊 Prediction Accuracy: {correct}/{len(predictions)} ({correct/len(predictions)*100:.1f}%)")
    
    print("\n✅ Accumulator validation ready")
    print("   Future version will track 2_ODDS, 4_ODDS, 7_ODDS, 10_ODDS separately")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
