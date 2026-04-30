"""
Core Filter Engine for Blueprint Results - SIMPLIFIED PARSER
"""

import re
import pandas as pd
from typing import Dict, List


class BlueprintFilterEngine:
    def __init__(self):
        self.blueprint_weights = {
            'BP1': 95, 'BP2': 85, 'BP3': 80,
            'BP4': 65, 'BP5': 60, 'BP6': 40, 'BP7': 55
        }
    
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Simple parser that works with your blueprint format"""
        matches = []
        
        # Split into lines
        lines = text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for BP pattern (e.g., "BP6 1. THE STRONG DRAW" or "🟡 BP6: THE STRONG DRAW")
            bp_match = re.search(r'BP([1-7])', line)
            
            if bp_match and not line.startswith('📊'):
                bp_num = bp_match.group(1)
                blueprint = f"BP{bp_num}"
                
                # Determine color
                if bp_num in ['1', '2']:
                    color = '🟢'
                elif bp_num in ['3', '4', '5', '7']:
                    color = '🟡'
                else:
                    color = '🔴'
                
                # Look ahead for match details (next 5-6 lines)
                home_team = ""
                away_team = ""
                league = ""
                home_odds = 0.0
                draw_odds = 0.0
                away_odds = 0.0
                play = ""
                risk = ""
                
                # Search through next 10 lines for data
                for j in range(i+1, min(i+10, len(lines))):
                    data_line = lines[j].strip()
                    
                    # Check for vs pattern (teams)
                    if ' vs ' in data_line and not home_team:
                        parts = data_line.split(' vs ')
                        home_team = parts[0].strip()
                        away_team = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Check for league (usually a single line without special chars)
                    elif data_line and not league and not any(x in data_line for x in ['Odds:', 'Play:', 'Risk:', '🏟️', '🏆', '📊', '🎯', '⚠️']):
                        if 'Europa' in data_line or 'League' in data_line or 'Conference' in data_line or 'Premier' in data_line:
                            league = data_line
                    
                    # Check for odds
                    elif 'Odds:' in data_line or '📊' in data_line:
                        odds_match = re.search(r'([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)', data_line)
                        if odds_match:
                            home_odds = float(odds_match.group(1))
                            draw_odds = float(odds_match.group(2))
                            away_odds = float(odds_match.group(3))
                    
                    # Check for play
                    elif 'Play:' in data_line or '🎯' in data_line:
                        play_match = re.search(r'Play:\s*(.+?)(?:\n|$)', data_line)
                        if play_match:
                            play = play_match.group(1).strip()
                        else:
                            # Remove emoji and prefix
                            play = re.sub(r'[🎯⚠️]', '', data_line).replace('Play:', '').strip()
                    
                    # Check for risk
                    elif 'Risk:' in data_line or '⚠️' in data_line:
                        risk_match = re.search(r'Risk:\s*(.+?)(?:\n|$)', data_line)
                        if risk_match:
                            risk = risk_match.group(1).strip()
                        else:
                            risk = re.sub(r'[🎯⚠️]', '', data_line).replace('Risk:', '').strip()
                    
                    # If we have all data, break
                    if home_team and league and home_odds > 0:
                        break
                
                if home_team and home_odds > 0:
                    matches.append({
                        'blueprint': blueprint,
                        'color': color,
                        'match': f"{home_team} vs {away_team}",
                        'league': league if league else "Unknown",
                        'home_odds': home_odds,
                        'draw_odds': draw_odds,
                        'away_odds': away_odds,
                        'play': play if play else "Match",
                        'risk': risk if risk else "Moderate"
                    })
                
                # Move to next match (skip ahead)
                i += 6
                continue
            
            i += 1
        
        print(f"✅ Parser found {len(matches)} matches")
        return matches
    
    def calculate_confidence_score(self, match: Dict) -> float:
        """Calculate confidence score based on blueprint and odds"""
        bp_weight = self.blueprint_weights.get(match['blueprint'], 50)
        
        # Base score by blueprint
        if match['blueprint'] == 'BP1':
            base = 85
        elif match['blueprint'] == 'BP2':
            base = 75
        elif match['blueprint'] == 'BP3':
            base = 70
        elif match['blueprint'] == 'BP4':
            base = 65
        elif match['blueprint'] == 'BP5':
            base = 60
        elif match['blueprint'] == 'BP6':
            base = 45
        elif match['blueprint'] == 'BP7':
            base = 55
        else:
            base = 50
        
        # Adjust based on color
        if match['color'] == '🟢':
            base += 5
        elif match['color'] == '🔴':
            base -= 5
        
        return min(100, max(0, base))
    
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
                'Risk': match['risk']
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('Confidence', ascending=False)
