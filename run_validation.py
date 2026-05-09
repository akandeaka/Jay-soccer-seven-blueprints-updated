"""
RUN VALIDATION - Automatically fetches results from free API
Runs at 1 AM daily - No manual CSV needed
"""

import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from results_validator import ResultsValidator

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Free API endpoint (Football-Data.org - free tier, no API key required for basic data)
# Note: This API has rate limits but works for validation

# ============================================================
# FUNCTION: FETCH RESULTS FROM FREE API
# ============================================================

def fetch_results_from_api(predictions):
    """
    Automatically fetch match results using free API
    No API key required for basic data
    """
    
    results = []
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Try multiple free endpoints
    apis_to_try = [
        f"https://api.football-data.org/v4/matches?date={yesterday}",
        f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={yesterday.replace('-', '')}&s=Soccer"
    ]
    
    for url in apis_to_try:
        try:
            headers = {}
            # Add API key if available (optional, free tier works without)
            api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
            if api_key:
                headers['X-Auth-Token'] = api_key
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse Football-Data.org format
                if 'matches' in data:
                    for match in data['matches']:
                        if match.get('status') == 'FINISHED':
                            home = match['homeTeam']['name']
                            away = match['awayTeam']['name']
                            match_name = f"{home} vs {away}"
                            home_score = match['score']['fullTime']['home']
                            away_score = match['score']['fullTime']['away']
                            
                            if home_score is not None and away_score is not None:
                                results.append({
                                    'match': match_name,
                                    'home_score': home_score,
                                    'away_score': away_score,
                                    'result': 'Home Win' if home_score > away_score else 'Away Win' if away_score > home_score else 'Draw'
                                })
                
                # Parse TheSportsDB format
                elif 'events' in data:
                    for match in data['events']:
                        home = match.get('strHomeTeam', '')
                        away = match.get('strAwayTeam', '')
                        if home and away:
                            match_name = f"{home} vs {away}"
                            home_score = int(match.get('intHomeScore', 0) or 0)
                            away_score = int(match.get('intAwayScore', 0) or 0)
                            results.append({
                                'match': match_name,
                                'home_score': home_score,
                                'away_score': away_score,
                                'result': 'Home Win' if home_score > away_score else 'Away Win' if away_score > home_score else 'Draw'
                            })
                
                if results:
                    break
                    
        except Exception as e:
            print(f"   API error: {e}")
            continue
    
    # Match results with predictions
    matched_results = []
    for pred in predictions:
        pred_match = pred.get('match', '')
        for res in results:
            if pred_match.lower() in res['match'].lower() or res['match'].lower() in pred_match.lower():
                matched_results.append({
                    'match': pred_match,
                    'home_score': res['home_score'],
                    'away_score': res['away_score'],
                    'result': res['result']
                })
                break
    
    if matched_results:
        df = pd.DataFrame(matched_results)
        df.to_csv("actual_results.csv", index=False)
        print(f"✅ Auto-fetched {len(matched_results)} results from API")
    else:
        print("⚠️ No results found from API - you may need to add actual_results.csv manually")
    
    return pd.DataFrame(matched_results)

# ============================================================
# FUNCTION: SEND TO TELEGRAM
# ============================================================

def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return False
    
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
# MAIN VALIDATION
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ AUTOMATIC MATCH VALIDATION")
    print("Fetching results from free API...")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if predictions exist
    if not os.path.exists("predictions.json"):
        print("\n❌ No predictions.json found!")
        print("   Run main.py first to generate predictions")
        return 1
    
    # Load predictions
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    if not predictions:
        print("❌ No predictions to validate")
        return 1
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Try to fetch results automatically
    print("\n📡 Fetching match results from free API...")
    actual_results = fetch_results_from_api(predictions)
    
    # If API fetch failed, check for manual CSV
    if actual_results.empty:
        print("\n⚠️ Could not auto-fetch results.")
        
        # Check if manual CSV exists
        if os.path.exists("actual_results.csv"):
            print("   Loading manual actual_results.csv...")
            actual_results = pd.read_csv("actual_results.csv")
        else:
            print("\n❌ No results available for validation")
            print("\n💡 To validate predictions:")
            print("   1. Create actual_results.csv manually")
            print("   2. Or add a free API key to FOOTBALL_DATA_API_KEY secret")
            send_telegram("⚠️ VALIDATION FAILED\n\nCould not fetch match results. Please check API configuration or add actual_results.csv manually.")
            return 1
    
    if actual_results.empty:
        print("❌ No results to validate")
        return 1
    
    # Validate predictions
    validator = ResultsValidator()
    validated = validator.validate_predictions(predictions, actual_results)
    
    # Calculate statistics
    total = len([v for v in validated if v['actual_result'] != 'NO_RESULT_FOUND'])
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"   Total matches: {total}")
    print(f"   Correct: {correct}")
    print(f"   Wrong: {total - correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    # Generate report
    report = validator.generate_performance_report(validated)
    validator.update_history(validated)
    
    # Send summary to Telegram
    summary = f"""📊 PERFORMANCE REPORT
📅 {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 VALIDATION RESULTS
   Total Predictions: {total}
   Correct: {correct}
   Wrong: {total - correct}
   Accuracy: {accuracy:.1f}%

✅ Results: {'Auto-fetched from API' if not os.path.exists('actual_results.csv') else 'Manually entered'}
"""
    
    send_telegram(summary)
    
    print(f"\n✅ Validation complete!")
    print(f"   Accuracy: {accuracy:.1f}% ({correct}/{total})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
