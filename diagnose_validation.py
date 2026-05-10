# Delete the broken file
rm -f diagnose_validation.py

# Create a clean version
cat > diagnose_validation.py << 'EOF'
import os
import json
import requests
from datetime import datetime, timedelta

print("="*60)
print("VALIDATION DIAGNOSTIC")
print("="*60)

# Check predictions
if os.path.exists("predictions.json"):
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    print(f"\n✅ predictions.json: {len(predictions)} predictions")
    for p in predictions[:3]:
        print(f"   - {p.get('match', 'N/A')}")
else:
    print("\n❌ predictions.json NOT FOUND")

# Check API key
api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
print(f"\n✅ API Key: {'SET' if api_key else 'NOT SET'}")

# Check recent matches
print("\n📡 Recent finished matches:")
headers = {'X-Auth-Token': api_key} if api_key else {}

for i in range(3):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    url = f"https://api.football-data.org/v4/matches?date={date}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            matches = data.get('matches', [])
            finished = [m for m in matches if m.get('status') == 'FINISHED']
            print(f"   {date}: {len(finished)} finished matches")
        else:
            print(f"   {date}: API status {r.status_code}")
    except Exception as e:
        print(f"   {date}: Error - {e}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
EOF
