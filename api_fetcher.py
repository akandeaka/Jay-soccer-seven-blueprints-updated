"""
API Fetcher - Automatically fetches match data and odds from APIs
No more manual copy/paste from Soccer24!
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import time


class OddsAPIFetcher:
    """
    Fetches live odds from The Odds API
    Provides: Home/Draw/Away odds, BTTS odds, Over/Under odds
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_upcoming_matches(self, sport: str = 'soccer_epl') -> List[Dict]:
        """
        Fetch all upcoming matches with odds for today
        Returns ONLY real data from API - NO DEMO DATA
        """
        if not self.api_key:
            print("⚠️ No API key found. Returning empty data.")
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
            data = response.json()
            
            # Check remaining requests (free tier has 500/month)
            remaining = response.headers.get('x-requests-remaining', 'N/A')
            print(f"📊 API requests remaining: {remaining}")
            
            matches = []
            for fixture in data:
                match_data = self._parse_fixture(fixture)
                if match_data:
                    matches.append(match_data)
            
            print(f"✅ Fetched {len(matches)} REAL matches from The Odds API")
            return matches
            
        except Exception as e:
            print(f"❌ Error fetching from Odds API: {e}")
            print("   No demo data will be generated. Check your API key.")
            return []
    
    def _parse_fixture(self, fixture: Dict) -> Optional[Dict]:
        """
        Parse a single fixture into the format your blueprint engine expects
        """
        try:
            # Extract teams
            home_team = fixture.get('home_team', '')
            away_team = fixture.get('away_team', '')
            
            if not home_team or not away_team:
                return None
            
            # Extract odds from bookmakers (use first bookmaker as primary)
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
            
            # Only return if we have minimum required odds
            if home_odds == 0 or draw_odds == 0 or away_odds == 0:
                return None
            
            # Get league name from sport title
            league = fixture.get('sport_title', 'Unknown').replace('Soccer - ', '')
            
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
            print(f"❌ Error parsing fixture: {e}")
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
            data = response.json()
            
            team_matches = []
            for match in data.get('matches', []):
                home = match.get('homeTeam', {}).get('name', '')
                away = match.get('awayTeam', {}).get('name', '')
                
                if team_name.lower() in home.lower() or team_name.lower() in away.lower():
                    home_score = match.get('score', {}).get('fullTime', {}).get('home', 0)
                    away_score = match.get('score', {}).get('fullTime', {}).get('away', 0)
                    
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
            
        except Exception as e:
            print(f"⚠️ Could not fetch form for {team_name}: {e}")
            return {'btts_record': None, 'form_score': 50}
    
    def get_btts_record_for_match(self, home_team: str, away_team: str, league: str) -> Optional[str]:
        """Get combined BTTS record for both teams"""
        home_form = self.get_team_form(home_team, league)
        away_form = self.get_team_form(away_team, league)
        
        if home_form['btts_record'] and away_form['btts_record']:
            # Return the better record
            return max(home_form['btts_record'], away_form['btts_record'])
        elif home_form['btts_record']:
            return home_form['btts_record']
        elif away_form['btts_record']:
            return away_form['btts_record']
        else:
            return None


class APIDataManager:
    """Main data manager that orchestrates both APIs"""
    
    def __init__(self):
        self.odds_fetcher = OddsAPIFetcher(os.getenv('ODDS_API_KEY', ''))
        self.stats_fetcher = FootballDataFetcher(os.getenv('FOOTBALL_DATA_API_KEY', ''))
    
    def get_todays_matches(self) -> pd.DataFrame:
        """Get all matches for today with complete data - REAL DATA ONLY"""
        all_matches = []
        
        sports = [
            'soccer_epl', 
            'soccer_spain_la_liga', 
            'soccer_germany_bundesliga', 
            'soccer_italy_serie_a', 
            'soccer_france_ligue_one', 
            'soccer_netherlands_eredivisie'
        ]
        
        for sport in sports:
            matches = self.odds_fetcher.get_upcoming_matches(sport)
            all_matches.extend(matches)
            time.sleep(0.5)
        
        if not all_matches:
            print("❌ No real matches fetched from API.")
            print("   Possible reasons:")
            print("   1. No API key configured")
            print("   2. No matches scheduled for today")
            print("   3. API rate limit reached")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_matches)
        df = df[(df['home_odds'] > 0) & (df['draw_odds'] > 0) & (df['away_odds'] > 0)]
        
        print(f"✅ Total {len(df)} REAL matches ready for blueprint analysis")
        return df
