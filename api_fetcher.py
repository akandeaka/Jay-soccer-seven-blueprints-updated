"""
API Fetcher - Automatically fetches match data and odds from APIs
NO DEMO DATA - Only real matches from API
"""

import requests
import pandas as pd
from typing import List, Dict, Optional
import os
import time


class OddsAPIFetcher:
    """
    Fetches live odds from The Odds API
    Returns ONLY real data - NO DEMOS
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_upcoming_matches(self, sport: str = 'soccer_epl') -> List[Dict]:
        """
        Fetch all upcoming matches with odds for today
        Returns EMPTY list if no real data available
        """
        if not self.api_key:
            print("❌ No API key found. Cannot fetch real matches.")
            print("   Please add ODDS_API_KEY to GitHub Secrets")
            return []
        
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'uk',
            'markets': 'h2h,btts,totals',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            # Check if request was successful
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return []
            
            data = response.json()
            
            # Check if data is empty
            if not data:
                print(f"⚠️ No matches found for {sport} today")
                return []
            
            # Check remaining requests
            remaining = response.headers.get('x-requests-remaining', 'N/A')
            if remaining != 'N/A':
                print(f"📊 API requests remaining: {remaining}")
            
            matches = []
            for fixture in data:
                match_data = self._parse_fixture(fixture)
                if match_data:
                    matches.append(match_data)
            
            return matches
            
        except requests.exceptions.Timeout:
            print(f"❌ Timeout fetching {sport}")
            return []
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error fetching {sport}")
            return []
        except Exception as e:
            print(f"❌ Error fetching {sport}: {e}")
            return []
    
    def _parse_fixture(self, fixture: Dict) -> Optional[Dict]:
        """
        Parse a single fixture into the format your blueprint engine expects
        Returns None if data is invalid
        """
        try:
            # Extract teams - MUST have valid team names
            home_team = fixture.get('home_team', '')
            away_team = fixture.get('away_team', '')
            
            if not home_team or not away_team:
                return None
            
            # Extract odds from bookmakers
            bookmakers = fixture.get('bookmakers', [])
            if not bookmakers:
                return None
            
            # Get odds from the first bookmaker
            odds_data = bookmakers[0].get('markets', [])
            
            # Initialize odds
            home_odds = 0
            draw_odds = 0
            away_odds = 0
            btts_yes_odds = 0
            over_25_odds = 0
            under_25_odds = 0
            
            # Parse each market
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
                
                elif market_key == 'btts':
                    for outcome in outcomes:
                        name = outcome.get('name', '')
                        price = outcome.get('price', 0)
                        if name == 'Yes':
                            btts_yes_odds = price
                
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
            
            # MUST have minimum required odds to proceed
            if home_odds == 0 or draw_odds == 0 or away_odds == 0:
                return None
            
            # Get league name
            league = fixture.get('sport_title', '')
            league = league.replace('Soccer - ', '').replace('soccer_', '').replace('_', ' ').title()
            
            return {
                'match': f"{home_team} vs {away_team}",
                'league': league,
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds,
                'btts_yes_odds': btts_yes_odds,
                'over_25_odds': over_25_odds,
                'under_25_odds': under_25_odds,
                'commence_time': fixture.get('commence_time', '')
            }
            
        except Exception as e:
            return None


class FootballDataFetcher:
    """
    Fetches historical team form and BTTS records from Football-Data.org
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {'X-Auth-Token': api_key} if api_key else {}
    
    def get_team_form(self, team_name: str, league_code: str = 'PL') -> Dict:
        """Get team's recent form including BTTS record"""
        if not self.api_key:
            return {'btts_record': None, 'form_score': 50}
        
        league_codes = {
            'premier league': 'PL',
            'bundesliga': 'BL1',
            'serie a': 'SA',
            'la liga': 'PD',
            'ligue 1': 'FL1',
            'eredivisie': 'DED'
        }
        
        league_code = league_codes.get(league_code.lower(), 'PL')
        
        url = f"{self.base_url}/competitions/{league_code}/matches"
        params = {'limit': 10, 'status': 'FINISHED'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return {'btts_record': None, 'form_score': 50}
            
            data = response.json()
            
            team_matches = []
            for match in data.get('matches', []):
                home = match.get('homeTeam', {}).get('name', '')
                away = match.get('awayTeam', {}).get('name', '')
                
                if team_name.lower() in home.lower() or team_name.lower() in away.lower():
                    home_score = match.get('score', {}).get('fullTime', {}).get('home')
                    away_score = match.get('score', {}).get('fullTime', {}).get('away')
                    
                    if home_score is not None and away_score is not None:
                        btts = (home_score > 0 and away_score > 0)
                        team_matches.append({'btts': btts})
            
            if len(team_matches) >= 10:
                btts_count = sum(1 for m in team_matches[:10] if m['btts'])
                if btts_count >= 7:
                    return {'btts_record': f"{btts_count}/10", 'form_score': (btts_count/10)*100}
            
            if len(team_matches) >= 5:
                btts_count = sum(1 for m in team_matches[:5] if m['btts'])
                if btts_count >= 3:
                    return {'btts_record': f"{btts_count}/5", 'form_score': (btts_count/5)*100}
            
            return {'btts_record': None, 'form_score': 50}
            
        except Exception:
            return {'btts_record': None, 'form_score': 50}
    
    def get_btts_record_for_match(self, home_team: str, away_team: str, league: str) -> Optional[str]:
        """Get combined BTTS record for both teams"""
        if not self.api_key:
            return None
        
        home_form = self.get_team_form(home_team, league)
        away_form = self.get_team_form(away_team, league)
        
        if home_form['btts_record'] and away_form['btts_record']:
            return max(home_form['btts_record'], away_form['btts_record'])
        elif home_form['btts_record']:
            return home_form['btts_record']
        elif away_form['btts_record']:
            return away_form['btts_record']
        else:
            return None


class APIDataManager:
    """Main data manager that orchestrates both APIs - REAL DATA ONLY"""
    
    def __init__(self):
        self.odds_fetcher = OddsAPIFetcher(os.getenv('ODDS_API_KEY', ''))
        self.stats_fetcher = FootballDataFetcher(os.getenv('FOOTBALL_DATA_API_KEY', ''))
    
    def get_todays_matches(self) -> pd.DataFrame:
        """
        Get all matches for today - REAL DATA ONLY
        Returns EMPTY DataFrame if no real data available
        """
        print("🌐 Fetching REAL matches from The Odds API...")
        
        all_matches = []
        
        # List of soccer leagues to fetch
        sports = [
            ('soccer_epl', 'Premier League'),
            ('soccer_spain_la_liga', 'La Liga'),
            ('soccer_germany_bundesliga', 'Bundesliga'),
            ('soccer_italy_serie_a', 'Serie A'),
            ('soccer_france_ligue_one', 'Ligue 1'),
            ('soccer_netherlands_eredivisie', 'Eredivisie'),
        ]
        
        for sport, league_name in sports:
            print(f"   Fetching {league_name}...")
            matches = self.odds_fetcher.get_upcoming_matches(sport)
            
            if matches:
                print(f"      ✅ Found {len(matches)} matches")
                all_matches.extend(matches)
            else:
                print(f"      ⚠️ No matches found")
            
            time.sleep(0.5)  # Rate limiting
        
        if not all_matches:
            print("\n" + "="*60)
            print("❌ NO REAL MATCHES FOUND")
            print("="*60)
            print("\nPossible reasons:")
            print("1. No matches scheduled for today")
            print("2. API key is invalid or expired")
            print("3. API rate limit reached")
            print("\n💡 To fix:")
            print("   - Check your API key at https://the-odds-api.com")
            print("   - Or use manual input_matches.txt file")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_matches)
        
        # Remove matches with missing odds
        df = df[(df['home_odds'] > 0) & (df['draw_odds'] > 0) & (df['away_odds'] > 0)]
        
        print(f"\n✅ TOTAL {len(df)} REAL MATCHES READY FOR ANALYSIS")
        print(f"   Leagues: {df['league'].nunique()} different leagues")
        
        return df
