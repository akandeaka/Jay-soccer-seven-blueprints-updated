# Updated GlobalOddsFetcher class - Use known working league keys

class GlobalOddsFetcher:
    """
    Fetches football matches from The Odds API using known working league keys.
    """
    
    # Known working soccer league keys for The Odds API
    SOCCER_LEAGUE_KEYS = [
        "soccer_epl",                    # England Premier League
        "soccer_spain_la_liga",          # Spain La Liga
        "soccer_germany_bundesliga",     # Germany Bundesliga
        "soccer_italy_serie_a",          # Italy Serie A
        "soccer_france_ligue_one",       # France Ligue 1
        "soccer_netherlands_eredivisie", # Netherlands Eredivisie
        "soccer_portugal_primeira_liga", # Portugal Primeira Liga
        "soccer_belgium_first_div",      # Belgium First Division
        "soccer_scotland_premiership",   # Scotland Premiership
        "soccer_turkey_super_league",    # Turkey Super Lig
        "soccer_greece_super_league",    # Greece Super League
        "soccer_brazil_campeonato",      # Brazil Serie A
        "soccer_argentina_primera_division", # Argentina Primera Division
        "soccer_usa_mls",                # USA MLS
        "soccer_mexico_ligamx",          # Mexico Liga MX
        "soccer_australia_a_league",     # Australia A-League
        "soccer_japan_j1_league",        # Japan J1 League
        "soccer_south_korea_kleague1",   # South Korea K League 1
        "soccer_china_super_league",     # China Super League
        "soccer_uefa_champs_league",     # UEFA Champions League
        "soccer_uefa_europa_league",     # UEFA Europa League
        "soccer_uefa_europa_conference_league", # UEFA Europa Conference League
        "soccer_copa_libertadores",      # Copa Libertadores
        "soccer_copa_sudamericana",      # Copa Sudamericana
        "soccer_fifa_world_cup",         # FIFA World Cup
        "soccer_international_friendly", # International Friendlies
    ]
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_all_soccer_leagues(self) -> List[Dict]:
        """
        Return the hardcoded list of known soccer league keys.
        This bypasses the /sports endpoint which may not return soccer leagues.
        """
        leagues = []
        for league_key in self.SOCCER_LEAGUE_KEYS:
            leagues.append({
                "key": league_key,
                "title": league_key.replace("_", " ").title()
            })
        return leagues
    
    def fetch_all_matches(self, max_leagues: int = None, league_filter: List[str] = None) -> List[Match]:
        """
        Fetch matches from known working soccer leagues.
        """
        print("\n" + "="*80)
        print("GLOBAL SOCCER SCAN - USING KNOWN WORKING LEAGUE KEYS")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Get all soccer leagues from hardcoded list
        all_leagues = self.get_all_soccer_leagues()
        
        print(f"\n✓ Using {len(all_leagues)} known soccer league keys")
        
        # Apply filter if specified
        if league_filter:
            all_leagues = [l for l in all_leagues if l.get('key') in league_filter]
            print(f"   Filtered to {len(all_leagues)} leagues")
        
        if max_leagues:
            all_leagues = all_leagues[:max_leagues]
            print(f"   Limited to first {max_leagues} leagues")
        
        # Fetch matches for each league
        print("\n[Fetching matches from each league...]")
        all_matches = []
        
        for i, league in enumerate(all_leagues, 1):
            league_key = league.get('key', '')
            league_name = league.get('title', league_key)
            
            print(f"\n  [{i}/{len(all_leagues)}] {league_name}...")
            
            matches = self.fetch_matches_for_league(league_key, league_name)
            
            if matches:
                all_matches.extend(matches)
                print(f"    ✓ Found {len(matches)} matches")
            else:
                print(f"    ✗ No matches (no games today or league inactive)")
        
        # Summary
        print("\n" + "="*80)
        print("📊 SCAN SUMMARY")
        print("="*80)
        print(f"   Leagues scanned: {len(all_leagues)}")
        print(f"   Leagues with matches: {len([m for m in all_matches])}")
        print(f"   Total matches found: {len(all_matches)}")
        print("="*80)
        
        return all_matches
    
    def fetch_matches_for_league(self, league_key: str, league_name: str) -> List[Match]:
        """
        Fetch matches for a specific league.
        """
        matches = []
        
        try:
            url = f"{self.base_url}/sports/{league_key}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,uk,us,au",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                for event in data:
                    bookmakers = event.get("bookmakers", [])
                    if not bookmakers:
                        continue
                    
                    markets = bookmakers[0].get("markets", [])
                    if not markets:
                        continue
                    
                    outcomes = markets[0].get("outcomes", [])
                    
                    home_odds = None
                    draw_odds = None
                    away_odds = None
                    
                    home_team = event.get("home_team", "")
                    away_team = event.get("away_team", "")
                    
                    for outcome in outcomes:
                        if outcome.get("name") == home_team:
                            home_odds = outcome.get("price")
                        elif outcome.get("name") == "Draw":
                            draw_odds = outcome.get("price")
                        elif outcome.get("name") == away_team:
                            away_odds = outcome.get("price")
                    
                    if home_odds and draw_odds and away_odds:
                        commence_time = event.get("commence_time", "")
                        date = commence_time.split("T")[0] if commence_time else ""
                        time = commence_time.split("T")[1][:5] if commence_time and len(commence_time.split("T")) > 1 else ""
                        
                        match = Match(
                            league=league_name,
                            league_key=league_key,
                            home_team=home_team,
                            away_team=away_team,
                            home_odds=home_odds,
                            draw_odds=draw_odds,
                            away_odds=away_odds,
                            time=time,
                            date=date,
                            commence_time=commence_time,
                            bookmaker=bookmakers[0].get("key", "")
                        )
                        matches.append(match)
                
                # Track API usage
                remaining = response.headers.get("x-requests-remaining", "Unknown")
                print(f"      API Remaining: {remaining}")
                
            elif response.status_code == 404:
                print(f"      League key not recognized: {league_key}")
            else:
                print(f"      HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {e}")
        
        return matches
