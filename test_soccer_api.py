"""
Test script to check soccer league access
Run this in GitHub Actions or locally
"""

import os
import requests

API_KEY = os.environ.get("ODDS_API_KEY", "YOUR_API_KEY_HERE")

print("="*60)
print("TESTING SOCCER-SPECIFIC ENDPOINTS")
print("="*60)

# Test 1: Try to fetch Premier League directly
print("\n[TEST 1] Fetching soccer_epl directly...")
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
        print(f"    ✓ SUCCESS! Found {len(data)} matches")
        if data:
            print(f"    First match: {data[0].get('home_team')} vs {data[0].get('away_team')}")
    elif response.status_code == 404:
        print(f"    ✗ League 'soccer_epl' not found (404)")
        print(f"    Response: {response.text[:200]}")
    else:
        print(f"    ✗ Error: {response.status_code}")
        print(f"    Response: {response.text[:200]}")
        
except Exception as e:
    print(f"    Exception: {e}")

# Test 2: Try Champions League
print("\n[TEST 2] Fetching soccer_uefa_champs_league directly...")
url = "https://api.the-odds-api.com/v4/sports/soccer_uefa_champs_league/odds"

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"    Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"    ✓ SUCCESS! Found {len(data)} matches")
    elif response.status_code == 404:
        print(f"    ✗ League 'soccer_uefa_champs_league' not found (404)")
    else:
        print(f"    ✗ Error: {response.status_code}")
        
except Exception as e:
    print(f"    Exception: {e}")

# Test 3: List all available sports (filtered)
print("\n[TEST 3] Getting all sports and filtering...")
url = "https://api.the-odds-api.com/v4/sports"
params = {"apiKey": API_KEY}

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"    Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"    Total sports: {len(data)}")
        
        # Look for any soccer-related sports
        soccer_keywords = ['soccer', 'football', 'uefa', 'epl', 'bundesliga', 'laliga', 'seriea', 'ligue1']
        soccer_sports = []
        
        for sport in data:
            sport_key = sport.get('key', '').lower()
            sport_title = sport.get('title', '').lower()
            for keyword in soccer_keywords:
                if keyword in sport_key or keyword in sport_title:
                    soccer_sports.append(sport)
                    break
        
        print(f"    Potential soccer-related sports: {len(soccer_sports)}")
        
        if soccer_sports:
            print("\n    Found these soccer-related sports:")
            for sport in soccer_sports[:20]:
                print(f"      - {sport.get('key')}: {sport.get('title')}")
        else:
            print("\n    ⚠️ NO soccer leagues found in the response!")
            print("    This suggests your API key may not have soccer access.")
            print("\n    First 10 sports returned:")
            for sport in data[:10]:
                print(f"      - {sport.get('key')}: {sport.get('title')}")
                
except Exception as e:
    print(f"    Exception: {e}")

print("\n" + "="*60)
