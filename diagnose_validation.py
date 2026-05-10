# Create the diagnostic script
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

# Check API
api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
print(f"\n✅ API Key: {'SET' if api_key else 'NOT SET'}")

# Check matches
print("\n📡 Recent finished matches:")
for i in range(3):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    url = f"https://api.football-data.org/v4/matches?date={date}"
    headers = {'X-Auth-Token': api_key} if api_key else {}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            matches = r.json().get('matches', [])
            finished = [m for m in matches if m.get('status') == 'FINISHED']
            print(f"   {date}: {len(finished)} finished matches")
    except:
        pass
EOF

# Run it
python diagnose_validation.py
