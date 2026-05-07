"""
Diagnostic Tool - Find where demo data is coming from
"""

import os
import sys

print("="*60)
print("🔍 DIAGNOSTIC TOOL - Finding Demo Data Source")
print("="*60)

# 1. Check config
print("\n1. Checking config.py...")
try:
    from config import Config
    print(f"   USE_API = {Config.USE_API}")
    print(f"   INPUT_FILE = {Config.INPUT_FILE}")
    print(f"   ODDS_API_KEY = {'SET' if Config.ODDS_API_KEY else 'NOT SET'}")
except Exception as e:
    print(f"   ERROR: {e}")

# 2. Check if input_matches.txt exists
print("\n2. Checking input_matches.txt...")
if os.path.exists("input_matches.txt"):
    print(f"   ✅ File exists: input_matches.txt")
    with open("input_matches.txt", 'r') as f:
        content = f.read()[:200]
        print(f"   Content preview: {content[:100]}...")
else:
    print(f"   ❌ File does NOT exist: input_matches.txt")

# 3. Test The Odds API directly
print("\n3. Testing The Odds API directly...")
import requests

API_KEY = os.getenv('ODDS_API_KEY', Config.ODDS_API_KEY if 'Config' in dir() else '')
if API_KEY:
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            sports = response.json()
            print(f"   ✅ Connected! Found {len(sports)} sports")
            
            # Try to get EPL matches
            epl_url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
            epl_params = {
                'apiKey': API_KEY,
                'regions': 'uk',
                'markets': 'h2h,totals',
                'oddsFormat': 'decimal'
            }
            epl_response = requests.get(epl_url, params=epl_params, timeout=10)
            
            if epl_response.status_code == 200:
                matches = epl_response.json()
                if matches:
                    print(f"   ✅ EPL: Found {len(matches)} REAL matches")
                    for match in matches[:3]:
                        print(f"      - {match.get('home_team')} vs {match.get('away_team')}")
                else:
                    print(f"   ⚠️ EPL: No matches returned (empty array)")
                    print(f"      This means: No real matches scheduled today")
            else:
                print(f"   ❌ EPL API Error: {epl_response.status_code}")
                print(f"      Response: {epl_response.text[:200]}")
        else:
            print(f"   ❌ API Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
else:
    print(f"   ❌ No API key found")

# 4. Check which file is generating predictions
print("\n4. Checking for predictions.json...")
if os.path.exists("predictions.json"):
    import json
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    print(f"   ✅ predictions.json exists with {len(predictions)} predictions")
    if predictions:
        print(f"   First prediction: {predictions[0].get('match', 'Unknown')}")
        print(f"   This is where the Telegram message is reading from!")

print("\n" + "="*60)
print("🔍 DIAGNOSIS COMPLETE")
print("="*60)
print("\n💡 Based on results above:")
print("   - If API returns no matches, the system is using FALLBACK data")
print("   - If predictions.json exists, DELETE it and rerun")
