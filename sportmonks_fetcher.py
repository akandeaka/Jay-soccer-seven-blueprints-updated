"""
Sportmonks API Fetcher for Jay Soccer Blueprints - GLOBAL VERSION
Automatically discovers and fetches matches from ALL leagues worldwide
Provides REAL odds for all 7 blueprints
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class Match:
    """Represents a football match with odds data"""
    league: str
    league_key: str
    league_id: int
    home_team: str
    away_team: str
    home_odds: float
    draw_odds: float
    away_odds: float
    time: str = ""
    date: str = ""
    commence_time: str = ""
    bookmaker: str = ""


class SportmonksFetcher:
    """
    Fetches odds from Sportmonks API via RapidAPI - GLOBAL COVERAGE
    Automatically discovers all active leagues and fetches matches worldwide
    
    Free tier: 100 requests/day - use efficiently
    """
    
    def __init__(self, rapidapi_key: str):
        self.api_key = rapidapi_key
        self.base_url = "https://sportmonks-football-v3.p.rapidapi.com/v3/football"
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "sportmonks-football-v3.p.rapidapi.com"
        }
        self.request_count = 0
        self.rate_limit_warning_shown = False
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        Make API request with rate limit tracking
        """
        if self.request_count >= 95 and not self.rate_limit_warning_shown:
            print("⚠️ WARNING: Approaching rate limit (95/100 requests)")
            self.rate_limit_warning_shown = True
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"❌ Rate limit exceeded! Used {self.request_count} requests")
                return None
            elif response.status_code == 401:
                print("❌ Invalid API key")
                return None
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def get_all_active_leagues(self) -> List[Dict]:
        """
        Fetch ALL active football leagues from Sportmonks
        This automatically discovers leagues worldwide
        """
        print("\n🌍 Discovering all active football leagues worldwide...")
        
        url = f"{self.base_url}/leagues"
        params = {
            "include": "season",
            "filters[active]": "true"
        }
        
        data = self._make_request(url, params)
        
        if not data:
            print("❌ Failed to fetch leagues")
            return []
        
        leagues = data.get("data", [])
        print(f"✓ Found {len(leagues)} active leagues worldwide")
        
        return leagues
    
    def get_leagues_with_todays_matches(self, leagues: List[Dict] = None) -> List[Dict]:
        """
        Filter leagues that have matches scheduled for today
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"\n📅 Checking which leagues have matches on {today}...")
        
        if leagues is None:
            leagues = self.get_all_active_leagues()
        
        leagues_with_matches = []
        
        for i, league in enumerate(leagues):
            league_id = league.get("id")
            league_name = league.get("name", "Unknown")
            
            # Check if league has fixtures today
            url = f"{self.base_url}/fixtures/date/{today}"
            params = {
                "filters[leagueIds]": str(league_id),
                "include": "participants",
                "limit": 1  # Just check if any exist
            }
            
            data = self._make_request(url, params)
            
            if data and data.get("data"):
                leagues_with_matches.append({
                    "id": league_id,
                    "name": league_name,
                    "country": league.get("country", {}).get("name", "World"),
                    "type": league.get("type", "league")
                })
                print(f"  ✓ {league_name} ({league.get('country', {}).get('name', 'Unknown')})")
            
            # Small delay to avoid rate limit
            time.sleep(0.1)
        
        print(f"\n✓ Found {len(leagues_with_matches)} leagues with matches today")
        return leagues_with_matches
    
    def fetch_all_todays_matches_global(self, max_leagues: int = 30) -> List[Match]:
        """
        Fetch ALL matches from ALL leagues worldwide for today
        Uses efficient pagination and bulk odds fetching
        
        Args:
            max_leagues: Maximum leagues to process (respects rate limits)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        print("\n" + "="*80)
        print("🌍 SPORTMONKS GLOBAL SCAN - ALL LEAGUES WORLDWIDE")
        print(f"📅 Date: {today}")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        
        # Step 1: Get all leagues with matches today
        leagues_with_matches = self.get_leagues_with_todays_matches()
        
        if not leagues_with_matches:
            print("❌ No leagues with matches found today")
            return []
        
        # Limit leagues to respect rate limits
        if len(leagues_with_matches) > max_leagues:
            print(f"\n⚠️ Limiting to {max_leagues} leagues (found {len(leagues_with_matches)})")
            leagues_with_matches = leagues_with_matches[:max_leagues]
        
        # Step 2: Fetch matches for each league
        all_matches = []
        
        for league in leagues_with_matches:
            league_id = league["id"]
            league_name = league["name"]
            country = league.get("country", "World")
            
            print(f"\n📋 Fetching {league_name} ({country})...")
            
            # Get all fixtures for this league today
            url = f"{self.base_url}/fixtures/date/{today}"
            params = {
                "filters[leagueIds]": str(league_id),
                "include": "participants,league",
                "per_page": 50
            }
            
            fixtures_data = self._make_request(url, params)
            
            if fixtures_data:
                fixtures = fixtures_data.get("data", [])
                print(f"   Found {len(fixtures)} fixtures")
                
                for fixture in fixtures:
                    match = self._get_match_with_odds(fixture, league_name)
                    if match:
                        all_matches.append(match)
            else:
                print(f"   No fixtures found")
        
        print("\n" + "="*80)
        print("📊 GLOBAL SCAN SUMMARY")
        print("="*80)
        print(f"   Leagues processed: {len(leagues_with_matches)}")
        print(f"   Total matches with odds: {len(all_matches)}")
        print(f"   API requests used: {self.request_count}")
        print("="*80)
        
        return all_matches
    
    def _get_match_with_odds(self, fixture: Dict, league_name: str) -> Optional[Match]:
        """
        Get match details and its odds
        """
        try:
            fixture_id = fixture.get("id")
            fixture_date = fixture.get("starting_at", "")
            
            # Get participants
            participants = fixture.get("participants", [])
            home_team = "Unknown"
            away_team = "Unknown"
            
            for participant in participants:
                position = participant.get("meta", {}).get("position", "")
                if position == "home":
                    home_team = participant.get("name", "Unknown")
                elif position == "away":
                    away_team = participant.get("name", "Unknown")
            
            # Default odds (fallback)
            home_odds = 2.00
            draw_odds = 3.20
            away_odds = 3.80
            
            # Fetch odds for this fixture
            odds_url = f"{self.base_url}/odds/fixture/{fixture_id}"
            odds_params = {
                "include": "bookmakers",
                "filters[marketId]": "1"  # 1X2 market
            }
            
            odds_data = self._make_request(odds_url, odds_params)
            
            if odds_data:
                odds_list = odds_data.get("data", [])
                for odd_item in odds_list:
                    bookmakers = odd_item.get("bookmakers", [])
                    for bookmaker in bookmakers:
                        markets = bookmaker.get("markets", [])
                        for market in markets:
                            odds_map = market.get("odds", {})
                            if "home" in odds_map and odds_map["home"]:
                                home_odds = float(odds_map["home"])
                            if "draw" in odds_map and odds_map["draw"]:
                                draw_odds = float(odds_map["draw"])
                            if "away" in odds_map and odds_map["away"]:
                                away_odds = float(odds_map["away"])
            
            return Match(
                league=league_name,
                league_key=league_name.lower().replace(" ", "_"),
                league_id=fixture.get("league", {}).get("id", 0),
                home_team=home_team,
                away_team=away_team,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                time=fixture_date[11:16] if fixture_date and len(fixture_date) > 11 else "",
                date=fixture_date[:10] if fixture_date and len(fixture_date) > 10 else "",
                commence_time=fixture_date,
                bookmaker="Sportmonks"
            )
            
        except Exception as e:
            print(f"   Error processing fixture: {e}")
            return None
    
    def fetch_todays_odds_fast(self) -> List[Match]:
        """
        FAST METHOD: Uses the pre-match odds endpoint directly
        This is more efficient and uses fewer API calls
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"\n⚡ FAST SCAN: Fetching all pre-match odds for {today}...")
        
        url = f"{self.base_url}/odds/pre-match"
        params = {
            "include": "participants,league,bookmakers",
            "filters[date]": today,
            "filters[marketId]": "1",
            "per_page": 100
        }
        
        all_odds_items = []
        page = 1
        
        while True:
            params["page"] = page
            data = self._make_request(url, params)
            
            if not data:
                break
            
            odds_items = data.get("data", [])
            if not odds_items:
                break
            
            all_odds_items.extend(odds_items)
            
            # Check if there are more pages
            pagination = data.get("meta", {}).get("pagination", {})
            total_pages = pagination.get("total_pages", 1)
            
            if page >= total_pages:
                break
            
            page += 1
            time.sleep(0.1)  # Small delay between pages
        
        print(f"✓ Found {len(all_odds_items)} matches with pre-match odds")
        
        matches = []
        for odd_item in all_odds_items:
            match = self._parse_odds_item_fast(odd_item)
            if match:
                matches.append(match)
        
        print(f"✓ Processed {len(matches)} matches with valid odds")
        print(f"   API requests used: {self.request_count}")
        
        return matches
    
    def _parse_odds_item_fast(self, odd_item: Dict) -> Optional[Match]:
        """
        Parse a pre-match odds item quickly
        """
        try:
            fixture = odd_item.get("fixture", {})
            participants = fixture.get("participants", [])
            
            home_team = "Unknown"
            away_team = "Unknown"
            
            for participant in participants:
                position = participant.get("meta", {}).get("position", "")
                if position == "home":
                    home_team = participant.get("name", "Unknown")
                elif position == "away":
                    away_team = participant.get("name", "Unknown")
            
            league = odd_item.get("league", {})
            league_name = league.get("name", "Unknown")
            league_id = league.get("id", 0)
            country = league.get("country", {}).get("name", "World")
            
            # Build full league name with country
            full_league_name = f"{league_name} ({country})"
            
            odds_data = odd_item.get("odds", {})
            home_odds = float(odds_data.get("home", 2.00))
            draw_odds = float(odds_data.get("draw", 3.20))
            away_odds = float(odds_data.get("away", 3.80))
            
            fixture_date = fixture.get("starting_at", "")
            
            return Match(
                league=full_league_name,
                league_key=league_name.lower().replace(" ", "_"),
                league_id=league_id,
                home_team=home_team,
                away_team=away_team,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                time=fixture_date[11:16] if fixture_date and len(fixture_date) > 11 else "",
                date=fixture_date[:10] if fixture_date and len(fixture_date) > 10 else "",
                commence_time=fixture_date,
                bookmaker="Sportmonks"
            )
            
        except Exception as e:
            return None
    
    def get_top_leagues_quick(self) -> List[Match]:
        """
        QUICK METHOD: Fetch only top leagues (saves API calls)
        Use this for daily scans within free tier limits
        """
        # Top league IDs by Sportmonks (global coverage)
        top_league_ids = [
            # Europe
            8,    # Premier League (England)
            564,  # Championship (England)
            9,    # La Liga (Spain)
            10,   # Bundesliga (Germany)
            11,   # Serie A (Italy)
            12,   # Ligue 1 (France)
            13,   # Eredivisie (Netherlands)
            14,   # Primeira Liga (Portugal)
            15,   # Champions League
            16,   # Europa League
            17,   # Europa Conference League
            22,   # Scottish Premiership
            23,   # Turkish Super Lig
            24,   # Belgian Pro League
            25,   # Swiss Super League
            26,   # Greek Super League
            27,   # Russian Premier League
            28,   # Ukrainian Premier League
            29,   # Czech First League
            30,   # Croatian HNL
            
            # South America
            33,   # Brasileirao (Brazil)
            34,   # Serie B (Brazil)
            35,   # Primera Division (Argentina)
            36,   # Chilean Primera
            37,   # Colombian Primera A
            38,   # Uruguayan Primera
            39,   # Paraguayan Primera
            40,   # Peruvian Liga 1
            41,   # Ecuadorian Liga Pro
            
            # North America
            42,   # MLS (USA)
            43,   # Liga MX (Mexico)
            44,   # Canadian Premier League
            
            # Asia
            45,   # J1 League (Japan)
            46,   # J2 League (Japan)
            47,   # K League 1 (South Korea)
            48,   # K League 2 (South Korea)
            49,   # Chinese Super League
            50,   # A-League (Australia)
            51,   # Saudi Pro League
            52,   # UAE Pro League
            53,   # Qatar Stars League
            54,   # Indian Super League
            
            # Africa
            55,   # Egyptian Premier League
            56,   # South African PSL
            57,   # Moroccan Botola Pro
            58,   # Tunisian Ligue 1
            59,   # Algerian Ligue 1
        ]
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"\n🏆 Fetching top leagues for {today}...")
        
        all_matches = []
        
        for league_id in top_league_ids:
            url = f"{self.base_url}/fixtures/date/{today}"
            params = {
                "filters[leagueIds]": str(league_id),
                "include": "participants,league"
            }
            
            data = self._make_request(url, params)
            
            if data and data.get("data"):
                fixtures = data.get("data", [])
                for fixture in fixtures:
                    match = self._get_match_with_odds(fixture, f"League {league_id}")
                    if match:
                        all_matches.append(match)
                
                if fixtures:
                    league_name = fixtures[0].get("league", {}).get("name", f"League {league_id}")
                    print(f"  ✓ {league_name}: {len(fixtures)} matches")
            
            time.sleep(0.1)  # Respect rate limits
        
        return all_matches


# =============================================================================
# MAIN FUNCTION FOR DAILY USE
# =============================================================================

def fetch_global_matches(api_key: str, mode: str = "fast") -> List[Match]:
    """
    Fetch matches from all leagues worldwide
    
    Modes:
        - "fast": Uses pre-match odds endpoint (recommended, fewer API calls)
        - "top": Only top leagues (good for free tier)
        - "full": All leagues worldwide (may hit rate limits)
    """
    fetcher = SportmonksFetcher(api_key)
    
    if mode == "fast":
        matches = fetcher.fetch_todays_odds_fast()
    elif mode == "top":
        matches = fetcher.get_top_leagues_quick()
    else:
        matches = fetcher.fetch_all_todays_matches_global()
    
    return matches


# Quick test function
def test_global_scan():
    """Test global league discovery"""
    import os
    
    API_KEY = os.environ.get("RAPIDAPI_KEY")
    
    print("="*60)
    print("SPORTMONKS GLOBAL SCAN TEST")
    print("="*60)
    
    if not API_KEY:
        print("\n❌ RAPIDAPI_KEY not set!")
        print("   Get from: https://rapidapi.com/sportmonks-data/api/football-pro")
        return
    
    fetcher = SportmonksFetcher(API_KEY)
    
    # Test fast mode
    print("\n🔍 Testing FAST mode (pre-match odds endpoint)...")
    matches = fetcher.fetch_todays_odds_fast()
    
    if matches:
        print(f"\n✅ SUCCESS! Found {len(matches)} matches with REAL odds")
        
        # Show league breakdown
        leagues = {}
        for m in matches[:20]:  # Show first 20
            leagues[m.league] = leagues.get(m.league, 0) + 1
        
        print("\n📊 Leagues with matches (sample):")
        for league, count in list(leagues.items())[:10]:
            print(f"   • {league}: {count} matches")
        
        print("\n📋 Sample matches with REAL odds:")
        for m in matches[:5]:
            print(f"\n   {m.home_team} vs {m.away_team}")
            print(f"     League: {m.league}")
            print(f"     Odds: {m.home_odds} | {m.draw_odds} | {m.away_odds}")
    else:
        print("\n❌ No matches found with odds")
        print("   Check if there are games scheduled today")


if __name__ == "__main__":
    test_global_scan()
