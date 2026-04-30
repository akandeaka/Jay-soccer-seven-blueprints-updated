"""
Accumulator Builder - Groups filtered matches into multi-bets
"""

import pandas as pd
import itertools
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class AccumulatorBuilder:
    """
    Builds accumulators from filtered matches without repeating teams
    """
    
    def __init__(self):
        self.max_attempts = 100  # Max attempts to find valid combinations
    
    def calculate_match_odds(self, match: Dict) -> float:
        """Calculate the odds to use for this match based on prediction type"""
        play = match.get('Play', '').lower()
        
        # Get the appropriate odds based on prediction
        if 'draw' in play or 'x' in play:
            return float(match.get('Draw Odds', 2.0))
        elif 'home' in play or 'straight home' in play:
            return float(match.get('Home Odds', 1.5))
        elif 'away' in play:
            return float(match.get('Away Odds', 2.0))
        elif 'over' in play or 'gg' in play:
            # For over/GG bets, use slightly lower odds as proxy
            return min(float(match.get('Home Odds', 1.8)) * 0.9, 2.0)
        else:
            return float(match.get('Home Odds', 1.8))
    
    def extract_team_names(self, match: Dict) -> Tuple[str, str]:
        """Extract home and away team names from match"""
        match_name = match.get('Match', '')
        if ' vs ' in match_name:
            parts = match_name.split(' vs ')
            return parts[0].strip(), parts[1].strip()
        return match_name, ''
    
    def is_team_used(self, team: str, used_teams: set, match: Dict, existing_picks: List) -> bool:
        """Check if a team is already used, considering different prediction types"""
        if not team:
            return False
        
        # Check if team is in used teams
        if team in used_teams:
            # Check if this is a different prediction type for the same team
            for existing in existing_picks:
                if existing.get('team') == team:
                    # Same team - need different prediction type
                    existing_play = existing.get('play', '').lower()
                    new_play = match.get('Play', '').lower()
                    
                    # Allow if predictions are different
                    if existing_play != new_play:
                        return False  # Not used (different prediction)
                    return True  # Used (same prediction)
            return True
        
        return False
    
    def build_accumulator(self, matches: List[Dict], target_odds: float, max_matches: int = 6) -> Optional[List[Dict]]:
        """
        Build an accumulator with odds close to target_odds
        """
        best_combination = None
        best_odds_diff = float('inf')
        used_teams = set()
        
        # Try different numbers of matches (2 to max_matches)
        for num_matches in range(2, min(max_matches + 1, len(matches) + 1)):
            for combo in itertools.combinations(matches, num_matches):
                # Check for team duplication
                teams_in_combo = set()
                team_conflicts = False
                
                for match in combo:
                    home, away = self.extract_team_names(match)
                    
                    # Check if home or away team already used
                    if home in teams_in_combo or away in teams_in_combo:
                        team_conflicts = True
                        break
                    
                    # Also check against the other match's teams
                    for other_match in combo:
                        if other_match == match:
                            continue
                        other_home, other_away = self.extract_team_names(other_match)
                        if home in [other_home, other_away] or away in [other_home, other_away]:
                            team_conflicts = True
                            break
                    
                    if team_conflicts:
                        break
                    
                    teams_in_combo.add(home)
                    teams_in_combo.add(away)
                
                if team_conflicts:
                    continue
                
                # Calculate combined odds
                combined_odds = 1.0
                for match in combo:
                    combined_odds *= self.calculate_match_odds(match)
                
                # Check if odds are close to target
                odds_diff = abs(combined_odds - target_odds)
                
                if odds_diff < best_odds_diff and combined_odds >= target_odds * 0.8:
                    best_odds_diff = odds_diff
                    best_combination = combo
                    
                    # Early exit if very close
                    if odds_diff < 0.2:
                        break
            
            if best_combination:
                break
        
        return best_combination
    
    def build_all_accumulators(self, filtered_matches: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Build accumulators for 2x, 4x, 7x, and 10x odds
        """
        results = {
            '2_odds': [],
            '4_odds': [],
            '7_odds': [],
            '10_odds': []
        }
        
        used_matches = set()
        all_matches_used = []
        
        # Target odds with some flexibility
        targets = [
            ('2_odds', 2.0, 3),      # 2x accumulator, 2-3 matches
            ('4_odds', 4.0, 4),      # 4x accumulator, 3-4 matches
            ('7_odds', 7.0, 5),      # 7x accumulator, 4-5 matches
            ('10_odds', 10.0, 6)     # 10x accumulator, 5-6 matches
        ]
        
        for acc_name, target_odds, max_matches in targets:
            # Get unused matches
            available_matches = []
            for i, match in enumerate(filtered_matches):
                if i not in used_matches:
                    # Check if teams aren't already used in this accumulator set
                    match_key = f"{match.get('Match', '')}_{match.get('Play', '')}"
                    if match_key not in all_matches_used:
                        available_matches.append((i, match))
            
            if len(available_matches) < 2:
                continue
            
            # Find best combination
            best_combo = None
            best_odds = 0
            best_odds_diff = float('inf')
            
            # Convert to list of matches only
            matches_list = [m for _, m in available_matches]
            
            for num in range(2, min(max_matches + 1, len(matches_list) + 1)):
                for combo in itertools.combinations(matches_list, num):
                    # Check team duplication in this combo
                    teams_in_combo = set()
                    team_conflict = False
                    
                    for match in combo:
                        home, away = self.extract_team_names(match)
                        if home in teams_in_combo or away in teams_in_combo:
                            team_conflict = True
                            break
                        teams_in_combo.add(home)
                        teams_in_combo.add(away)
                    
                    if team_conflict:
                        continue
                    
                    # Calculate odds
                    combined = 1.0
                    for match in combo:
                        combined *= self.calculate_match_odds(match)
                    
                    odds_diff = abs(combined - target_odds)
                    
                    if odds_diff < best_odds_diff and combined >= target_odds * 0.7:
                        best_odds_diff = odds_diff
                        best_combo = combo
                        best_odds = combined
                    
                    if odds_diff < 0.15:
                        break
                
                if best_combo:
                    break
            
            if best_combo:
                results[acc_name] = list(best_combo)
                # Mark used matches
                for match in best_combo:
                    for i, m in enumerate(filtered_matches):
                        if m.get('Match') == match.get('Match') and m.get('Play') == match.get('Play'):
                            used_matches.add(i)
                            match_key = f"{match.get('Match', '')}_{match.get('Play', '')}"
                            all_matches_used.append(match_key)
                            break
        
        return results
    
    def format_accumulator_message(self, accumulators: Dict[str, List[Dict]], total_matches: int) -> str:
        """Format accumulators for Telegram message"""
        
        message = f"""
⚽ ACCUMULATOR BUILDER - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Source: {total_matches} filtered matches
✅ No duplicate teams (different prediction types allowed)

"""
        
        acc_names = {
            '2_odds': ('🎯 2x ODDS ACCUMULATOR', 2),
            '4_odds': ('💰 4x ODDS ACCUMULATOR', 4),
            '7_odds': ('💎 7x ODDS ACCUMULATOR', 7),
            '10_odds': ('🏆 10x ODDS ACCUMULATOR', 10)
        }
        
        for acc_key, (title, target_odds) in acc_names.items():
            matches = accumulators.get(acc_key, [])
            
            if matches:
                # Calculate total odds
                total_odds = 1.0
                for match in matches:
                    total_odds *= self.calculate_match_odds(match)
                
                message += f"""
{title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Target: {target_odds}x | Actual: {total_odds:.2f}x
📋 {len(matches)} selections:

"""
                for i, match in enumerate(matches, 1):
                    odds_value = self.calculate_match_odds(match)
                    play = match.get('Play', 'Unknown')
                    
                    message += f"{i}. {match.get('Match', 'Unknown')}\n"
                    message += f"   🎯 {play}\n"
                    message += f"   📊 Odds: {odds_value:.2f}x\n\n"
                
                message += f"💵 Total Accumulator Odds: {total_odds:.2f}x\n"
                message += f"💰 Potential Return: Stake × {total_odds:.2f}\n"
                message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            else:
                message += f"""
{title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Could not build accumulator (insufficient unique matches)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        message += """
📌 DISCLAIMER:
   • No team appears twice unless prediction type differs
   • Always bet responsibly
   • Past performance doesn't guarantee future results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return message


def test_accumulator_builder():
    """Test the accumulator builder with sample data"""
    
    # Sample filtered matches
    sample_matches = [
        {'Match': 'Entebbe UPPC vs Calvary', 'Play': 'Straight Home Win', 'Home Odds': 1.28, 'Draw Odds': 4.2, 'Away Odds': 12.2},
        {'Match': 'Monastir vs AS Gabes', 'Play': 'Straight Home Win', 'Home Odds': 1.27, 'Draw Odds': 4.35, 'Away Odds': 11.9},
        {'Match': 'Neftchi Fargona vs Kokand 1912', 'Play': 'Straight Home Win', 'Home Odds': 1.24, 'Draw Odds': 5.48, 'Away Odds': 12.1},
        {'Match': 'Tromso vs Brann', 'Play': 'GG / Over 2.5 Goals', 'Home Odds': 1.95, 'Draw Odds': 3.5, 'Away Odds': 3.8},
        {'Match': 'FC Astana vs Tobol', 'Play': 'Over 1.5 Goals', 'Home Odds': 1.8, 'Draw Odds': 3.32, 'Away Odds': 4.13},
        {'Match': 'Den Bosch vs Almere City', 'Play': 'HT 0.5 Goals / Over 2.5 Goals', 'Home Odds': 2.55, 'Draw Odds': 3.6, 'Away Odds': 2.45},
        {'Match': 'Wydad AC vs Yacoub El Mansour', 'Play': 'Home Win', 'Home Odds': 1.30, 'Draw Odds': 4.33, 'Away Odds': 9.0},
        {'Match': 'Criciuma W vs R4 EC W', 'Play': '1X & Over 1.5 Goals', 'Home Odds': 1.30, 'Draw Odds': 4.6, 'Away Odds': 8.9},
    ]
    
    builder = AccumulatorBuilder()
    accumulators = builder.build_all_accumulators(sample_matches)
    
    message = builder.format_accumulator_message(accumulators, len(sample_matches))
    print(message)
    
    return accumulators


if __name__ == "__main__":
    test_accumulator_builder()
