"""
Blueprint Engine - 8 Soccer Betting Blueprints
Complete implementation with AI integration
"""

import pandas as pd
from typing import Dict, List, Optional


class BlueprintEngine:
    """Apply 8 blueprints to filter matches with AI decision making"""
    
    # League classifications for AI decisions
    HIGH_SCORING_LEAGUES = [
        'bundesliga', 'eredivisie', 'premier league', 
        'epl', 'serie a', 'ligue 1', 'la liga'
    ]
    
    DEFENSIVE_LEAGUES = [
        'serie b', 'ligue 2', 'championship', 
        'liga nos', 'super lig', 'primeira liga'
    ]
    
    def __init__(self):
        self.blueprint_stats = {f'BP{i}': 0 for i in range(1, 9)}
    
    def classify_blueprint(self, match: Dict) -> Optional[Dict]:
        """
        Classify match against all 8 blueprints
        Returns blueprint data with AI decision if matched
        """
        home = match.get('home_odds', 0)
        draw = match.get('draw_odds', 0)
        away = match.get('away_odds', 0)
        league = match.get('league', '')
        
        # Extract team names for AI analysis
        match_name = match.get('match', '')
        home_team = match_name.split(' vs ')[0] if ' vs ' in match_name else ''
        away_team = match_name.split(' vs ')[1] if ' vs ' in match_name else ''
        
        # Check each blueprint
        result = None
        
        result = result or self._check_bp1(home, away, match)
        result = result or self._check_bp2(home, away, match)
        result = result or self._check_bp3(home, away, match)
        result = result or self._check_bp4(home, league, home_team, away_team, match)
        result = result or self._check_bp5(home, league, home_team, away_team, match)
        result = result or self._check_bp6(draw, match)
        result = result or self._check_bp7(home, league, home_team, away_team, match)
        result = result or self._check_bp8(draw, league, match)
        
        if result:
            self.blueprint_stats[result['blueprint']] += 1
        
        return result
    
    def _check_bp1(self, home: float, away: float, match: Dict) -> Optional[Dict]:
        """BP1: Elite Home Banker - Home odds 1.20-1.29, Away odds ≥ 10.0"""
        if 1.20 <= home <= 1.29 and away >= 10.0:
            return self._create_result(
                'BP1', match,
                'Straight Home Win',
                'Ultra-Low',
                95,
                f'Home odds {home} indicate 77-83% win probability. Away odds {away} show underdog has <10% chance.'
            )
        return None
    
    def _check_bp2(self, home: float, away: float, match: Dict) -> Optional[Dict]:
        """BP2: Primary Favorite - Home odds 1.30-1.36, Away odds ≥ 9.0"""
        if 1.30 <= home <= 1.36 and away >= 9.0:
            return self._create_result(
                'BP2', match,
                'Home Win',
                'Low',
                90,
                f'Home odds {home} indicate 73-77% win probability. Strong favorite with value.'
            )
        return None
    
    def _check_bp3(self, home: float, away: float, match: Dict) -> Optional[Dict]:
        """BP3: Moderate Favorite Safety - Home odds 1.30-1.36, Away odds 7.0-8.99"""
        if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
            return self._create_result(
                'BP3', match,
                '1X & Over 1.5 Goals',
                'Low-Moderate',
                85,
                f'Home favored but away team not hopeless ({away}). Adding Over 1.5 goals for safety.'
            )
        return None
    
    def _check_bp4(self, home: float, league: str, home_team: str, away_team: str, match: Dict) -> Optional[Dict]:
        """BP4: Goal Engine - Home odds 1.72-1.80 with AI decision on Over 1.5 Goals"""
        if 1.72 <= home <= 1.80:
            # AI Decision: Check if league is high-scoring or teams have scoring history
            if self._is_high_scoring_league(league) or (self._has_goalscoring_history(home_team) and self._has_goalscoring_history(away_team)):
                return self._create_result(
                    'BP4', match,
                    'Over 1.5 Goals - YES',
                    'Moderate',
                    75,
                    f'Home odds {home} in {league}. Teams have goalscoring history.'
                )
            else:
                return self._create_result(
                    'BP4', match,
                    'Over 1.5 Goals - NO / Under 1.5 Goals',
                    'Moderate',
                    65,
                    f'Home odds {home} but {league} is defensive. Consider Under 1.5 Goals.'
                )
        return None
    
    def _check_bp5(self, home: float, league: str, home_team: str, away_team: str, match: Dict) -> Optional[Dict]:
        """BP5: Defensive Trap - Home odds 1.90-2.02 with AI decision on goals"""
        if 1.90 <= home <= 2.02:
            # AI Decision: Under 3.5 for defensive teams/leagues
            if self._is_defensive_league(league) or (self._has_defensive_history(home_team) and self._has_defensive_history(away_team)):
                return self._create_result(
                    'BP5', match,
                    '1X & Under 3.5 FT - YES',
                    'Moderate (Value Pick)',
                    70,
                    f'Close match odds ({home}) in defensive {league}. Expect low scoring.'
                )
            else:
                return self._create_result(
                    'BP5', match,
                    '1X & Over 2.5 Goals',
                    'Moderate',
                    60,
                    f'Close match but teams are attacking. Consider goals.'
                )
        return None
    
    def _check_bp6(self, draw: float, match: Dict) -> Optional[Dict]:
        """BP6: Strong Draw - Draw odds 2.75-3.39"""
        if 2.75 <= draw <= 3.39:
            return self._create_result(
                'BP6', match,
                'Full Time Draw (X) Potential',
                'High (Strategic)',
                50,
                f'Draw odds {draw} indicate 29-36% draw probability. Two evenly matched teams.'
            )
        return None
    
    def _check_bp7(self, home: float, league: str, home_team: str, away_team: str, match: Dict) -> Optional[Dict]:
        """BP7: BTTS Value Spot - Home odds 1.40-1.69 with AI deciding Yes/No"""
        if 1.40 <= home <= 1.69:
            # AI Decision: BTTS YES for high-scoring leagues with attacking teams
            if self._is_high_scoring_league(league) and (self._has_goalscoring_history(home_team) and self._has_goalscoring_history(away_team)):
                return self._create_result(
                    'BP7', match,
                    'Both Teams to Score (GG) - YES',
                    'Low-Moderate',
                    75,
                    f'Home odds {home} in high-scoring {league}. Both teams have strong scoring history.'
                )
            # AI Decision: BTTS NO for defensive leagues
            elif self._is_defensive_league(league) or (self._has_defensive_history(home_team) and self._has_defensive_history(away_team)):
                return self._create_result(
                    'BP7', match,
                    'Both Teams to Score (GG) - NO',
                    'Low-Moderate',
                    70,
                    f'Home odds {home} but {league} is defensive. Clean sheet likely.'
                )
            # Default: BTTS YES with lower confidence
            else:
                return self._create_result(
                    'BP7', match,
                    'Both Teams to Score (GG) - YES',
                    'Moderate',
                    65,
                    f'Home odds {home} trigger. Moderate confidence for BTTS.'
                )
        return None
    
    def _check_bp8(self, draw: float, league: str, match: Dict) -> Optional[Dict]:
        """BP8: High-Scoring Signals - Draw odds 3.60-3.75 + high-scoring league only"""
        if 3.60 <= draw <= 3.75 and self._is_high_scoring_league(league):
            return self._create_result(
                'BP8', match,
                'HT 0.5 Goals / Over 2.5 Goals',
                'Moderate-High',
                60,
                f'Draw odds {draw} in high-scoring {league} league. Expect goal-heavy match.'
            )
        return None
    
    def _create_result(self, bp: str, match: Dict, play: str, risk: str, confidence: int, reasoning: str) -> Dict:
        """Create standardized result dictionary"""
        return {
            'blueprint': bp,
            'match': match.get('match', 'Unknown'),
            'league': match.get('league', 'Unknown'),
            'play': play,
            'risk': risk,
            'confidence': confidence,
            'home_odds': match.get('home_odds', 0),
            'draw_odds': match.get('draw_odds', 0),
            'away_odds': match.get('away_odds', 0),
            'btts_odds': match.get('btts_yes_odds', 0),
            'reasoning': reasoning
        }
    
    def _is_high_scoring_league(self, league: str) -> bool:
        """Check if league is high-scoring"""
        for hl in self.HIGH_SCORING_LEAGUES:
            if hl in league.lower():
                return True
        return False
    
    def _is_defensive_league(self, league: str) -> bool:
        """Check if league is defensive/low-scoring"""
        for dl in self.DEFENSIVE_LEAGUES:
            if dl in league.lower():
                return True
        return False
    
    def _has_goalscoring_history(self, team: str) -> bool:
        """
        AI function to check if team has strong scoring history
        This would use actual team form data from input
        """
        # Known high-scoring teams (for demo purposes)
        high_scoring_teams = [
            'bayern', 'dortmund', 'leverkusen', 'leipzig',
            'man city', 'liverpool', 'arsenal', 'chelsea',
            'real madrid', 'barcelona', 'atletico', 'sevilla',
            'psg', 'monaco', 'lyon', 'milan', 'inter', 'napoli',
            'ajax', 'psv', 'feyenoord'
        ]
        
        for hst in high_scoring_teams:
            if hst.lower() in team.lower():
                return True
        return False
    
    def _has_defensive_history(self, team: str) -> bool:
        """
        AI function to check if team has strong defensive history
        """
        # Known defensive/low-scoring teams (for demo purposes)
        defensive_teams = [
            'burnley', 'sheffield', 'west brom',
            'getafe', 'cadiz', 'elche', 'spezia', 'salernitana'
        ]
        
        for dt in defensive_teams:
            if dt.lower() in team.lower():
                return True
        return False
    
    def filter_matches(self, df: pd.DataFrame) -> List[Dict]:
        """Filter all matches through blueprints"""
        results = []
        
        for _, row in df.iterrows():
            match = row.to_dict()
            result = self.classify_blueprint(match)
            if result:
                results.append(result)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get blueprint statistics"""
        return self.blueprint_stats
