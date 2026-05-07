"""
Accumulator Builder - Create multi-bet accumulators without duplicate teams
"""

import itertools
from typing import List, Dict


class AccumulatorBuilder:
    """Build accumulators at different odds targets"""
    
    def __init__(self):
        pass
    
    def get_match_odds(self, match: Dict) -> float:
        play = match.get('play', '')
        
        if 'Home Win' in play:
            return match.get('home_odds', 1.5)
        elif 'Draw' in play:
            return match.get('draw_odds', 3.0)
        elif 'BTTS' in play or 'Both Teams to Score' in play:
            return match.get('btts_odds', 1.65)
        elif 'Over 1.5' in play:
            return 1.30
        elif 'Over 2.5' in play:
            return match.get('over_25_odds', 1.75)
        elif 'Under 3.5' in play:
            return 1.45
        else:
            return 1.50
    
    def extract_teams(self, match: Dict) -> List[str]:
        match_name = match.get('match', '')
        if ' vs ' in match_name:
            return match_name.split(' vs ')
        return [match_name]
    
    def remove_duplicate_teams(self, matches: List[Dict]) -> List[Dict]:
        seen_teams = set()
        unique_matches = []
        
        for match in matches:
            teams = self.extract_teams(match)
            if not any(team in seen_teams for team in teams):
                unique_matches.append(match)
                seen_teams.update(teams)
        
        return unique_matches
    
    def calculate_combination_odds(self, matches: List[Dict]) -> float:
        odds = 1.0
        for match in matches:
            odds *= self.get_match_odds(match)
        return round(odds, 2)
    
    def build_accumulators(self, analyzed_matches: List[Dict]) -> Dict:
        if len(analyzed_matches) < 2:
            return {'error': 'Not enough matches'}
        
        unique_matches = self.remove_duplicate_teams(analyzed_matches)
        
        if len(unique_matches) < 2:
            return {'error': 'Not enough unique teams'}
        
        matches = sorted(unique_matches, key=lambda x: x.get('ai_confidence', 0), reverse=True)
        
        results = {}
        
        results['2_odds'] = self._build_target_accumulator(matches, 2.0, 2, 3)
        results['4_odds'] = self._build_target_accumulator(matches, 4.0, 4, 4)
        results['7_odds'] = self._build_target_accumulator(matches, 7.0, 5, 5)
        results['10_odds'] = self._build_target_accumulator(matches, 10.0, 5, 6)
        
        return results
    
    def _build_target_accumulator(self, matches: List[Dict], target_odds: float, 
                                   min_matches: int, max_matches: int) -> Dict:
        
        for n in range(min_matches, min(max_matches, len(matches)) + 1):
            for combo in itertools.combinations(matches[:12], n):
                teams_in_combo = set()
                has_duplicate = False
                
                for match in combo:
                    teams = self.extract_teams(match)
                    for team in teams:
                        if team in teams_in_combo:
                            has_duplicate = True
                            break
                    teams_in_combo.update(teams)
                    if has_duplicate:
                        break
                
                if has_duplicate:
                    continue
                
                total_odds = self.calculate_combination_odds(list(combo))
                
                if target_odds <= total_odds <= target_odds * 1.3:
                    return {
                        'matches': list(combo),
                        'total_odds': total_odds,
                        'target_odds': target_odds,
                        'status': 'BUILT'
                    }
        
        return {'error': f'Could not build {target_odds}x accumulator'}
