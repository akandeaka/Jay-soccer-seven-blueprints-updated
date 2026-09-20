"""
VALIDATION SYSTEM - Robust Fuzzy Matching & Accumulator Settlement
-------------------------------------------------------------------
Fixes string matching failures caused by markdown formatting, country 
tags (e.g. '(Fin)'), and variable result line spacings.
"""

import os
import sys
import json
import re
import html
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def normalize_name(name: str) -> str:
    """Strips markdown, country codes in parentheses, punctuation, and standardizes spacing."""
    if not name:
        return ""
    name = name.replace('**', '').replace('*', '')
    name = re.sub(r'\([a-zA-Z0-9\s\.-]+\)', '', name)  # Removes (Fin), (Isr), etc.
    name = re.sub(r'\b(fc|ac|utd|united|sv|vfb|sc|afc|cd|ud)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z0-9]', '', name.lower())
    return name.strip()


def parse_validation_file(filepath="results.txt") -> dict:
    """Robustly parses validation results text file."""
    if not os.path.exists(filepath):
        print(f"❌ '{filepath}' not found.")
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {}
    # Split content by fixture blocks or double newlines
    blocks = re.split(r'\n\s*\n', content)
    
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        match_name = None
        
        for line in lines:
            if ' vs ' in line and 'RESULT:' not in line:
                match_name = line
            elif 'RESULT:' in line and match_name:
                score_match = re.search(r'(\d+)-(\d+)', line)
                if score_match:
                    norm_key = normalize_name(match_name)
                    results[norm_key] = {
                        'raw_name': match_name,
                        'home_score': int(score_match.group(1)),
                        'away_score': int(score_match.group(2))
                    }
                match_name = None  # Reset for next match

    return results


def check_prediction(play: str, actual: dict) -> bool:
    """Validates predictions against actual scores."""
    home = actual['home_score']
    away = actual['away_score']
    total = home + away
    p = play.lower()

    if 'straight home win' in p or 'home win' in p or p == '1':
        return home > away
    elif 'away win' in p or p == '2':
        return away > home
    elif 'draw' in p and 'or' not in p:
        return home == away
    elif 'both teams to score - yes' in p or 'gg' in p:
        return home > 0 and away > 0
    elif 'both teams to score - no' in p:
        return home == 0 or away == 0
    elif 'over 1.5' in p:
        return total > 1
    elif 'under 3.5' in p:
        return total < 4
    elif 'over 2.5' in p:
        return total > 2
    elif 'under 2.5' in p:
        return total < 3
    elif '1x & over 1.5' in p:
        return (home >= away) and total > 1
    elif '1x & under 3.5' in p:
        return (home >= away) and total < 4
    elif 'draw or under 2.5' in p:
        return (home == away) or total < 3
    elif 'draw or gg' in p:
        return (home == away) or (home > 0 and away > 0)
    return False


def get_short_play(play: str) -> str:
    """Converts prediction text to short format."""
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


def find_actual_result(match_name: str, validation_results: dict):
    """Finds score matching using fuzzy normalized key comparison."""
    norm_match = normalize_name(match_name)
    if not norm_match:
        return None
        
    for key, data in validation_results.items():
        if norm_match in key or key in norm_match:
            return data
    return None


def validate_accumulator_legs(accumulators: dict, validation_results: dict) -> dict:
    """Validates each leg inside accumulators.json."""
    acc_results = {}
    
    for acc_name, acc_data in accumulators.items():
        legs = []
        all_correct = True
        
        for match in acc_data.get('matches', []):
            raw_match_name = match.get('match', '')
            play = match.get('play', '')
            actual = find_actual_result(raw_match_name, validation_results)
            
            if actual:
                is_correct = check_prediction(play, actual)
                legs.append({
                    'match': raw_match_name,
                    'play': play,
                    'short_play': get_short_play(play),
                    'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                    'correct': is_correct
                })
                if not is_correct:
                    all_correct = False
            else:
                legs.append({
                    'match': raw_match_name,
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


def main():
    print("\n" + "="*60)
    print("⚽ VALIDATION ENGINE - FUZZY MATCH & SETTLEMENT")
    print("="*60)
    
    if not os.path.exists("predictions.json"):
        print("❌ predictions.json not found")
        return 1
    
    with open("predictions.json", 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    validation_results = parse_validation_file("results.txt")
    if not validation_results:
        print("❌ No valid score entries retrieved from results.txt")
        return 1
        
    accumulators = {}
    if os.path.exists("accumulators.json"):
        with open("accumulators.json", 'r', encoding='utf-8') as f:
            accumulators = json.load(f)

    # Sort and take Top 30 predictions
    sorted_preds = sorted(predictions, key=lambda x: x.get('composite_score', x.get('confidence', 0)), reverse=True)
    top_30 = sorted_preds[:30]
    
    validated_preds = []
    for pred in top_30:
        raw_match_name = pred.get('match', '')
        play = pred.get('play', '')
        actual = find_actual_result(raw_match_name, validation_results)
        
        if actual:
            is_correct = check_prediction(play, actual)
            validated_preds.append({
                'match': raw_match_name,
                'play': play,
                'short_play': get_short_play(play),
                'actual_score': f"{actual['home_score']}-{actual['away_score']}",
                'correct': is_correct
            })
        else:
            validated_preds.append({
                'match': raw_match_name,
                'play': play,
                'short_play': get_short_play(play),
                'actual_score': 'NOT FOUND',
                'correct': False
            })

    acc_validation = validate_accumulator_legs(accumulators, validation_results)
    
    # Assemble Telegram message with escaped HTML
    report = f"🏁 <b>SETTLEMENT REPORT</b>\n📅 {datetime.now().strftime('%Y-%m-%d')}\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += "📊 <b>TOP 30 PREDICTIONS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for v in validated_preds:
        status = "✅" if v['correct'] else "❌"
        clean_match = html.escape(v['match'])
        clean_play = html.escape(v['short_play'])
        report += f"{status} <b>{clean_match}</b>\n   🎯 {clean_play} | Score: {v['actual_score']}\n"
    
    if acc_validation:
        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 <b>ACCUMULATOR RESULTS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for acc_name, acc_data in acc_validation.items():
            status = "✅ WON" if acc_data['all_correct'] else "❌ LOST"
            report += f"\n<b>{acc_name}</b> | Odds: {acc_data['odds']} | {status} ({acc_data['correct_count']}/{acc_data['total_count']})\n"
            for leg in acc_data['legs']:
                leg_status = "✅" if leg['correct'] else "❌"
                clean_leg_match = html.escape(leg['match'])
                report += f"   {leg_status} {clean_leg_match} -> {leg['short_play']} ({leg['actual_score']})\n"
    
    correct_preds = sum(1 for v in validated_preds if v['correct'])
    total_preds = len(validated_preds)
    pred_accuracy = (correct_preds / total_preds * 100) if total_preds > 0 else 0
    
    report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 <b>SUMMARY</b>\n"
    report += f"✅ Top 30 Accuracy: {correct_preds}/{total_preds} ({pred_accuracy:.1f}%)\n"
    
    print("\n" + report)
    
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            r = requests.post(url, json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': report,
                'parse_mode': 'HTML'
            }, timeout=30)
            if r.json().get('ok'):
                print("✅ Report dispatched to Telegram.")
            else:
                print(f"⚠️ Telegram send failure: {r.text}")
        except Exception as e:
            print(f"❌ Telegram exception: {e}")
            
    return 0

if __name__ == "__main__":
    sys.exit(main())
