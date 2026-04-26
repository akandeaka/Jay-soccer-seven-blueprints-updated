"""
Alternate odds fetcher using API-Football (RapidAPI)
This definitely provides soccer data
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Match:
    """Represents a football match with odds data"""
    league: str
    league_key: str
    home_team: str
    away_team: str
    home_odds: float
    draw_odds: float
    away_odds: float
    time: str = ""
    date: str = ""
    commence_time: str = ""
    bookmaker: str = ""


class APIFootballFetcher:
    """
    Fetches odds from API-Football (RapidAPI)
    This is the recommended alternative since The Odds API isn't returning soccer
    """
    
    def __init__(self, rapidapi_key: str):
        self.api_key = rapidapi_key
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
    
    def fetch_todays_matches(self) -> List[Match]:
        """
        Fetch all matches for today
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"\nFetching matches for {today} from API-Football...")
        
        url = f"{self.base_url}/fixtures"
        params = {"date": today}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])
                print(f"✓ Found {len(fixtures)} fixtures")
                
                matches = []
                for fixture in fixtures:
                    match = self._parse_fixture(fixture)
                    if match:
                        matches.append(match)
                
                return matches
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def fetch_matches_with_odds(self) -> List[Match]:
        """
        Fetch matches that have odds available
        """
        url = f"{self.base_url}/odds"
        params = {"date": datetime.now().strftime("%Y-%m-%d")}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                odds_data = data.get("response", [])
                print(f"✓ Found {len(odds_data)} matches with odds")
                
                matches = []
                for odd_item in odds_data:
                    match = self._parse_odds(odd_item)
                    if match:
                        matches.append(match)
                
                return matches
            else:
                print(f"❌ API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def _parse_fixture(self, fixture: Dict) -> Optional[Match]:
        """Parse a fixture into a Match object"""
        try:
            league = fixture.get("league", {})
            teams = fixture.get("teams", {})
            home = teams.get("home", {})
            away = teams.get("away", {})
            fixture_date = fixture.get("fixture", {}).get("date", "")
            
            # For odds, we need to fetch separately or use default values
            # This is a simplified version - you'll want to fetch odds endpoint
            return Match(
                league=league.get("name", "Unknown"),
                league_key=league.get("name", "").lower().replace(" ", "_"),
                home_team=home.get("name", "Unknown"),
                away_team=away.get("name", "Unknown"),
                home_odds=2.00,  # Placeholder - fetch from odds endpoint
                draw_odds=3.00,  # Placeholder - fetch from odds endpoint
                away_odds=4.00,  # Placeholder - fetch from odds endpoint
                time=fixture_date[11:16] if fixture_date else "",
                date=fixture_date[:10] if fixture_date else "",
                commence_time=fixture_date
            )
        except Exception as e:
            print(f"Error parsing fixture: {e}")
            return None
    
    def _parse_odds(self, odd_item: Dict) -> Optional[Match]:
        """Parse odds data into a Match object"""
        try:
            fixture = odd_item.get("fixture", {})
            bookmakers = odd_item.get("bookmakers", [])
            
            if not bookmakers:
                return None
            
            # Get first bookmaker's odds
            bookmaker = bookmakers[0]
            bets = bookmaker.get("bets", [])
            
            # Find the match winner market
            match_winner_bet = None
            for bet in bets:
                if bet.get("name") == "Match Winner":
                    match_winner_bet = bet
                    break
            
            if not match_winner_bet:
                return None
            
            values = match_winner_bet.get("values", [])
            home_odds = None
            draw_odds = None
            away_odds = None
            
            for value in values:
                outcome = value.get("value")
                odd = value.get("odd")
                if outcome == "Home":
                    home_odds = float(odd) if odd else None
                elif outcome == "Draw":
                    draw_odds = float(odd) if odd else None
                elif outcome == "Away":
                    away_odds = float(odd) if odd else None
            
            if home_odds and draw_odds and away_odds:
                league = odd_item.get("league", {})
                teams = fixture.get("teams", {})
                home = teams.get("home", {})
                away = teams.get("away", {})
                fixture_date = fixture.get("date", "")
                
                return Match(
                    league=league.get("name", "Unknown"),
                    league_key=league.get("name", "").lower().replace(" ", "_"),
                    home_team=home.get("name", "Unknown"),
                    away_team=away.get("name", "Unknown"),
                    home_odds=home_odds,
                    draw_odds=draw_odds,
                    away_odds=away_odds,
                    time=fixture_date[11:16] if fixture_date else "",
                    date=fixture_date[:10] if fixture_date else "",
                    commence_time=fixture_date,
                    bookmaker=bookmaker.get("name", "")
                )
            
            return None
            
        except Exception as e:
            print(f"Error parsing odds: {e}")
            return None


# Quick test function
def test_apifootball():
    """Test API-Football connection"""
    import os
    
    API_KEY = os.environ.get("RAPIDAPI_KEY")
    
    if not API_KEY:
        print("❌ RAPIDAPI_KEY environment variable not set")
        print("   Get a free key from: https://rapidapi.com/api-sports-api/api/api-football/")
        return
    
    fetcher = APIFootballFetcher(API_KEY)
    matches = fetcher.fetch_todays_matches()
    
    print(f"\n✓ Found {len(matches)} matches today")
    
    if matches:
        print("\nFirst 5 matches:")
        for m in matches[:5]:
            print(f"  {m.home_team} vs {m.away_team} ({m.league})")
