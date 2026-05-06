"""
Accumulator Builder - Create multi-bet accumulators without duplicate teams
"""

import itertools
from typing import List, Dict, Tuple
import pandas as pd


class AccumulatorBuilder:
    """Build accumulators at different odds targets without duplicate teams"""
    
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
        """Extract team names from a match"""
        match_name = match.get('match', '')
        if ' vs ' in match_name:
            return match_name.split(' vs ')
        return [match_name]
    
    def remove_duplicate_teams(self, matches: List[Dict]) -> List[Dict]:
        """
        Remove matches that share the same team
        Ensures no team appears more than once in accumulators
        """
        seen_teams = set()
        unique_matches = []
        
        for match in matches:
            teams = self.extract_teams(match)
            # Check if any team has been seen before
            if not any(team in seen_teams for team in teams):
                unique_matches.append(match)
                seen_teams.update(teams)
        
        return unique_matches
    
    def calculate_combination_odds(self, matches: List[Dict]) -> float:
        """Calculate total odds for a combination"""
        odds = 1.0
        for match in matches:
            odds *= self.get_match_odds(match)
        return round(odds, 2)
    
    def build_accumulators(self, analyzed_matches: List[Dict]) -> Dict:
        """
        Build accumulators at different odds levels
        Ensures no duplicate teams across any accumulator
        """
        if len(analyzed_matches) < 2:
            return {'error': 'Not enough matches for accumulators'}
        
        # Remove duplicate teams first
        unique_matches = self.remove_duplicate_teams(analyzed_matches)
        
        if len(unique_matches) < 2:
            return {'error': 'Not enough unique teams for accumulators'}
        
        # Sort by confidence
        matches = sorted(unique_matches, key=lambda x: x.get('ai_confidence', 0), reverse=True)
        
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
        """Build accumulator to reach target odds without duplicate teams"""
        best_combination = None
        best_odds = 0
        
        for n in range(min_matches, min(max_matches, len(matches)) + 1):
            for combo in itertools.combinations(matches[:12], n):  # Top 12 matches
                # Check for duplicate teams in this combination
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
                    continue  # Skip this combination
                
                total_odds = self.calculate_combination_odds(list(combo))
                
                # Find closest to target
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
            # Fallback: use top matches without duplicates
            fallback = []
            seen_teams = set()
            for match in matches:
                teams = self.extract_teams(match)
                if not any(team in seen_teams for team in teams):
                    fallback.append(match)
                    seen_teams.update(teams)
                    if len(fallback) >= min_matches:
                        break
            
            if len(fallback) >= min_matches:
                return {
                    'matches': fallback,
                    'total_odds': self.calculate_combination_odds(fallback),
                    'target_odds': target_odds,
                    'status': 'FALLBACK'
                }
            else:
                return {'error': f'Not enough unique teams for {target_odds}x accumulator'}
    
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
            message += f"   📊 AI Confidence: {match.get('ai_confidence', match.get('confidence', 50)):.0f}%\n\n"
        
        return message
