"""
Blueprint Engine - 8 Soccer Betting Blueprints
NO DEMO DATA - Pure logic based on input data only
"""

import pandas as pd
from typing import Dict, List, Optional


class BlueprintEngine:
    """Apply 8 blueprints to filter matches - NO HARDCODED DATA"""
    
    # League classifications (these are factual, not demo)
    HIGH_SCORING_LEAGUES = [
        'bundesliga', 'eredivisie', 'premier league', 
        'epl', 'serie a', 'ligue 1', 'la liga'
    ]
    
    DEFENSIVE_LEAGUES = [
        'serie b', 'ligue 2', 'championship', 
        'liga nos', 'super lig'
    ]
    
    def __init__(self):
        self.blueprint_stats = {f'BP{i}': 0 for i in range(1, 9)}
    
    def classify_blueprint(self, match: Dict) -> Optional[Dict]:
        """
        Classify match against all 8 blueprints
        Uses ONLY the data provided in the match dictionary
        """
        home = match.get('home_odds', 0)
        draw = match.get('draw_odds', 0)
        away = match.get('away_odds', 0)
        league = match.get('league', '')
        
        # Check each blueprint - NO HARDCODED TEAM NAMES
        result = None
        
        result = result or self._check_bp1(home, away, match)
        result = result or self._check_bp2(home, away, match)
        result = result or self._check_bp3(home, away, match)
        result = result or self._check_bp4(home, league, match)
        result = result or self._check_bp5(home, league, match)
        result = result or self._check_bp6(draw, match)
        result = result or self._check_bp7(home, league, match)
        result = result or self._check_bp8(draw, league, match)
        
        if result:
            self.blueprint_stats[result['blueprint']] += 1
        
        return result
    
    def _check_bp1(self, home: float, away: float, match: Dict) -> Optional[Dict]:
        """BP1: Elite Home Banker"""
        if 1.20 <= home <= 1.29 and away >= 10.0:
            return self._create_result(
                'BP1', match, 'Straight Home Win', 'Ultra-Low', 95
            )
        return None
    
    def _check_bp2(self, home: float, away: float, match: Dict) -> Optional[Dict]:
        """BP2: Primary Favorite"""
        if 1.30 <= home <= 1.36 and away >= 9.0:
            return self._create_result(
                'BP2', match, 'Home Win', 'Low', 90
            )
        return None
    
    def _check_bp3(self, home: float, away: float, match: Dict) -> Optional[Dict]:
        """BP3: Moderate Favorite Safety"""
        if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
            return self._create_result(
                'BP3', match, '1X & Over 1.5 Goals', 'Low-Moderate', 85
            )
        return None
    
    def _check_bp4(self, home: float, league: str, match: Dict) -> Optional[Dict]:
        """BP4: Goal Engine - Based ONLY on league (no team names)"""
        if 1.72 <= home <= 1.80:
            if self._is_high_scoring_league(league):
                return self._create_result(
                    'BP4', match, 'Over 1.5 Goals - YES', 'Moderate', 75
                )
            else:
                return self._create_result(
                    'BP4', match, 'Over 1.5 Goals - NO', 'Moderate', 65
                )
        return None
    
    def _check_bp5(self, home: float, league: str, match: Dict) -> Optional[Dict]:
        """BP5: Defensive Trap - Based ONLY on league (no team names)"""
        if 1.90 <= home <= 2.02:
            if self._is_defensive_league(league):
                return self._create_result(
                    'BP5', match, '1X & Under 3.5 FT', 'Moderate', 70
                )
            else:
                return self._create_result(
                    'BP5', match, '1X & Over 2.5 Goals', 'Moderate', 60
                )
        return None
    
    def _check_bp6(self, draw: float, match: Dict) -> Optional[Dict]:
        """BP6: Strong Draw"""
        if 2.75 <= draw <= 3.39:
            return self._create_result(
                'BP6', match, 'Full Time Draw', 'High', 50
            )
        return None
    
    def _check_bp7(self, home: float, league: str, match: Dict) -> Optional[Dict]:
        """
        BP7: BTTS Value Spot
        TRIGGER: Home odds 1.40-1.69
        DECISION: Based ONLY on league type (no team names)
        """
        if 1.40 <= home <= 1.69:
            if self._is_high_scoring_league(league):
                return self._create_result(
                    'BP7', match, 'Both Teams to Score (GG) - YES', 'Low-Moderate', 75
                )
            else:
                return self._create_result(
                    'BP7', match, 'Both Teams to Score (GG) - NO', 'Moderate', 65
                )
        return None
    
    def _check_bp8(self, draw: float, league: str, match: Dict) -> Optional[Dict]:
        """BP8: High-Scoring Signals - High-scoring league only"""
        if 3.60 <= draw <= 3.75 and self._is_high_scoring_league(league):
            return self._create_result(
                'BP8', match, 'HT 0.5 / Over 2.5 Goals', 'Moderate-High', 60
            )
        return None
    
    def _create_result(self, bp: str, match: Dict, play: str, risk: str, confidence: int) -> Dict:
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
            'reasoning': f'{bp} triggered by odds criteria'
        }
    
    def _is_high_scoring_league(self, league: str) -> bool:
        """Check if league is high-scoring - FACTUAL only"""
        for hl in self.HIGH_SCORING_LEAGUES:
            if hl in league.lower():
                return True
        return False
    
    def _is_defensive_league(self, league: str) -> bool:
        """Check if league is defensive - FACTUAL only"""
        for dl in self.DEFENSIVE_LEAGUES:
            if dl in league.lower():
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
