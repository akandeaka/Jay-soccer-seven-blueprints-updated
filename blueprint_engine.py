"""
Blueprint Engine - 8 Soccer Betting Blueprints
NO DEMO DATA - Only processes real matches passed to it
"""

import pandas as pd
from typing import Dict, List, Optional


class BlueprintEngine:
    """Apply 8 blueprints to filter matches"""
    
    HIGH_SCORING_LEAGUES = [
        'bundesliga', 'eredivisie', 'premier league', 
        'serie a', 'ligue 1', 'epl', 'premiership'
    ]
    
    def __init__(self):
        self.blueprint_stats = {f'BP{i}': 0 for i in range(1, 9)}
    
    def classify_blueprint(self, match: Dict) -> Optional[Dict]:
        """Classify match against all 8 blueprints"""
        
        home = match.get('home_odds', 0)
        draw = match.get('draw_odds', 0)
        away = match.get('away_odds', 0)
        league = match.get('league', '').lower()
        btts_yes = match.get('btts_yes_odds', 0)
        
        # BP1: Elite Home Banker
        if 1.20 <= home <= 1.29 and away >= 10.0:
            return self._create_result('BP1', match, 'Straight Home Win', 'Ultra-Low', 95)
        
        # BP2: Primary Favorite
        if 1.30 <= home <= 1.36 and away >= 9.0:
            return self._create_result('BP2', match, 'Home Win', 'Low', 90)
        
        # BP3: Moderate Favorite Safety
        if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
            return self._create_result('BP3', match, '1X & Over 1.5 Goals', 'Low-Moderate', 85)
        
        # BP4: Goal Engine
        if 1.72 <= home <= 1.80:
            return self._create_result('BP4', match, 'Over 1.5 Goals', 'Moderate', 75)
        
        # BP5: Defensive Trap
        if 1.90 <= home <= 2.02:
            return self._create_result('BP5', match, '1X & Under 3.5 FT', 'Moderate', 70)
        
        # BP6: Strong Draw
        if 2.75 <= draw <= 3.39:
            return self._create_result('BP6', match, 'Full Time Draw', 'High', 50)
        
        # BP7: BTTS Value Spot
        if 1.40 <= btts_yes <= 1.69:
            return self._create_result('BP7', match, 'Both Teams to Score', 'Low-Moderate', 75, requires_gg=True)
        
        # BP8: High-Scoring Signals
        if 3.60 <= draw <= 3.75 and self._is_high_scoring_league(league):
            return self._create_result('BP8', match, 'HT 0.5 / Over 2.5 Goals', 'Moderate-High', 60)
        
        return None
    
    def _create_result(self, bp: str, match: Dict, play: str, risk: str, confidence: int, requires_gg: bool = False) -> Dict:
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
            'requires_gg': requires_gg
        }
    
    def _is_high_scoring_league(self, league: str) -> bool:
        for hl in self.HIGH_SCORING_LEAGUES:
            if hl in league.lower():
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
                self.blueprint_stats[result['blueprint']] += 1
        
        return results
    
    def get_stats(self) -> Dict:
        return self.blueprint_stats
