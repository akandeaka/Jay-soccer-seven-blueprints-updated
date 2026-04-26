"""
JAY SOCCER PREDICTION SYSTEM - THE 7 MASTER BLUEPRINTS
Version: 4.0
Based strictly on the provided blueprints - no additions or deletions
"""

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Match:
    """Represents a football match with odds data"""
    league: str
    home_team: str
    away_team: str
    home_odds: float
    draw_odds: float
    away_odds: float
    time: str = ""
    date: str = ""


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
    """
    
    # =========================================================================
    # BLUEPRINT 1: THE ELITE HOME BANKER
    # =========================================================================
    def blueprint_1_elite_home_banker(self, match: Match) -> Optional[BlueprintResult]:
        """Home (1.20–1.29) | Away ≥ 10.0 | Straight Home Win | Ultra-Low"""
        if 1.20 <= match.home_odds <= 1.29 and match.away_odds >= 10.0:
            return BlueprintResult(
                match=match,
                blueprint_number=1,
                blueprint_name="THE ELITE HOME BANKER",
                target_market="Straight Home Win",
                risk_level="Ultra-Low",
                qualifies=True,
                reason=f"Home {match.home_odds} in [1.20-1.29] & Away {match.away_odds} ≥ 10.0"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 2: THE PRIMARY FAVORITE
    # =========================================================================
    def blueprint_2_primary_favorite(self, match: Match) -> Optional[BlueprintResult]:
        """Home (1.30–1.36) | Away ≥ 9.0 | Home Winning | Low"""
        if 1.30 <= match.home_odds <= 1.36 and match.away_odds >= 9.0:
            return BlueprintResult(
                match=match,
                blueprint_number=2,
                blueprint_name="THE PRIMARY FAVORITE",
                target_market="Home Winning (Straight Win)",
                risk_level="Low",
                qualifies=True,
                reason=f"Home {match.home_odds} in [1.30-1.36] & Away {match.away_odds} ≥ 9.0"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 3: THE MODERATE FAVORITE SAFETY
    # =========================================================================
    def blueprint_3_moderate_favorite_safety(self, match: Match) -> Optional[BlueprintResult]:
        """Home (1.30–1.36) | Away (7.0–8.99) | 1X & Over 1.5 | Low-Moderate"""
        if 1.30 <= match.home_odds <= 1.36 and 7.0 <= match.away_odds <= 8.99:
            return BlueprintResult(
                match=match,
                blueprint_number=3,
                blueprint_name="THE MODERATE FAVORITE SAFETY",
                target_market="1X & Over 1.5 Goals",
                risk_level="Low-Moderate (Safety Net Applied)",
                qualifies=True,
                reason=f"Home {match.home_odds} in [1.30-1.36] & Away {match.away_odds} in [7.0-8.99]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 4: THE GOAL ENGINE
    # =========================================================================
    def blueprint_4_goal_engine(self, match: Match) -> Optional[BlueprintResult]:
        """Home (1.72–1.80) | Independent of Away odds | Over 1.5 Goals | Moderate"""
        if 1.72 <= match.home_odds <= 1.80:
            return BlueprintResult(
                match=match,
                blueprint_number=4,
                blueprint_name="THE GOAL ENGINE",
                target_market="Over 1.5 Goals",
                risk_level="Moderate",
                qualifies=True,
                reason=f"Home {match.home_odds} in [1.72-1.80]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 5: THE DEFENSIVE TRAP
    # =========================================================================
    def blueprint_5_defensive_trap(self, match: Match) -> Optional[BlueprintResult]:
        """Home (1.90–2.02) | 1X & Under 3.5 FT | Moderate (Value Pick)"""
        if 1.90 <= match.home_odds <= 2.02:
            return BlueprintResult(
                match=match,
                blueprint_number=5,
                blueprint_name="THE DEFENSIVE TRAP",
                target_market="1X & Under 3.5 FT",
                risk_level="Moderate (Value Pick)",
                qualifies=True,
                reason=f"Home {match.home_odds} in [1.90-2.02]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 6: THE STRONG DRAW
    # =========================================================================
    def blueprint_6_strong_draw(self, match: Match) -> Optional[BlueprintResult]:
        """Draw (2.75–3.39) | Full Time Draw (X) | High (Strategic)"""
        if 2.75 <= match.draw_odds <= 3.39:
            return BlueprintResult(
                match=match,
                blueprint_number=6,
                blueprint_name="THE STRONG DRAW",
                target_market="Full Time Draw (X) Potential",
                risk_level="High (Strategic)",
                qualifies=True,
                reason=f"Draw {match.draw_odds} in [2.75-3.39]"
            )
        return None
    
    # =========================================================================
    # BLUEPRINT 7: THE HIGH-SCORING SIGNALS
    # =========================================================================
    def blueprint_7_high_scoring_signals(self, match: Match) -> Optional[List[BlueprintResult]]:
        """Draw (3.40–3.56) → GG / Over 2.5 | Draw (3.60–3.75) → HT 0.5 / Over 2.5"""
        results = []
        
        if 3.40 <= match.draw_odds <= 3.56:
            results.append(BlueprintResult(
                match=match,
                blueprint_number=7,
                blueprint_name="THE HIGH-SCORING SIGNALS (A)",
                target_market="GG / Over 2.5 Goals",
                risk_level="Moderate-High",
                qualifies=True,
                reason=f"Draw {match.draw_odds} in [3.40-3.56] → GG / Over 2.5"
            ))
        
        if 3.60 <= match.draw_odds <= 3.75:
            results.append(BlueprintResult(
                match=match,
                blueprint_number=7,
                blueprint_name="THE HIGH-SCORING SIGNALS (B)",
                target_market="HT 0.5 Goals / Over 2.5 Goals",
                risk_level="Moderate-High",
                qualifies=True,
                reason=f"Draw {match.draw_odds} in [3.60-3.75] → HT 0.5 / Over 2.5"
            ))
        
        return results if results else None
    
    # =========================================================================
    # MASTER SCANNER
    # =========================================================================
    def scan_match(self, match: Match) -> List[BlueprintResult]:
        """Run all 7 blueprints on a single match"""
        results = []
        
        r1 = self.blueprint_1_elite_home_banker(match)
        if r1: results.append(r1)
        
        r2 = self.blueprint_2_primary_favorite(match)
        if r2: results.append(r2)
        
        r3 = self.blueprint_3_moderate_favorite_safety(match)
        if r3: results.append(r3)
        
        r4 = self.blueprint_4_goal_engine(match)
        if r4: results.append(r4)
        
        r5 = self.blueprint_5_defensive_trap(match)
        if r5: results.append(r5)
        
        r6 = self.blueprint_6_strong_draw(match)
        if r6: results.append(r6)
        
        r7 = self.blueprint_7_high_scoring_signals(match)
        if r7: results.extend(r7)
        
        return results
    
    def scan_matches(self, matches: List[Match]) -> List[BlueprintResult]:
        """Run all 7 blueprints on a list of matches"""
        all_results = []
        for match in matches:
            all_results.extend(self.scan_match(match))
        return all_results
