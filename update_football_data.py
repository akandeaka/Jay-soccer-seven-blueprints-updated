"""
Automatically updates football-data.co.uk datasets daily
Uses GitHub Actions to run at 6 AM every day
"""

import os
import requests
import pandas as pd
from datetime import datetime

# List of leagues to download (from football-data.co.uk)
LEAGUES = {
    'E0': 'Premier League',
    'E1': 'Championship',
    'E2': 'League One',
    'E3': 'League Two',
    'SC0': 'Scottish Premiership',
    'SC1': 'Scottish Championship',
    'D1': 'Bundesliga',
    'D2': '2. Bundesliga',
    'I1': 'Serie A',
    'I2': 'Serie B',
    'SP1': 'La Liga',
    'SP2': 'Segunda Division',
    'F1': 'Ligue 1',
    'F2': 'Ligue 2',
    'N1': 'Eredivisie',
    'P1': 'Primeira Liga',
    'T1': 'Super Lig',
    'G1': 'Super League Greece',
    'B1': 'Pro League Belgium',
    'C1': 'Chance Liga',
}

def download_league_data(league_code, league_name):
    """Download data for a specific league"""
    url = f"https://www.football-data.co.uk/mmz4281/2526/{league_code}.csv"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Save raw CSV
            with open(f"data/{league_code}_{league_name}.csv", 'wb') as f:
                f.write(response.content)
            
            # Also parse and save as JSON for easier use
            df = pd.read_csv(url)
            df.to_json(f"data/{league_code}_{league_name}.json", orient='records')
            
            print(f"✅ Downloaded {league_name}")
            return True
    except Exception as e:
        print(f"❌ Failed to download {league_name}: {e}")
        return False

def main():
    """Download all league data"""
    print(f"📅 Football-Data.co.uk Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Download all leagues
    for code, name in LEAGUES.items():
        download_league_data(code, name)
    
    print("✅ Update complete")

if __name__ == "__main__":
    main()
