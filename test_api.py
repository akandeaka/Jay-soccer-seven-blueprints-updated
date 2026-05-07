import os
from api_fetcher import APIDataManager

print("Testing API connection...")
manager = APIDataManager()
df = manager.get_todays_matches()

if df.empty:
    print("\n❌ No real matches returned")
else:
    print(f"\n✅ Found {len(df)} real matches:")
    for i, row in df.head(5).iterrows():
        print(f"   - {row['match']} ({row['league']})")
