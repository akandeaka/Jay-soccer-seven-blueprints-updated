"""
run_validation.py - Improved version
Fetches results from last 3 days, shows debug info
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')

# ============================================================
# DEBUG: Check API key
# ============================================================

print("="*60)
print("STARTING AUTOMATIC VALIDATION")
print("="*60)
print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if not FOOTBALL_DATA_API_KEY:
    print("\n❌ CRITICAL ERROR: FOOTBALL_DATA_API_KEY not found.")
    print("Please add your free API key from football-data.org to GitHub Secrets.")
    sys.exit(1)
else:
    print("\n✅ FOOTBALL_DATA_API_KEY is configured.")

# ============================================================
# LOAD PREDICTIONS
# ============================================================

try:
    with open('predictions.json', 'r') as f:
        predictions = json.load(f)
    print(f"\n✅ Loaded {len(predictions)} predictions from yesterday.")
except FileNotFoundError:
    print("\n❌ Error: 'predictions.json' not found. Run main.py first.")
    sys.exit(1)

# ============================================================
# FETCH RESULTS FROM LAST 3 DAYS
# ============================================================

print("\n📡 Fetching match results from football-data.org...")

all_matches = []
dates_to_check = []

# Check last 3 days (today, yesterday, day before)
for i in range(3):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    dates_to_check.append(date)

print(f"   Checking dates: {', '.join(dates_to_check)}")

for check_date in dates_to_check:
    api_url = f"https://api.football-data.org/v4/matches?date={check_date}"
    headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        matches = data.get('matches', [])
        print(f"   {check_date}: Found {len(matches)} matches total")
        
        # Filter only FINISHED matches
        finished = [m for m in matches if m.get('status') == 'FINISHED']
        print(f"      Finished: {len(finished)} matches")
        
        all_matches.extend(finished)
        
    except Exception as e:
        print(f"   {check_date}: Error - {e}")

print(f"\n✅ Total finished matches found: {len(all_matches)}")

if not all_matches:
    print("\n⚠️ No finished matches found in the last 3 days.")
    print("\nPossible reasons:")
    print("   1. No major league matches were played")
    print("   2. API free tier only covers: EPL, La Liga, Bundesliga, Serie A, Ligue 1")
    print("   3. Timezone difference - matches may be scheduled for later today")
    sys.exit(0)

# ============================================================
# MATCH PREDICTIONS WITH ACTUAL RESULTS
# ============================================================

print("\n🔍 Matching predictions with actual results...")

validated_results = []
for pred in predictions:
    predicted_match = pred.get('match', '')
    
    for api_match in all_matches:
        home = api_match['homeTeam']['name']
        away = api_match['awayTeam']['name']
        full_match_name = f"{home} vs {away}"
        
        if predicted_match.lower() == full_match_name.lower():
            home_score = api_match['score']['fullTime']['home']
            away_score = api_match['score']['fullTime']['away']
            
            # Simple validation - you can expand this
            is_correct = False
            predicted_play = pred.get('play', '')
            
            if 'Home Win' in predicted_play:
                is_correct = (home_score > away_score)
            elif 'Draw' in predicted_play:
                is_correct = (home_score == away_score)
            elif 'Both Teams to Score' in predicted_play:
                is_correct = (home_score > 0 and away_score > 0)
            elif 'Over 1.5' in predicted_play:
                is_correct = (home_score + away_score > 1)
            
            validated_results.append({
                "match": predicted_match,
                "predicted": predicted_play,
                "actual_score": f"{home_score}-{away_score}",
                "was_correct": is_correct
            })
            print(f"   ✅ Matched: {predicted_match} → {home_score}-{away_score}")
            break

# ============================================================
# CALCULATE STATISTICS
# ============================================================

total = len(validated_results)
correct = sum(1 for r in validated_results if r['was_correct'])
accuracy = (correct / total * 100) if total > 0 else 0

print(f"\n📊 VALIDATION RESULTS:")
print(f"   Matches found: {total}")
print(f"   Correct: {correct}")
print(f"   Wrong: {total - correct}")
print(f"   Accuracy: {accuracy:.1f}%")

# ============================================================
# SEND REPORT TO TELEGRAM
# ============================================================

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    report = f"""📊 *Performance Report*
📅 {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━
✅ Correct: {correct}
❌ Wrong: {total - correct}
📈 Accuracy: {accuracy:.1f}%
━━━━━━━━━━━━━━━━━━━━━━
_Matches validated: {total}_
"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': report,
            'parse_mode': 'Markdown'
        }, timeout=10)
        print("\n✅ Report sent to Telegram")
    except Exception as e:
        print(f"\n❌ Telegram error: {e}")
else:
    print("\n⚠️ Telegram not configured - report not sent")

# ============================================================
# SAVE RESULTS
# ============================================================

with open("performance_report.md", "w") as f:
    f.write(f"# Performance Report\n\n")
    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
    f.write(f"**Accuracy:** {accuracy:.1f}% ({correct}/{total})\n\n")
    f.write(f"## Detailed Results\n\n")
    for r in validated_results:
        status = "✅" if r['was_correct'] else "❌"
        f.write(f"{status} {r['match']}\n")
        f.write(f"   Predicted: {r['predicted']}\n")
        f.write(f"   Actual: {r['actual_score']}\n\n")

print(f"\n✅ Report saved to performance_report.md")
print("\n" + "="*60)
print("VALIDATION COMPLETE")
print("="*60)
