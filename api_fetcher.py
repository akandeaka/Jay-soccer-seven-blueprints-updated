"""
API Fetcher - ONLY real matches from API, NO DEMO DATA
"""

import requests
import pandas as pd
from typing import List, Dict, Optional
import os
import time
from datetime import datetime


class OddsAPIFetcher:
    """Fetches ONLY real matches from The Odds API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def test_api_key(self) -> bool:
        """Test if API key is valid"""
        if not self.api_key:
            print("❌ No API key found")
            return False
        
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                print("✅ API key is VALID")
                return True
            else:
                print(f"❌ API key INVALID (Status: {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Cannot reach API: {e}")
            return False
    
    def get_upcoming_matches(self, sport: str) -> List[Dict]:
        """Fetch REAL upcoming matches - NO DEMO DATA"""
        
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'uk',
            'markets': 'h2h,totals',
            'oddsFormat': 'decimal'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            if not data:
                return []
            
            matches = []
            for fixture in data:
                match_data = self._parse_fixture(fixture)
                if match_data:
                    matches.append(match_data)
            
            return matches
            
        except Exception:
            return []
    
    def _parse_fixture(self, fixture: Dict) -> Optional[Dict]:
        """Parse fixture data"""
        try:
            home_team = fixture.get('home_team', '')
            away_team = fixture.get('away_team', '')
            
            if not home_team or not away_team:
                return None
            
            bookmakers = fixture.get('bookmakers', [])
            if not bookmakers:
                return None
            
            odds_data = bookmakers[0].get('markets', [])
            
            home_odds = 0
            draw_odds = 0
            away_odds = 0
            over_25_odds = 0
            under_25_odds = 0
            
            for market in odds_data:
                market_key = market.get('key', '')
                outcomes = market.get('outcomes', [])
                
                if market_key == 'h2h':
                    for outcome in outcomes:
                        name = outcome.get('name', '')
                        price = outcome.get('price', 0)
                        if name == home_team:
                            home_odds = price
                        elif name == away_team:
                            away_odds = price
                        elif name == 'Draw':
                            draw_odds = price
                
                elif market_key == 'totals':
                    for outcome in outcomes:
                        name = outcome.get('name', '')
                        price = outcome.get('price', 0)
                        point = outcome.get('point', 2.5)
                        
                        if point == 2.5:
                            if 'Over' in name:
                                over_25_odds = price
                            elif 'Under' in name:
                                under_25_odds = price
            
            if home_odds == 0 or draw_odds == 0 or away_odds == 0:
                return None
            
            sport_title = fixture.get('sport_title', '')
            league = sport_title.replace('Soccer - ', '').replace('soccer_', '').replace('_', ' ').title()
            
            return {
                'match': f"{home_team} vs {away_team}",
                'league': league,
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds,
                'btts_yes_odds': 0,
                'over_25_odds': over_25_odds,
                'under_25_odds': under_25_odds,
                'commence_time': fixture.get('commence_time', '')
            }
            
        except Exception:
            return None


class APIDataManager:
    """Main data manager - REAL DATA ONLY, NO DEMOS"""
    
    def __init__(self):
        self.odds_fetcher = OddsAPIFetcher(os.getenv('ODDS_API_KEY', ''))
    
    def get_todays_matches(self) -> pd.DataFrame:
        """Get REAL matches - Returns EMPTY DataFrame if no data"""
        
        print("="*60)
        print("🌐 FETCHING REAL MATCHES FROM API")
        print("="*60)
        
        if not self.odds_fetcher.test_api_key():
            print("\n❌ API KEY ISSUE - Cannot fetch real matches")
            return pd.DataFrame()
        
        all_matches = []
        
        sports = [
            'soccer_epl',
            'soccer_spain_la_liga', 
            'soccer_germany_bundesliga',
            'soccer_italy_serie_a',
            'soccer_france_ligue_one',
        ]
        
        for sport in sports:
            matches = self.odds_fetcher.get_upcoming_matches(sport)
            if matches:
                league_name = sport.replace('soccer_', '').replace('_', ' ').title()
                print(f"✅ {league_name}: {len(matches)} REAL matches")
                all_matches.extend(matches)
            time.sleep(0.5)
        
        if not all_matches:
            print("\n" + "="*60)
            print("❌ NO REAL MATCHES FOUND")
            print("="*60)
            print("\nPossible reasons:")
            print("1. No matches scheduled for today")
            print("2. API rate limit reached")
            print("3. API key has insufficient permissions")
            print("\n💡 The system will NOT generate fake data.")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_matches)
        print(f"\n✅ TOTAL: {len(df)} REAL MATCHES READY")
        print(f"   First match: {df.iloc[0]['match']}")
        
        return df
