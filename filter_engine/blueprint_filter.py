"""
Core Filter Engine for Blueprint Results - UPDATED PARSER
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
    
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Parse blueprint text - FLEXIBLE PARSER that works with your format"""
        matches = []
        
        # Try multiple patterns to extract matches
        
        # Pattern 1: With emojis (original format)
        pattern1 = r'([🟢🟡🔴]+\s*\d+\.\s*BP\d+:\s*[^\n]+)\n\s*🏟️\s*([^\n]+)\n\s*🏆\s*([^\n]+)\n\s*📊\s*Odds:\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\n\s*🎯\s*Play:\s*([^\n]+)\n\s*⚠️\s*Risk:\s*([^\n]+)'
        
        # Pattern 2: Without emojis (your current format)
        # Looks for: "BP6 1. THE STRONG DRAW" then next lines with match data
        pattern2 = r'BP(\d+)\s+\d+\.\s+[^\n]+\n([^\n]+)\n([^\n]+)\nOdds:\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\nPlay:\s*([^\n]+)\nRisk:\s*([^\n]+)'
        
        # Try pattern1 first
        matches_raw = re.findall(pattern1, text, re.MULTILINE)
        
        if matches_raw:
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
                    'blueprint': blueprint,
                    'color': color,
                    'match': f"{home_team} vs {away_team}",
                    'league': league,
                    'home_odds': home_odds,
                    'draw_odds': draw_odds,
                    'away_odds': away_odds,
                    'play': play,
                    'risk': risk
                })
        
        # If pattern1 found nothing, try pattern2
        if not matches_raw:
            matches_raw2 = re.findall(pattern2, text, re.MULTILINE)
            
            for match in matches_raw2:
                bp_num = match[0]
                teams = match[1].strip()
                league = match[2].strip()
                home_odds = float(match[3])
                draw_odds = float(match[4])
                away_odds = float(match[5])
                play = match[6].strip()
                risk = match[7].strip()
                
                blueprint = f"BP{bp_num}"
                
                # Determine color based on BP number
                if bp_num in ['1', '2']:
                    color = '🟢'
                elif bp_num in ['3', '4', '5', '7']:
                    color = '🟡'
                else:
                    color = '🔴'
                
                teams_split = teams.split(' vs ')
                home_team = teams_split[0] if len(teams_split) > 0 else teams
                away_team = teams_split[1] if len(teams_split) > 1 else ''
                
                matches.append({
                    'blueprint': blueprint,
                    'color': color,
                    'match': f"{home_team} vs {away_team}",
                    'league': league,
                    'home_odds': home_odds,
                    'draw_odds': draw_odds,
                    'away_odds': away_odds,
                    'play': play,
                    'risk': risk
                })
        
        # If still no matches, try a simpler line-by-line approach
        if not matches:
            print("⚠️ Pattern matching failed, trying line-by-line parser...")
            matches = self._parse_line_by_line(text)
        
        return matches
    
    def _parse_line_by_line(self, text: str) -> List[Dict]:
        """Fallback parser - line by line"""
        matches = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for BP pattern
            bp_match = re.search(r'BP(\d+)', line)
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
                
                # Get next lines for match data
                if i + 4 < len(lines):
                    teams_line = lines[i + 1].strip()
                    league_line = lines[i + 2].strip()
                    odds_line = lines[i + 3].strip()
                    play_line = lines[i + 4].strip() if i + 4 < len(lines) else ""
                    risk_line = lines[i + 5].strip() if i + 5 < len(lines) else ""
                    
                    # Extract teams
                    teams_split = teams_line.split(' vs ')
                    home_team = teams_split[0] if len(teams_split) > 0 else teams_line
                    away_team = teams_split[1] if len(teams_split) > 1 else ''
                    
                    # Extract odds
                    odds_match = re.search(r'Odds:\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)', odds_line)
                    if odds_match:
                        home_odds = float(odds_match.group(1))
                        draw_odds = float(odds_match.group(2))
                        away_odds = float(odds_match.group(3))
                        
                        # Extract play
                        play = play_line.replace('Play:', '').strip() if 'Play:' in play_line else ''
                        risk = risk_line.replace('Risk:', '').strip() if 'Risk:' in risk_line else ''
                        
                        matches.append({
                            'blueprint': blueprint,
                            'color': color,
                            'match': f"{home_team} vs {away_team}",
                            'league': league_line,
                            'home_odds': home_odds,
                            'draw_odds': draw_odds,
                            'away_odds': away_odds,
                            'play': play,
                            'risk': risk
                        })
                        
                        i += 6
                        continue
            i += 1
        
        return matches
    
    def calculate_confidence_score(self, match: Dict) -> float:
        """Calculate final confidence score (0-100)"""
        bp_weight = self.blueprint_weights.get(match['blueprint'], 50)
        
        # Simple confidence calculation
        if match['blueprint'] == 'BP1':
            base = 85
        elif match['blueprint'] == 'BP2':
            base = 75
        elif match['blueprint'] == 'BP3':
            base = 70
        elif match['blueprint'] == 'BP6':
            base = 40
        elif match['blueprint'] == 'BP7':
            base = 55
        else:
            base = 60
        
        if match['color'] == '🟢':
            base += 5
        elif match['color'] == '🔴':
            base -= 5
        
        # Adjust based on odds
        if match['home_odds'] < 1.5:
            base += 10
        elif match['home_odds'] > 3.0:
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
