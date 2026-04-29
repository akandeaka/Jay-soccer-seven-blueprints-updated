"""
Core Filter Engine for Blueprint Results
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional
from .config import FilterConfig


class BlueprintFilterEngine:
    def __init__(self):
        self.blueprint_weights = FilterConfig.BLUEPRINT_WEIGHTS
        self.competition_weights = FilterConfig.COMPETITION_WEIGHTS
        
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Parse the raw blueprint text into structured data"""
        matches = []
        
        # Pattern to extract each match block
        pattern = r'([🟢🟡🔴]+\s*\d+\.\s*BP\d+:\s*[^\n]+)\n\s*🏟️\s*([^\n]+)\n\s*🏆\s*([^\n]+)\n\s*📊\s*Odds:\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\n\s*🎯\s*Play:\s*([^\n]+)\n\s*⚠️\s*Risk:\s*([^\n]+)'
        
        matches_raw = re.findall(pattern, text, re.MULTILINE)
        
        for match in matches_raw:
            header = match[0]
            teams = match[1]
            league = match[2]
            home_odds = float(match[3])
            draw_odds = float(match[4])
            away_odds = float(match[5])
            play = match[6]
            risk = match[7]
            
            # Extract blueprint number
            bp_match = re.search(r'BP(\d+)', header)
            blueprint = f"BP{bp_match.group(1)}" if bp_match else "Unknown"
            
            # Extract color indicator
            color = '🟢' if '🟢' in header else '🟡' if '🟡' in header else '🔴'
            
            # Split teams
            teams_split = teams.split(' vs ')
            home_team = teams_split[0] if len(teams_split) > 0 else teams
            away_team = teams_split[1] if len(teams_split) > 1 else ''
            
            matches.append({
                'raw_header': header,
                'blueprint': blueprint,
                'color': color,
                'home_team': home_team,
                'away_team': away_team,
                'match': f"{home_team} vs {away_team}",
                'league': league,
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds,
                'play': play,
                'risk': risk
            })
        
        return matches
    
    def calculate_odds_value_score(self, match: Dict) -> float:
        """Calculate odds value score based on blueprint type"""
        blueprint = match['blueprint']
        home_odds = match['home_odds']
        draw_odds = match['draw_odds']
        play = match['play']
        
        if blueprint in ['BP1', 'BP2']:
            if home_odds <= 1.85:
                return 90
            elif home_odds <= 2.20:
                return 70
            elif home_odds <= 2.50:
                return 50
            else:
                return 30
                
        elif blueprint == 'BP3':
            if home_odds <= 1.50:
                return 85
            elif home_odds <= 1.80:
                return 70
            else:
                return 50
                
        elif blueprint == 'BP5':
            if home_odds <= 1.85:
                return 75
            else:
                return 55
                
        elif blueprint == 'BP6':
            if 2.80 <= draw_odds <= 3.40:
                return 80
            elif 2.50 <= draw_odds <= 3.80:
                return 60
            else:
                return 30
                
        elif blueprint == 'BP7':
            if 'GG' in play or 'Over 2.5' in play:
                return 65
            else:
                return 55
        else:
            return 50
    
    def calculate_form_score(self, match: Dict) -> float:
        """Calculate form score using odds as proxy"""
        blueprint = match['blueprint']
        home_odds = match['home_odds']
        away_odds = match['away_odds']
        draw_odds = match['draw_odds']
        
        if blueprint in ['BP1', 'BP2', 'BP3', 'BP5']:
            if home_odds < 1.60:
                return 85
            elif home_odds < 2.00:
                return 70
            elif home_odds < 2.50:
                return 55
            else:
                return 40
                
        elif blueprint == 'BP6':
            if abs(home_odds - away_odds) < 0.5 and draw_odds < 3.50:
                return 75
            elif abs(home_odds - away_odds) < 1.0:
                return 60
            else:
                return 40
                
        elif blueprint == 'BP7':
            if abs(home_odds - away_odds) < 1.0:
                return 70
            else:
                return 55
        else:
            return 50
    
    def calculate_goals_score(self, match: Dict) -> float:
        """Calculate goals statistics score"""
        play = match['play']
        home_odds = match['home_odds']
        away_odds = match['away_odds']
        
        if 'Over 1.5' in play or 'Over 2.5' in play or 'GG' in play:
            if home_odds < 2.00 or away_odds < 2.00:
                return 80
            elif home_odds < 2.50 or away_odds < 2.50:
                return 65
            else:
                return 50
        elif 'Under 3.5' in play:
            if home_odds > 2.00:
                return 75
            else:
                return 55
        else:
            return 60
    
    def calculate_competition_score(self, match: Dict) -> float:
        """Calculate competition trust score"""
        league = match['league']
        
        for keyword, weight in self.competition_weights.items():
            if keyword.lower() in league.lower():
                return weight
        
        return 50
    
    def apply_filters(self, match: Dict) -> Tuple[bool, List[str]]:
        """Apply all filter layers and return (pass, reasons)"""
        reasons = []
        
        blueprint = match['blueprint']
        home_odds = match['home_odds']
        draw_odds = match['draw_odds']
        play = match['play']
        
        # Odds consistency filters
        if blueprint in ['BP1', 'BP2', 'BP3']:
            if home_odds > 2.20:
                reasons.append(f"Home odds too high ({home_odds}) for {blueprint}")
        
        elif blueprint == 'BP6':
            if draw_odds > 4.0:
                reasons.append(f"Draw odds too high ({draw_odds}) for BP6")
            elif draw_odds < 2.50:
                reasons.append(f"Draw odds too low ({draw_odds}) for BP6")
        
        # Competition context filter
        comp_score = self.calculate_competition_score(match)
        if comp_score == 0:
            reasons.append(f"Low-trust competition: {match['league']}")
        
        # BP7 in low-trust leagues
        if blueprint == 'BP7' and comp_score < 50:
            reasons.append(f"BP7 in low-trust league: {match['league']}")
        
        # BP6 with mismatched odds
        if blueprint == 'BP6':
            odds_diff = abs(match['home_odds'] - match['away_odds'])
            if odds_diff > 1.5:
                reasons.append(f"Odds too mismatched for draw ({odds_diff:.2f} diff)")
        
        return len(reasons) == 0, reasons
    
    def calculate_confidence_score(self, match: Dict) -> float:
        """Calculate final confidence score (0-100)"""
        passes, reasons = self.apply_filters(match)
        if not passes:
            return 0
        
        bp_weight = self.blueprint_weights.get(match['blueprint'], 50)
        odds_score = self.calculate_odds_value_score(match)
        form_score = self.calculate_form_score(match)
        goals_score = self.calculate_goals_score(match)
        comp_score = self.calculate_competition_score(match)
        
        final_score = (
            (bp_weight * 0.35) +
            (odds_score * 0.25) +
            (form_score * 0.20) +
            (goals_score * 0.10) +
            (comp_score * 0.10)
        )
        
        if match['color'] == '🟢':
            final_score += 5
        elif match['color'] == '🔴':
            final_score -= 5
        
        return min(100, max(0, final_score))
    
    def process_matches(self, matches: List[Dict]) -> pd.DataFrame:
        """Process all matches and return ranked results"""
        results = []
        
        for match in matches:
            confidence = self.calculate_confidence_score(match)
            passes, reasons = self.apply_filters(match)
            
            if confidence >= 80:
                tier = "🔥 GOLD"
            elif confidence >= 65:
                tier = "✅ SILVER"
            elif confidence >= 50:
                tier = "⚠️ BRONZE"
            else:
                tier = "❌ REJECT"
            
            results.append({
                'Tier': tier,
                'Confidence': round(confidence, 1),
                'Blueprint': match['blueprint'],
                'Match': match['match'],
                'League': match['league'],
                'Play': match['play'],
                'Home Odds': match['home_odds'],
                'Draw Odds': match['draw_odds'],
                'Away Odds': match['away_odds'],
                'Risk': match['risk'],
                'Status': 'PASS' if passes else 'FAIL',
                'Filter Reasons': '; '.join(reasons) if reasons else 'None'
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values('Confidence', ascending=False)
        
        return df
