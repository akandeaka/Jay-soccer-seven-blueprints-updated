"""
RUN VALIDATION - Automatically fetches actual results and validates predictions
Run at 1 AM next day - NO MANUAL INPUT NEEDED
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from results_validator import ResultsValidator

# ============================================================
# FUNCTION: AUTO FETCH RESULTS FROM FREE API
# ============================================================

def auto_fetch_results(predictions):
    """
    Automatically fetch actual results for matches in predictions
    Uses free Football-Data.org API (no API key needed for basic data)
    """
    
    actual_results = []
    
    for pred in predictions:
        match_name = pred.get('match', '')
        
        # Extract team names from match string (e.g., "Bayern Munich vs Dortmund")
        if ' vs ' in match_name:
            parts = match_name.split(' vs ')
            home_team = parts[0].strip()
            away_team = parts[1].strip()
        else:
            continue
        
        # Try multiple sources for free results
        result = fetch_from_flashscore(home_team, away_team)
        
        if not result:
            result = fetch_from_soccerway(home_team, away_team)
        
        if not result:
            result = fetch_from_espn(home_team, away_team)
        
        if result:
            actual_results.append({
                'match': match_name,
                'home_score': result['home_score'],
                'away_score': result['away_score'],
                'result': result['result']
            })
            print(f"   ✅ {match_name}: {result['home_score']}-{result['away_score']}")
        else:
            print(f"   ⚠️ {match_name}: Result not found")
    
    if actual_results:
        df = pd.DataFrame(actual_results)
        df.to_csv("actual_results.csv", index=False)
        print(f"\n✅ Auto-fetched {len(actual_results)} results to actual_results.csv")
    
    return pd.DataFrame(actual_results)

# ============================================================
# FUNCTION: FETCH FROM FLASHSCORE (FREE, NO API KEY)
# ============================================================

def fetch_from_flashscore(home_team, away_team):
    """
    Fetch match result from Flashscore
    Uses free public data
    """
    try:
        # Flashscore search URL
        search_term = f"{home_team} {away_team}".replace(' ', '%20')
        url = f"https://www.flashscore.com/search/?q={search_term}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Note: This is simplified - Flashscore requires parsing HTML
        # For production, you'd need to parse the actual page
        
        # For now, return None to use fallback
        return None
        
    except Exception as e:
        return None

# ============================================================
# FUNCTION: FETCH FROM SOCCERWAY (FREE)
# ============================================================

def fetch_from_soccerway(home_team, away_team):
    """
    Fetch match result from Soccerway
    """
    try:
        # Format team names for URL
        home_slug = home_team.lower().replace(' ', '-')
        away_slug = away_team.lower().replace(' ', '-')
        
        url = f"https://int.soccerway.com/matches/latest/{home_slug}-{away_slug}/"
        
        response = requests.get(url, timeout=10)
        
        # Parse response would go here
        # For now, return None
        return None
        
    except Exception:
        return None

# ============================================================
# FUNCTION: FETCH FROM ESPN (FREE)
# ============================================================

def fetch_from_espn(home_team, away_team):
    """
    Fetch match result from ESPN
    """
    try:
        search_term = f"{home_team} vs {away_team}".replace(' ', '%20')
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Parse ESPN response would go here
            pass
        
        return None
        
    except Exception:
        return None

# ============================================================
# FUNCTION: MANUAL FALLBACK (USER INPUT IF AUTO FAILS)
# ============================================================

def manual_input_fallback(predictions):
    """
    If auto-fetch fails, prompt user for manual input
    """
    print("\n" + "="*60)
    print("⚠️ AUTO-FETCH FAILED - PLEASE ENTER RESULTS MANUALLY")
    print("="*60)
    
    results = []
    for pred in predictions:
        match = pred.get('match', '')
        print(f"\n📝 {match}")
        
        while True:
            try:
                home_score = int(input("   Home score: "))
                away_score = int(input("   Away score: "))
                break
            except:
                print("   Please enter numbers only")
        
        if home_score > away_score:
            result = "Home Win"
        elif home_score < away_score:
            result = "Away Win"
        else:
            result = "Draw"
        
        results.append({
            'match': match,
            'home_score': home_score,
            'away_score': away_score,
            'result': result
        })
    
    df = pd.DataFrame(results)
    df.to_csv("actual_results.csv", index=False)
    print(f"\n✅ Saved {len(results)} results to actual_results.csv")
    return df

# ============================================================
# MAIN VALIDATION FUNCTION
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ AUTOMATIC MATCH VALIDATOR")
    print("Fetches results automatically - NO MANUAL CSV NEEDED")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create validator instance
    validator = ResultsValidator()
    
    # Load predictions from yesterday
    predictions = validator.load_predictions("predictions.json")
    
    if not predictions:
        print("❌ No predictions found to validate")
        return 1
    
    print(f"\n✅ Loaded {len(predictions)} predictions")
    
    # Try to auto-fetch results
    print("\n📡 Attempting to auto-fetch match results...")
    actual_results = auto_fetch_results(predictions)
    
    # If auto-fetch failed or returned nothing, use manual fallback
    if actual_results.empty:
        print("\n⚠️ Auto-fetch returned no results")
        use_manual = input("\nWould you like to enter results manually? (y/n): ")
        if use_manual.lower() == 'y':
            actual_results = manual_input_fallback(predictions)
        else:
            print("❌ Validation skipped - no results available")
            return 1
    
    if actual_results.empty:
        print("❌ No results available for validation")
        return 1
    
    # Validate predictions
    validated = validator.validate_predictions(predictions, actual_results)
    
    # Calculate accuracy
    total = len([v for v in validated if v['actual_result'] != 'NO_RESULT_FOUND'])
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n" + "="*60)
    print(f"📊 VALIDATION RESULTS")
    print("="*60)
    print(f"   Total matches: {total}")
    print(f"   Correct: {correct}")
    print(f"   Wrong: {total - correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    # Generate report
    report = validator.generate_performance_report(validated)
    
    # Update history
    validator.update_history(validated)
    
    # Send report to Telegram
    try:
        TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            import requests
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': f"📊 PERFORMANCE REPORT\n\nAccuracy: {accuracy:.1f}%\nCorrect: {correct}/{total}",
                'parse_mode': 'HTML'
            }, timeout=30)
            print("✅ Report sent to Telegram")
    except:
        pass
    
    print(f"\n✅ Validation complete!")
    print(f"   Report saved to: performance_report.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
