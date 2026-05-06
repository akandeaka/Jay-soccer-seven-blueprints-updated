"""
Accumulator Builder - Create multi-bet accumulators
"""

import itertools
from typing import List, Dict, Tuple
import pandas as pd


class AccumulatorBuilder:
    """Build accumulators at different odds targets"""
    
    def __init__(self):
        self.accumulators = {
            '2_odds': {'matches': [], 'total_odds': 1.0, 'target': 2.0},
            '4_odds': {'matches': [], 'total_odds': 1.0, 'target': 4.0},
            '7_odds': {'matches': [], 'total_odds': 1.0, 'target': 7.0},
            '10_odds': {'matches': [], 'total_odds': 1.0, 'target': 10.0}
        }
    
    def get_match_odds(self, match: Dict) -> float:
        """Get the odds for the recommended play"""
        play = match.get('play', '')
        blueprint = match.get('blueprint', '')
        
        if 'Home Win' in play:
            return match.get('home_odds', 1.5)
        elif 'Draw' in play:
            return match.get('draw_odds', 3.0)
        elif 'BTTS' in play:
            return match.get('btts_odds', 1.65)
        elif 'Over 1.5' in play:
            return 1.30
        elif 'Over 2.5' in play:
            return 1.75
        elif 'Under 3.5' in play:
            return 1.45
        else:
            return 1.50
    
    def calculate_combination_odds(self, matches: List[Dict]) -> float:
        """Calculate total odds for a combination"""
        odds = 1.0
        for match in matches:
            odds *= self.get_match_odds(match)
        return round(odds, 2)
    
    def build_accumulators(self, analyzed_matches: List[Dict]) -> Dict:
        """
        Build accumulators at different odds levels
        Returns dictionary of accumulator recommendations
        """
        if len(analyzed_matches) < 2:
            return {'error': 'Not enough matches for accumulators'}
        
        # Sort by confidence
        matches = sorted(analyzed_matches, key=lambda x: x['ai_confidence'], reverse=True)
        
        results = {}
        
        # Build 2 odds accumulator (2-3 matches)
        results['2_odds'] = self._build_target_accumulator(
            matches, target_odds=2.0, min_matches=2, max_matches=3
        )
        
        # Build 4 odds accumulator (4 matches)
        results['4_odds'] = self._build_target_accumulator(
            matches, target_odds=4.0, min_matches=4, max_matches=4
        )
        
        # Build 7 odds accumulator (5 matches)
        results['7_odds'] = self._build_target_accumulator(
            matches, target_odds=7.0, min_matches=5, max_matches=5
        )
        
        # Build 10 odds accumulator (5-6 matches)
        results['10_odds'] = self._build_target_accumulator(
            matches, target_odds=10.0, min_matches=5, max_matches=6
        )
        
        return results
    
    def _build_target_accumulator(self, matches: List[Dict], target_odds: float, 
                                   min_matches: int, max_matches: int) -> Dict:
        """Build accumulator to reach target odds"""
        best_combination = None
        best_odds = 0
        
        for n in range(min_matches, max_matches + 1):
            if n > len(matches):
                continue
            
            for combo in itertools.combinations(matches[:10], n):  # Use top 10 matches
                total_odds = self.calculate_combination_odds(list(combo))
                
                # Find closest to target without going too far over
                if target_odds <= total_odds <= target_odds * 1.3:
                    if best_combination is None or abs(total_odds - target_odds) < abs(best_odds - target_odds):
                        best_combination = list(combo)
                        best_odds = total_odds
        
        if best_combination:
            return {
                'matches': best_combination,
                'total_odds': best_odds,
                'target_odds': target_odds,
                'status': 'BUILT'
            }
        else:
            # Fallback: use top matches even if odds exceed target
            fallback = list(matches[:min_matches])
            return {
                'matches': fallback,
                'total_odds': self.calculate_combination_odds(fallback),
                'target_odds': target_odds,
                'status': 'FALLBACK'
            }
    
    def format_accumulator_message(self, acc_name: str, acc_data: Dict) -> str:
        """Format accumulator for Telegram message"""
        if 'error' in acc_data:
            return ""
        
        message = f"\n📊 {acc_name.upper()} ACCUMULATOR\n"
        message += f"🎯 Target: {acc_data['target_odds']} odds | 📈 Total: {acc_data['total_odds']} odds\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for i, match in enumerate(acc_data['matches'], 1):
            odds = self.get_match_odds(match)
            message += f"{i}. {match['match']}\n"
            message += f"   🎯 {match['play']} @ {odds}\n"
            message += f"   📊 AI Confidence: {match['ai_confidence']}%\n\n"
        
        return message
