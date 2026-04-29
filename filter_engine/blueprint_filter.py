"""
Core Filter Engine for Blueprint Results
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional


class BlueprintFilterEngine:
    def __init__(self):
        self.blueprint_weights = {
            'BP1': 95, 'BP2': 85, 'BP3': 80,
            'BP4': 65, 'BP5': 60, 'BP6': 40, 'BP7': 55
        }
        self.competition_weights = {
            'Champions League': 90, 'Eredivisie': 85,
            'Copa Libertadores': 85, 'Copa Sudamericana': 80,
            'J1 League': 80, 'Serie A': 85, 'LaLiga': 85,
            'U20': 0, 'Women': 0, 'Reserve League': 0
        }
    
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Parse the raw blueprint text into structured data"""
        matches = []
        
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
            
            bp_match = re.search(r'BP(\d+)', header)
            blueprint = f"BP{bp_match.group(1)}" if bp_match else "Unknown"
            color = '🟢' if '🟢' in header else '🟡' if '🟡' in header else '🔴'
            
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
    
    def calculate_confidence_score(self, match: Dict) -> float:
        """Calculate final confidence score (0-100)"""
        bp_weight = self.blueprint_weights.get(match['blueprint'], 50)
        
        # Simple confidence calculation for testing
        if match['blueprint'] == 'BP1':
            confidence = 85
        elif match['blueprint'] == 'BP2':
            confidence = 75
        elif match['blueprint'] == 'BP3':
            confidence = 70
        elif match['blueprint'] == 'BP4':
            confidence = 60
        elif match['blueprint'] == 'BP5':
            confidence = 55
        elif match['blueprint'] == 'BP6':
            confidence = 40
        else:
            confidence = 50
        
        # Adjust based on color
        if match['color'] == '🟢':
            confidence += 5
        elif match['color'] == '🔴':
            confidence -= 5
        
        return min(100, max(0, confidence))
    
    def process_matches(self, matches: List[Dict]) -> pd.DataFrame:
        """Process all matches and return ranked results"""
        results = []
        
        for match in matches:
            confidence = self.calculate_confidence_score(match)
            
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
                'Status': 'PASS' if confidence >= 50 else 'FAIL'
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values('Confidence', ascending=False)
        
        return df