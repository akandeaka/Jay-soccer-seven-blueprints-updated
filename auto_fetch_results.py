"""
Auto Fetch Results from Flashscore
Automatically validates predictions without manual CSV creation
"""

import os
import json
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from flashscore import FlashscoreApi

async def fetch_match_results(predictions):
    """
    Fetch actual results from Flashscore for predicted matches
    """
    api = FlashscoreApi()
    results = []
    
    # Get today's and yesterday's matches
    try:
        print("📡 Fetching recent matches from Flashscore...")
        today_matches = await api.get_today_matches()
        
        print(f"   Found {len(today_matches)} recent matches")
        
        # Load match content to get scores
        for match in today_matches:
            await match.load_content()
            
            # Get match details
            home_team = getattr(match, 'home_team_name', '')
            away_team = getattr(match, 'away_team_name', '')
            match_name = f"{home_team} vs {away_team}"
            
            # Check if this match is in our predictions
            for pred in predictions:
                if match_name.lower() in pred['match'].lower() or pred['match'].lower() in match_name.lower():
                    home_score = getattr(match, 'home_team_score', 0) or 0
                    away_score = getattr(match, 'away_team_score', 0) or 0
                    
                    if home_score > 0 or away_score > 0:
                        result = "Home Win" if home_score > away_score else "Away Win" if away_score > home_score else "Draw"
                        
                        results.append({
                            'match': match_name,
                            'home_score': home_score,
                            'away_score': away_score,
                            'result': result
                        })
                        print(f"   ✅ Found: {match_name} - {home_score}-{away_score}")
                        break
        
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"❌ Error fetching from Flashscore: {e}")
        return pd.DataFrame()

def create_actual_results_from_flashscore(predictions_file="predictions.json"):
    """
    Main function - replaces manual actual_results.csv creation
    """
    print("\n" + "="*60)
    print("⚽ AUTO FETCHING MATCH RESULTS FROM FLASHSCORE")
    print("="*60)
    
    # Load predictions
    if not os.path.exists(predictions_file):
        print("❌ No predictions.json found - run main.py first")
        return None
    
    with open(predictions_file, 'r') as f:
        predictions = json.load(f)
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Fetch results asynchronously
    results_df = asyncio.run(fetch_match_results(predictions))
    
    if results_df.empty:
        print("⚠️ No results found on Flashscore yet")
        print("   (Matches may not have finished or are not available)")
        return None
    
    # Save to actual_results.csv
    results_df.to_csv("actual_results.csv", index=False)
    print(f"\n✅ Saved {len(results_df)} results to actual_results.csv")
    
    return results_df

if __name__ == "__main__":
    create_actual_results_from_flashscore()
