"""
Manual test script - Run this on your local machine first
to verify API key and connectivity
"""

import os
import requests

# IMPORTANT: Replace with your actual API key
API_KEY = "YOUR_API_KEY_HERE"

def test_api():
    print("="*60)
    print("MANUAL API TEST")
    print("="*60)
    
    # Test 1: Get all sports
    print("\n[1] Testing /sports endpoint...")
    url = "https://api.the-odds-api.com/v4/sports"
    params = {"apiKey": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Total sports: {len(data)}")
            
            soccer_leagues = [s for s in data if s.get('key', '').startswith('soccer')]
            print(f"    Soccer leagues: {len(soccer_leagues)}")
            
            print("\n    First 10 soccer leagues:")
            for league in soccer_leagues[:10]:
                print(f"      - {league.get('key')}")
        else:
            print(f"    Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"    Exception: {e}")
    
    # Test 2: Get odds for Premier League
    print("\n[2] Testing /sports/soccer_epl/odds...")
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "uk",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Matches found: {len(data)}")
            
            # Print headers for rate limit info
            remaining = response.headers.get("x-requests-remaining")
            used = response.headers.get("x-requests-used")
            print(f"    Rate limit - Remaining: {remaining}, Used: {used}")
            
            if data:
                print("\n    First match:")
                first = data[0]
                print(f"      Home: {first.get('home_team')}")
                print(f"      Away: {first.get('away_team')}")
                print(f"      Time: {first.get('commence_time')}")
        else:
            print(f"    Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"    Exception: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_api()
