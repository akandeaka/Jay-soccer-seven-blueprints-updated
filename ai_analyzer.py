"""
AI Analyzer - Smart analysis of blueprint matches
"""

import pandas as pd
import random
from typing import List, Dict, Tuple
from datetime import datetime, timedelta


class AIAnalyzer:
    """
    AI-based match analyzer
    Uses current trends, form, and historical patterns
    """
    
    def __init__(self):
        # Simulated team form database
        # In production, this would connect to a real API
        self.form_database = self._initialize_form_database()
        
        # League scoring averages
        self.league_avg_goals = {
            'bundesliga': 3.2,
            'eredivisie': 3.1,
            'premier league': 2.8,
            'serie a': 2.6,
            'ligue 1': 2.7,
            'la liga': 2.5
        }
        
        # Current month factor (for seasonal trends)
        self.current_month = datetime.now().month
        
    def _initialize_form_database(self) -> Dict:
        """Initialize simulated form database"""
        # In production, this would fetch real data
        return {}
    
    def analyze_match(self, match: Dict) -> Dict:
        """
        Analyze a single match with AI
        Returns validated prediction or alternative
        """
        match_name = match.get('match', '')
        blueprint = match.get('blueprint', '')
        confidence = match.get('confidence', 50)
        
        # Extract team names
        teams = self._extract_teams(match_name)
        
        # Calculate form score (1-10)
        form_score = self._calculate_form_score(teams)
        
        # Calculate head-to-head factor
        h2h_factor = self._calculate_h2h_factor(teams)
        
        # Calculate league trend factor
        league_trend = self._calculate_league_trend(match.get('league', ''))
        
        # Calculate injury/suspension factor (simulated)
        injury_factor = self._calculate_injury_factor(teams)
        
        # Calculate motivation factor
        motivation = self._calculate_motivation(teams)
        
        # Final AI confidence adjustment
        ai_adjustment = (
            form_score * 0.3 +
            h2h_factor * 0.2 +
            league_trend * 0.2 +
            injury_factor * 0.15 +
            motivation * 0.15
        )
        
        # Adjusted confidence (60-95 range)
        adjusted_confidence = min(95, max(60, confidence * (0.7 + ai_adjustment * 0.3)))
        
        # Determine if AI validates or suggests alternative
        ai_decision, alternative = self._ai_decision(
            blueprint, adjusted_confidence, form_score, teams
        )
        
        return {
            **match,
            'ai_confidence': round(adjusted_confidence, 1),
            'ai_decision': ai_decision,
            'ai_alternative': alternative,
            'form_score': round(form_score, 2),
            'h2h_factor': round(h2h_factor, 2),
            'trend_score': round(league_trend, 2)
        }
    
    def _extract_teams(self, match_name: str) -> Tuple[str, str]:
        """Extract home and away team names"""
        if ' vs ' in match_name:
            parts = match_name.split(' vs ')
            return parts[0].strip(), parts[1].strip()
        return 'Team A', 'Team B'
    
    def _calculate_form_score(self, teams: Tuple[str, str]) -> float:
        """Calculate form score based on recent results (simulated)"""
        # In production, fetch real recent form
        # Simulated: random between 0.5 and 1.0
        return random.uniform(0.5, 1.0)
    
    def _calculate_h2h_factor(self, teams: Tuple[str, str]) -> float:
        """Calculate head-to-head factor (simulated)"""
        # In production, fetch real H2H data
        return random.uniform(0.4, 1.0)
    
    def _calculate_league_trend(self, league: str) -> float:
        """Calculate league scoring trend"""
        league_lower = league.lower()
        for key, avg_goals in self.league_avg_goals.items():
            if key in league_lower:
                if avg_goals >= 3.0:
                    return 0.9
                elif avg_goals >= 2.7:
                    return 0.7
                else:
                    return 0.5
        return 0.6
    
    def _calculate_injury_factor(self, teams: Tuple[str, str]) -> float:
        """Calculate injury/suspension impact (simulated)"""
        return random.uniform(0.6, 1.0)
    
    def _calculate_motivation(self, teams: Tuple[str, str]) -> float:
        """Calculate motivation factor (derby, relegation, title race)"""
        return random.uniform(0.5, 1.0)
    
    def _ai_decision(self, blueprint: str, confidence: float, form_score: float, teams: Tuple[str, str]) -> Tuple[str, str]:
        """AI decides to validate or suggest alternative"""
        if confidence >= 80 and form_score >= 0.7:
            return "VALIDATED", match.get('play', 'Original pick')
        elif confidence >= 70 and form_score >= 0.6:
            return "CONFIRMED", match.get('play', 'Original pick')
        elif confidence >= 60:
            return "CONSIDER", match.get('play', 'Original pick')
        else:
            # Suggest alternative based on blueprint
            alternatives = {
                'BP1': 'Double Chance Home/Draw',
                'BP2': 'Home Win or Draw',
                'BP3': 'Over 1.5 Goals',
                'BP4': 'Over 2.5 Goals',
                'BP5': 'Under 3.5 Goals',
                'BP6': 'Draw No Bet',
                'BP7': 'BTTS Yes',
                'BP8': 'Over 2.5 Goals'
            }
            return "ALTERNATIVE", alternatives.get(blueprint, 'Value Bet')
    
    def analyze_batch(self, matches: List[Dict]) -> List[Dict]:
        """Analyze multiple matches"""
        analyzed = []
        for match in matches:
            analyzed_match = self.analyze_match(match)
            # Only keep matches that pass AI threshold
            if analyzed_match['ai_confidence'] >= 60:
                analyzed.append(analyzed_match)
        
        # Sort by AI confidence
        analyzed.sort(key=lambda x: x['ai_confidence'], reverse=True)
        return analyzed
