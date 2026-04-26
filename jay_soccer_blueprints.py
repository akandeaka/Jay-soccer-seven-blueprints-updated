"""
JAY SOCCER PREDICTION SYSTEM - THE 7 MASTER BLUEPRINTS
Version: 4.0 - GLOBAL DAILY COVERAGE
Covers ALL football matches worldwide for any given day
Based strictly on the provided blueprints - no additions or deletions
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


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


@dataclass
class BlueprintResult:
    """Result of applying a blueprint to a match"""
    match: Match
    blueprint_number: int
    blueprint_name: str
    target_market: str
    risk_level: str
    qualifies: bool
    reason: str = ""


class JaySoccerBlueprints:
    """
    Implementation of the 7 Master Blueprints for soccer prediction.
    Each blueprint contains strict trigger conditions exactly as defined.
    """
    
    def __init__(self):
        self.results: List[BlueprintResult] = []
        
    # =========================================================================
    # BLUEPRINT 1: THE ELITE HOME BANKER
    # =========================================================================
    def blueprint_1_elite_home_banker(self, match: Match) -> Optional[BlueprintResult]:
        """
        Trigger Odds: Home (1.20 – 1.29)
        Mandatory Clause: Away Odds must be 10.0 or higher
        Target Market: Straight Home Win
        Risk Level: Ultra-Low
        """
        home_range_min = 1.20
        home_range_max = 1.29
        away_min = 10.0
        
        home_in_range = home_range_min <= match.home_odds <= home_range_max
        away_meets = match.away_odds >= away_min
        
        if home_in_range and away_meets:
            return BlueprintResult(
                match=match,
                blueprint_number=1,
                blueprint_name="THE ELITE HOME BANKER",
                target_market="Straight Home Win",
                risk_level="Ultra-Low",
                qualifies=True,
                reason=f"Home odds {match.home_odds} in [{home_range_min}-{home_range_max}] & Away odds {match.away_odds} >= {away_min}"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 2: THE PRIMARY FAVORITE
    # =========================================================================
    def blueprint_2_primary_favorite(self, match: Match) -> Optional[BlueprintResult]:
        """
        Trigger Odds: Home (1.30 – 1.36)
        Mandatory Clause: Away Odds must be 9.0 or higher
        Target Market: Home Winning (Straight Win)
        Risk Level: Low
        """
        home_range_min = 1.30
        home_range_max = 1.36
        away_min = 9.0
        
        home_in_range = home_range_min <= match.home_odds <= home_range_max
        away_meets = match.away_odds >= away_min
        
        if home_in_range and away_meets:
            return BlueprintResult(
                match=match,
                blueprint_number=2,
                blueprint_name="THE PRIMARY FAVORITE",
                target_market="Home Winning (Straight Win)",
                risk_level="Low",
                qualifies=True,
                reason=f"Home odds {match.home_odds} in [{home_range_min}-{home_range_max}] & Away odds {match.away_odds} >= {away_min}"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 3: THE MODERATE FAVORITE SAFETY
    # =========================================================================
    def blueprint_3_moderate_favorite_safety(self, match: Match) -> Optional[BlueprintResult]:
        """
        Trigger Odds: Home (1.30 – 1.36)
        Mandatory Clause: Away Odds are moderate (7.0 – 8.99)
        Target Market: 1X & Over 1.5 Goals
        Risk Level: Low-Moderate (Safety Net Applied)
        """
        home_range_min = 1.30
        home_range_max = 1.36
        away_min = 7.0
        away_max = 8.99
        
        home_in_range = home_range_min <= match.home_odds <= home_range_max
        away_in_range = away_min <= match.away_odds <= away_max
        
        if home_in_range and away_in_range:
            return BlueprintResult(
                match=match,
                blueprint_number=3,
                blueprint_name="THE MODERATE FAVORITE SAFETY",
                target_market="1X & Over 1.5 Goals",
                risk_level="Low-Moderate (Safety Net Applied)",
                qualifies=True,
                reason=f"Home odds {match.home_odds} in [{home_range_min}-{home_range_max}] & Away odds {match.away_odds} in [{away_min}-{away_max}]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 4: THE GOAL ENGINE
    # =========================================================================
    def blueprint_4_goal_engine(self, match: Match) -> Optional[BlueprintResult]:
        """
        Trigger Odds: Home (1.72 – 1.80)
        The Clause: Independent of Away odds; signals high offensive output.
        Target Market: Over 1.5 Goals
        Risk Level: Moderate
        """
        home_range_min = 1.72
        home_range_max = 1.80
        
        home_in_range = home_range_min <= match.home_odds <= home_range_max
        
        if home_in_range:
            return BlueprintResult(
                match=match,
                blueprint_number=4,
                blueprint_name="THE GOAL ENGINE",
                target_market="Over 1.5 Goals",
                risk_level="Moderate",
                qualifies=True,
                reason=f"Home odds {match.home_odds} in [{home_range_min}-{home_range_max}] (Independent of away odds)"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 5: THE DEFENSIVE TRAP
    # =========================================================================
    def blueprint_5_defensive_trap(self, match: Match) -> Optional[BlueprintResult]:
        """
        Trigger Odds: Home (1.90 – 2.02)
        The Clause: High home price indicates a struggle to break down the opponent.
        Target Market: 1X & Under 3.5 FT
        Risk Level: Moderate (Value Pick)
        """
        home_range_min = 1.90
        home_range_max = 2.02
        
        home_in_range = home_range_min <= match.home_odds <= home_range_max
        
        if home_in_range:
            return BlueprintResult(
                match=match,
                blueprint_number=5,
                blueprint_name="THE DEFENSIVE TRAP",
                target_market="1X & Under 3.5 FT",
                risk_level="Moderate (Value Pick)",
                qualifies=True,
                reason=f"Home odds {match.home_odds} in [{home_range_min}-{home_range_max}]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 6: THE STRONG DRAW
    # =========================================================================
    def blueprint_6_strong_draw(self, match: Match) -> Optional[BlueprintResult]:
        """
        Trigger Odds: Draw (2.75 – 3.39)
        The Clause: Focus is strictly on the Draw column alignment.
        Target Market: Full Time Draw (X) Potential
        Risk Level: High (Strategic)
        """
        draw_range_min = 2.75
        draw_range_max = 3.39
        
        draw_in_range = draw_range_min <= match.draw_odds <= draw_range_max
        
        if draw_in_range:
            return BlueprintResult(
                match=match,
                blueprint_number=6,
                blueprint_name="THE STRONG DRAW",
                target_market="Full Time Draw (X) Potential",
                risk_level="High (Strategic)",
                qualifies=True,
                reason=f"Draw odds {match.draw_odds} in [{draw_range_min}-{draw_range_max}]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 7: THE HIGH-SCORING SIGNALS
    # =========================================================================
    def blueprint_7_high_scoring_signals(self, match: Match) -> Optional[List[BlueprintResult]]:
        """
        Trigger Odds (A): Draw (3.40 – 3.56) → GG / Over 2.5 Goals
        Trigger Odds (B): Draw (3.60 – 3.75) → HT 0.5 Goals / Over 2.5 Goals
        The Clause: High draw prices signal an expectation of high goal volatility.
        Risk Level: Moderate-High
        """
        results = []
        
        # Trigger A
        draw_a_min = 3.40
        draw_a_max = 3.56
        
        if draw_a_min <= match.draw_odds <= draw_a_max:
            results.append(BlueprintResult(
                match=match,
                blueprint_number=7,
                blueprint_name="THE HIGH-SCORING SIGNALS (A)",
                target_market="GG / Over 2.5 Goals",
                risk_level="Moderate-High",
                qualifies=True,
                reason=f"Draw odds {match.draw_odds} in [{draw_a_min}-{draw_a_max}] → GG / Over 2.5 Goals"
            ))
        
        # Trigger B
        draw_b_min = 3.60
        draw_b_max = 3.75
        
        if draw_b_min <= match.draw_odds <= draw_b_max:
            results.append(BlueprintResult(
                match=match,
                blueprint_number=7,
                blueprint_name="THE HIGH-SCORING SIGNALS (B)",
                target_market="HT 0.5 Goals / Over 2.5 Goals",
                risk_level="Moderate-High",
                qualifies=True,
                reason=f"Draw odds {match.draw_odds} in [{draw_b_min}-{draw_b_max}] → HT 0.5 Goals / Over 2.5 Goals"
            ))
        
        return results if results else None
    
    # =========================================================================
    # MASTER SCANNER: Run all blueprints on a match
    # =========================================================================
    def scan_match(self, match: Match) -> List[BlueprintResult]:
        """
        Run all 7 blueprints on a single match and return all qualifying results.
        """
        match_results = []
        
        # Blueprint 1
        result = self.blueprint_1_elite_home_banker(match)
        if result:
            match_results.append(result)
        
        # Blueprint 2
        result = self.blueprint_2_primary_favorite(match)
        if result:
            match_results.append(result)
        
        # Blueprint 3
        result = self.blueprint_3_moderate_favorite_safety(match)
        if result:
            match_results.append(result)
        
        # Blueprint 4
        result = self.blueprint_4_goal_engine(match)
        if result:
            match_results.append(result)
        
        # Blueprint 5
        result = self.blueprint_5_defensive_trap(match)
        if result:
            match_results.append(result)
        
        # Blueprint 6
        result = self.blueprint_6_strong_draw(match)
        if result:
            match_results.append(result)
        
        # Blueprint 7 (can return multiple)
        results_7 = self.blueprint_7_high_scoring_signals(match)
        if results_7:
            match_results.extend(results_7)
        
        return match_results
    
    def scan_matches(self, matches: List[Match]) -> List[BlueprintResult]:
        """
        Run all 7 blueprints on a list of matches.
        """
        all_results = []
        for match in matches:
            results = self.scan_match(match)
            all_results.extend(results)
        return all_results
    
    # =========================================================================
    # OUTPUT METHODS
    # =========================================================================
    def print_results(self, results: List[BlueprintResult]) -> None:
        """
        Print blueprint results in a readable format.
        """
        if not results:
            print("\n" + "="*60)
            print("NO MATCHES QUALIFY FOR ANY BLUEPRINT")
            print("="*60)
            return
        
        print("\n" + "="*80)
        print("JAY SOCCER PREDICTION SYSTEM - BLUEPRINT RESULTS")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Group by blueprint for summary
        blueprint_counts = {}
        for res in results:
            key = f"BP{res.blueprint_number}"
            blueprint_counts[key] = blueprint_counts.get(key, 0) + 1
        
        print("\n📊 SUMMARY:")
        for bp, count in sorted(blueprint_counts.items()):
            print(f"   {bp}: {count} qualifying matches")
        
        print("\n" + "-"*80)
        
        for i, res in enumerate(results, 1):
            print(f"\n[{i}] BLUEPRINT {res.blueprint_number}: {res.blueprint_name}")
            print(f"    Match: {res.match.home_team} vs {res.match.away_team}")
            print(f"    League: {res.match.league}")
            print(f"    Time: {res.match.time} | Date: {res.match.date}")
            print(f"    Odds: H={res.match.home_odds} | D={res.match.draw_odds} | A={res.match.away_odds}")
            print(f"    Target Market: {res.target_market}")
            print(f"    Risk Level: {res.risk_level}")
            print(f"    Reason: {res.reason}")
            print("-" * 60)
    
    def to_csv_format(self, results: List[BlueprintResult]) -> str:
        """
        Export results to CSV format for Excel/Google Sheets.
        """
        if not results:
            return "No matches qualify for any blueprint."
        
        lines = [
            "Timestamp,Blueprint,Blueprint Name,League,League Key,Home Team,Away Team,Time,Date,Home Odds,Draw Odds,Away Odds,Target Market,Risk Level,Reason"
        ]
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for res in results:
            line = f'"{timestamp}",{res.blueprint_number},"{res.blueprint_name}","{res.match.league}","{res.match.league_key}","{res.match.home_team}","{res.match.away_team}","{res.match.time}","{res.match.date}",{res.match.home_odds},{res.match.draw_odds},{res.match.away_odds},"{res.target_market}","{res.risk_level}","{res.reason}"'
            lines.append(line)
        
        return "\n".join(lines)
    
    def to_text_format(self, results: List[BlueprintResult]) -> str:
        """
        Export results to plain text format for offline reference.
        """
        if not results:
            return "NO MATCHES QUALIFY FOR ANY BLUEPRINT"
        
        lines = []
        lines.append("="*80)
        lines.append(f"JAY SOCCER PREDICTION SYSTEM - BLUEPRINT RESULTS")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*80)
        
        for i, res in enumerate(results, 1):
            lines.append(f"\n[{i}] BLUEPRINT {res.blueprint_number}: {res.blueprint_name}")
            lines.append(f"    Match: {res.match.home_team} vs {res.match.away_team}")
            lines.append(f"    League: {res.match.league}")
            lines.append(f"    Target Market: {res.target_market}")
            lines.append(f"    Risk Level: {res.risk_level}")
            lines.append(f"    Reason: {res.reason}")
            lines.append("-"*60)
        
        return "\n".join(lines)
    
    def to_detailed_text(self, results: List[BlueprintResult]) -> str:
        """
        Export results to detailed text format with all match information.
        """
        if not results:
            return "NO MATCHES QUALIFY FOR ANY BLUEPRINT"
        
        lines = []
        lines.append("="*80)
        lines.append("⚽ JAY SOCCER PREDICTION SYSTEM - DAILY REPORT ⚽")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Qualifying Matches: {len(results)}")
        lines.append("="*80)
        
        # Group by blueprint
        for bp_num in range(1, 8):
            bp_results = [r for r in results if r.blueprint_number == bp_num]
            if not bp_results:
                continue
            
            lines.append(f"\n\n{'='*80}")
            lines.append(f"BLUEPRINT {bp_num}: {bp_results[0].blueprint_name}")
            lines.append(f"Target: {bp_results[0].target_market}")
            lines.append(f"Risk: {bp_results[0].risk_level}")
            lines.append(f"Count: {len(bp_results)} matches")
            lines.append("="*80)
            
            for res in bp_results:
                lines.append(f"\n📍 {res.match.home_team} vs {res.match.away_team}")
                lines.append(f"   League: {res.match.league}")
                lines.append(f"   Time: {res.match.time}")
                lines.append(f"   Odds: {res.match.home_odds} | {res.match.draw_odds} | {res.match.away_odds}")
                lines.append(f"   Play: {res.target_market}")
        
        return "\n".join(lines)


# =============================================================================
# GLOBAL ODDS FETCHER - COVERS ALL FOOTBALL MATCHES WORLDWIDE
# =============================================================================

class GlobalOddsFetcher:
    """
    Fetches ALL football matches worldwide from The Odds API.
    Automatically discovers all active soccer leagues each day.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_all_soccer_leagues(self) -> List[Dict]:
        """
        Get ALL active soccer leagues from The Odds API.
        Returns a list of all soccer sports available.
        """
        try:
            url = f"{self.base_url}/sports"
            params = {"apiKey": self.api_key}
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                all_sports = response.json()
                # Filter only soccer sports (those starting with 'soccer')
                soccer_leagues = [sport for sport in all_sports if sport.get('key', '').startswith('soccer')]
                return soccer_leagues
            else:
                print(f"Error fetching sports: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching sports: {e}")
            return []
    
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
                    # Get the best odds from the first bookmaker
                    bookmakers = event.get("bookmakers", [])
                    if not bookmakers:
                        continue
                    
                    # Use the first bookmaker (typically has good odds)
                    best_bookmaker = bookmakers[0]
                    
                    markets = best_bookmaker.get("markets", [])
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
                            bookmaker=best_bookmaker.get("key", "")
                        )
                        matches.append(match)
                
                # Track API usage
                remaining = response.headers.get("x-requests-remaining", "Unknown")
                print(f"  ✓ {league_name}: {len(data)} matches | Remaining: {remaining}")
                
            elif response.status_code == 429:
                print(f"  ✗ Rate limit exceeded for {league_name}")
            else:
                print(f"  ✗ {league_name}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout for {league_name}")
        except Exception as e:
            print(f"  ✗ Error for {league_name}: {e}")
        
        return matches
    
    def fetch_all_matches(self, max_leagues: int = None, league_filter: List[str] = None) -> List[Match]:
        """
        Fetch ALL football matches from ALL active soccer leagues worldwide.
        
        Args:
            max_leagues: Maximum number of leagues to fetch (None = all)
            league_filter: List of specific league keys to fetch (None = all)
        
        Returns:
            List of Match objects from all leagues
        """
        print("\n" + "="*80)
        print("GLOBAL SOCCER SCAN - FETCHING ALL MATCHES WORLDWIDE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Step 1: Get all soccer leagues
        print("\n[1/2] Discovering all active soccer leagues...")
        all_leagues = self.get_all_soccer_leagues()
        
        if not all_leagues:
            print("❌ No leagues found. Check your API key.")
            return []
        
        print(f"✓ Found {len(all_leagues)} active soccer leagues")
        
        # Apply filter if specified
        if league_filter:
            all_leagues = [l for l in all_leagues if l.get('key') in league_filter]
            print(f"   Filtered to {len(all_leagues)} specified leagues")
        
        if max_leagues:
            all_leagues = all_leagues[:max_leagues]
            print(f"   Limited to first {max_leagues} leagues")
        
        # Step 2: Fetch matches for each league
        print("\n[2/2] Fetching matches from each league...")
        all_matches = []
        failed_leagues = []
        
        for i, league in enumerate(all_leagues, 1):
            league_key = league.get('key', '')
            league_name = league.get('title', league_key)
            
            # Clean up league name for display
            display_name = league_name.replace('Soccer - ', '')
            
            print(f"\n  [{i}/{len(all_leagues)}] {display_name}...")
            
            matches = self.fetch_matches_for_league(league_key, display_name)
            
            if matches:
                all_matches.extend(matches)
            else:
                failed_leagues.append(display_name)
        
        # Summary
        print("\n" + "="*80)
        print("📊 SCAN SUMMARY")
        print("="*80)
        print(f"   Total leagues scanned: {len(all_leagues)}")
        print(f"   Leagues with matches: {len(all_leagues) - len(failed_leagues)}")
        print(f"   Leagues with no matches: {len(failed_leagues)}")
        print(f"   Total matches found: {len(all_matches)}")
        
        if failed_leagues:
            print(f"\n   ⚠️ Leagues with no matches (may have no games today):")
            for league in failed_leagues[:10]:
                print(f"      - {league}")
            if len(failed_leagues) > 10:
                print(f"      ... and {len(failed_leagues) - 10} more")
        
        print("="*80)
        return all_matches
    
    def fetch_matches_for_date(self, target_date: str = None) -> List[Match]:
        """
        Fetch matches for a specific date.
        
        Args:
            target_date: Date in YYYY-MM-DD format. If None, uses today.
        
        Returns:
            List of Match objects for that date
        """
        all_matches = self.fetch_all_matches()
        
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        # Filter matches by date
        filtered_matches = [m for m in all_matches if m.date == target_date]
        
        print(f"\n📅 Filtered to {len(filtered_matches)} matches on {target_date}")
        
        return filtered_matches
    
    def fetch_todays_matches(self) -> List[Match]:
        """
        Convenience method to fetch only today's matches.
        """
        return self.fetch_matches_for_date()


# =============================================================================
# MAIN FUNCTION FOR DAILY AUTOMATION
# =============================================================================

def run_daily_global_scan(api_key: str) -> Tuple[List[BlueprintResult], List[Match]]:
    """
    Run a complete daily scan of ALL football matches worldwide.
    
    Args:
        api_key: Your The Odds API key
    
    Returns:
        Tuple of (blueprint_results, all_matches)
    """
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█     JAY SOCCER PREDICTION SYSTEM - GLOBAL DAILY SCAN     █")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    # Step 1: Fetch all matches
    fetcher = GlobalOddsFetcher(api_key)
    all_matches = fetcher.fetch_all_matches()
    
    if not all_matches:
        print("\n❌ No matches found. Check your API key or try again later.")
        return [], []
    
    # Step 2: Run blueprints
    print("\n" + "="*80)
    print("🔍 RUNNING BLUEPRINTS ON ALL MATCHES")
    print("="*80)
    
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(all_matches)
    
    # Step 3: Display results
    scanner.print_results(results)
    
    # Step 4: Print summary statistics
    print("\n" + "="*80)
    print("📈 DAILY STATISTICS")
    print("="*80)
    print(f"   Total matches scanned: {len(all_matches)}")
    print(f"   Total qualifying matches: {len(results)}")
    print(f"   Qualification rate: {len(results)/len(all_matches)*100:.1f}%")
    
    # Breakdown by blueprint
    bp_counts = {}
    for res in results:
        bp_counts[f"BP{res.blueprint_number}"] = bp_counts.get(f"BP{res.blueprint_number}", 0) + 1
    
    if bp_counts:
        print("\n   Breakdown by blueprint:")
        for bp, count in sorted(bp_counts.items()):
            print(f"      {bp}: {count} matches")
    
    print("="*80)
    
    return results, all_matches


# =============================================================================
# EXPORT FUNCTIONS FOR DAILY REPORTS
# =============================================================================

def save_daily_report(results: List[BlueprintResult], matches: List[Match], output_dir: str = "."):
    """
    Save daily results to multiple file formats.
    
    Args:
        results: List of BlueprintResult objects
        matches: List of all Match objects scanned
        output_dir: Directory to save files
    """
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # Save CSV
    csv_path = os.path.join(output_dir, f"jay_blueprint_results_{timestamp}.csv")
    with open(csv_path, 'w') as f:
        scanner = JaySoccerBlueprints()
        f.write(scanner.to_csv_format(results))
    print(f"✓ CSV saved: {csv_path}")
    
    # Save detailed text report
    txt_path = os.path.join(output_dir, f"jay_daily_report_{timestamp}.txt")
    with open(txt_path, 'w') as f:
        scanner = JaySoccerBlueprints()
        f.write(scanner.to_detailed_text(results))
    print(f"✓ Text report saved: {txt_path}")
    
    # Save all matches scanned (for reference)
    all_matches_path = os.path.join(output_dir, f"all_matches_scanned_{timestamp}.csv")
    with open(all_matches_path, 'w') as f:
        f.write("League,Home Team,Away Team,Home Odds,Draw Odds,Away Odds,Time,Date\n")
        for match in matches:
            f.write(f'"{match.league}","{match.home_team}","{match.away_team}",{match.home_odds},{match.draw_odds},{match.away_odds},"{match.time}","{match.date}"\n')
    print(f"✓ All matches saved: {all_matches_path}")


# =============================================================================
# LEAGUE REFERENCE - ALL SOCCER LEAGUES COVERED
# =============================================================================

SOCCER_LEAGUES_REFERENCE = {
    "europe": [
        "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga",
        "soccer_italy_serie_a", "soccer_france_ligue_one", "soccer_netherlands_eredivisie",
        "soccer_portugal_primeira_liga", "soccer_belgium_first_div", "soccer_scotland_premiership",
        "soccer_turkey_super_league", "soccer_greece_super_league", "soccer_russia_premier_league",
        "soccer_ukraine_premier_league", "soccer_czech_republic_1_league", "soccer_croatia_hnl",
        "soccer_switzerland_super_league", "soccer_austria_bundesliga", "soccer_denmark_superliga",
        "soccer_poland_ekstraklasa", "soccer_serbia_super_liga", "soccer_romania_liga_1"
    ],
    "international": [
        "soccer_uefa_champs_league", "soccer_uefa_europa_league", "soccer_uefa_europa_conference_league",
        "soccer_fifa_world_cup", "soccer_uefa_nations_league", "soccer_international_friendly"
    ],
    "south_america": [
        "soccer_brazil_campeonato", "soccer_argentina_primera_division",
        "soccer_chile_primera_division", "soccer_colombia_primera_a",
        "soccer_uruguay_primera_division", "soccer_paraguay_primera_division",
        "soccer_peru_primera_division", "soccer_ecuador_liga_pro",
        "soccer_copa_libertadores", "soccer_copa_sudamericana"
    ],
    "north_america": [
        "soccer_usa_mls", "soccer_mexico_ligamx", "soccer_canada_premier_league",
        "soccer_concacaf_champions_cup", "soccer_concacaf_nations_league"
    ],
    "asia": [
        "soccer_japan_j1_league", "soccer_japan_j2_league", "soccer_south_korea_kleague1",
        "soccer_south_korea_kleague2", "soccer_china_super_league", "soccer_australia_a_league",
        "soccer_saudi_pro_league", "soccer_uae_arabian_gulf_league", "soccer_qatar_stars_league",
        "soccer_afc_champions_league", "soccer_indian_super_league"
    ],
    "africa": [
        "soccer_egypt_premier_league", "soccer_south_africa_psl", "soccer_morocco_botola_pro",
        "soccer_tunisia_ligue_1", "soccer_algeria_ligue_1", "soccer_caf_champions_league",
        "soccer_caf_confederation_cup"
    ]
}


def get_all_league_keys() -> List[str]:
    """Return all league keys from the reference dictionary."""
    all_keys = []
    for category, leagues in SOCCER_LEAGUES_REFERENCE.items():
        all_keys.extend(leagues)
    return all_keys
