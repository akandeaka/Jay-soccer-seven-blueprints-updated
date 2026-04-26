"""
JAY SOCCER PREDICTION SYSTEM - THE 7 MASTER BLUEPRINTS
Version: 4.0
Based strictly on the provided blueprints - no additions or deletions
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
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
