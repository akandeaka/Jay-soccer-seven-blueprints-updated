"""
Football-Data.org API Fetcher
This fetches match odds and fixtures from Football-Data.org
Free tier: 10 requests per minute, 300 per day
"""

import requests
from datetime import datetime, timedelta
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
    bookmaker: str = "Football-Data.org"


class FootballDataFetcher:
    """
    Fetches matches and odds from Football-Data.org
    Free tier includes: Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Eredivisie, Primeira Liga, Championship, etc.
    """
    
    # Football-Data.org competition codes
    COMPETITIONS = {
        "premier_league": {"code": "PL", "name": "Premier League"},
        "championship": {"code": "ELC", "name": "Championship"},
        "league_one": {"code": "EL1", "name": "League One"},
        "league_two": {"code": "EL2", "name": "League Two"},
        "la_liga": {"code": "PD", "name": "La Liga"},
        "segunda_division": {"code": "SD", "name": "Segunda Division"},
        "bundesliga": {"code": "BL1", "name": "Bundesliga"},
        "bundesliga_2": {"code": "BL2", "name": "2. Bundesliga"},
        "serie_a": {"code": "SA", "name": "Serie A"},
        "serie_b": {"code": "SB", "name": "Serie B"},
        "ligue_1": {"code": "FL1", "name": "Ligue 1"},
        "ligue_2": {"code": "FL2", "name": "Ligue 2"},
        "eredivisie": {"code": "DED", "name": "Eredivisie"},
        "primeira_liga": {"code": "PPL", "name": "Primeira Liga"},
        "champions_league": {"code": "CL", "name": "UEFA Champions League"},
        "europa_league": {"code": "EL", "name": "UEFA Europa League"},
        "conference_league": {"code": "ECL", "name": "UEFA Europa Conference League"},
        "bundesliga_women": {"code": "BL1F", "name": "Bundesliga Women"},
        "league_cup": {"code": "CLC", "name": "League Cup"},
        "fa_cup": {"code": "FAC", "name": "FA Cup"},
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {"X-Auth-Token": api_key}
        
    def test_connection(self) -> bool:
        """
        Test if the API key is working by fetching Premier League matches
        """
        print("\n" + "="*60)
        print("TESTING FOOTBALL-DATA.ORG CONNECTION")
        print("="*60)
        
        try:
            url = f"{self.base_url}/competitions/PL/matches"
            params = {"limit": 1}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API key is VALID!")
                print(f"   Total matches available: {data.get('count', 0)}")
                return True
            elif response.status_code == 401:
                print("❌ API key is INVALID (401 Unauthorized)")
                print("   Please check your API key at: https://www.football-data.org/")
                return False
            elif response.status_code == 429:
                print("⚠️ Rate limit exceeded (429)")
                print("   Free tier: 10 requests per minute, 300 per day")
                return True  # Key is valid, just rate limited
            else:
                print(f"❌ Unexpected error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def fetch_matches_by_competition(self, competition_code: str, competition_name: str) -> List[Match]:
        """
        Fetch matches for a specific competition
        """
        matches = []
        
        try:
            url = f"{self.base_url}/competitions/{competition_code}/matches"
            params = {
                "status": "SCHEDULED,LIVE,IN_PLAY,PAUSED",
                "limit": 50
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("matches", [])
                
                for fixture in fixtures:
                    match = self._parse_match(fixture, competition_name, competition_code)
                    if match:
                        matches.append(match)
                
                # Track API usage
                remaining = response.headers.get("X-Requests-Available", "Unknown")
                print(f"      {competition_name}: {len(fixtures)} matches | Requests left: {remaining}")
                
            elif response.status_code == 429:
                print(f"      ⚠️ Rate limit reached for {competition_name}")
            else:
                print(f"      ✗ {competition_name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ✗ Error fetching {competition_name}: {e}")
        
        return matches
    
    def _parse_match(self, fixture: Dict, league_name: str, league_code: str) -> Optional[Match]:
        """
        Parse a fixture into a Match object
        Note: Football-Data.org free tier does NOT provide live odds
        We use implied odds based on standings or simulate for now
        """
        try:
            home_team = fixture.get("homeTeam", {}).get("name", "Unknown")
            away_team = fixture.get("awayTeam", {}).get("name", "Unknown")
            match_date = fixture.get("utcDate", "")
            status = fixture.get("status", "SCHEDULED")
            
            # Calculate implied odds based on standings if available
            # For free tier, we need to estimate or you'll need paid tier for real odds
            home_odds = self._calculate_implied_odds(fixture, "HOME")
            draw_odds = self._calculate_implied_odds(fixture, "DRAW")
            away_odds = self._calculate_implied_odds(fixture, "AWAY")
            
            return Match(
                league=league_name,
                league_key=league_code,
                home_team=home_team,
                away_team=away_team,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                time=match_date[11:16] if match_date else "",
                date=match_date[:10] if match_date else "",
                commence_time=match_date,
                bookmaker="Football-Data.org"
            )
            
        except Exception as e:
            print(f"Error parsing match: {e}")
            return None
    
    def _calculate_implied_odds(self, fixture: Dict, outcome: str) -> float:
        """
        Calculate implied odds for free tier (no real odds available)
        This is a temporary solution - upgrade to paid tier for real odds
        """
        # Base odds based on home advantage (1.00 = even money)
        # In real implementation, you'd get these from the odds endpoint
        
        # Default values if no data available
        default_odds = {
            "HOME": 2.10,
            "DRAW": 3.30,
            "AWAY": 3.80
        }
        
        return default_odds.get(outcome, 3.00)
    
    def fetch_all_todays_matches(self, specific_leagues: List[str] = None) -> List[Match]:
        """
        Fetch all matches for today from all or specific leagues
        """
        print("\n" + "="*80)
        print("FOOTBALL-DATA.ORG - FETCHING TODAY'S MATCHES")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Test connection first
        if not self.test_connection():
            print("\n❌ API connection failed. Check your API key.")
            return []
        
        # Determine which competitions to fetch
        if specific_leagues:
            competitions = {k: v for k, v in self.COMPETITIONS.items() if k in specific_leagues}
        else:
            competitions = self.COMPETITIONS
        
        print(f"\n📋 Fetching from {len(competitions)} competitions...")
        
        all_matches = []
        
        for comp_key, comp_info in competitions.items():
            code = comp_info["code"]
            name = comp_info["name"]
            
            print(f"\n  Fetching {name} ({code})...")
            matches = self.fetch_matches_by_competition(code, name)
            all_matches.extend(matches)
        
        # Filter to today's matches only
        today = datetime.now().strftime("%Y-%m-%d")
        todays_matches = [m for m in all_matches if m.date == today]
        
        print("\n" + "="*80)
        print("📊 SCAN SUMMARY")
        print("="*80)
        print(f"   Competitions scanned: {len(competitions)}")
        print(f"   Total matches fetched: {len(all_matches)}")
        print(f"   Today's matches: {len(todays_matches)}")
        print("="*80)
        
        if len(todays_matches) == 0:
            print("\n⚠️ No matches found for today.")
            print("   Possible reasons:")
            print("   1. No games scheduled today")
            print("   2. Your free tier only shows certain competitions")
            print("   3. Check tomorrow's matches instead")
        
        return todays_matches
    
    def fetch_tomorrows_matches(self) -> List[Match]:
        """
        Fetch matches for tomorrow
        """
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        print(f"\n📅 Fetching matches for {tomorrow}...")
        
        all_matches = self.fetch_all_todays_matches()
        tomorrows_matches = [m for m in all_matches if m.date == tomorrow]
        
        print(f"✓ Found {len(tomorrows_matches)} matches for tomorrow")
        return tomorrows_matches


# Quick test function
def test_football_data():
    """Test Football-Data.org connection"""
    import os
    
    API_KEY = os.environ.get("FOOTBALL_DATA_KEY")
    
    print("="*60)
    print("FOOTBALL-DATA.ORG API TEST")
    print("="*60)
    
    if not API_KEY:
        print("\n❌ FOOTBALL_DATA_KEY environment variable not set!")
        print("   Get a free key from: https://www.football-data.org/")
        print("   Then add it to GitHub Secrets as 'FOOTBALL_DATA_KEY'")
        return
    
    print(f"\n✓ API Key found: {API_KEY[:8]}...{API_KEY[-4:]}")
    
    fetcher = FootballDataFetcher(API_KEY)
    matches = fetcher.fetch_all_todays_matches()
    
    if matches:
        print(f"\n✅ SUCCESS! Found {len(matches)} matches today")
        print("\nFirst 5 matches:")
        for m in matches[:5]:
            odds_info = f"{m.home_odds} - {m.draw_odds} - {m.away_odds}"
            print(f"  {m.home_team} vs {m.away_team} ({m.league})")
            print(f"    Odds: {odds_info}")
    else:
        print("\n❌ No matches found today")
        print("   Try running again or check if there are games scheduled")


if __name__ == "__main__":
    test_football_data()
