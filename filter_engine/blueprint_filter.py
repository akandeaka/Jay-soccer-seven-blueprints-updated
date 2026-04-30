"""
Blueprint Filter Engine - Using YOUR Original 7 Blueprint Rules
"""

import re
import pandas as pd
from typing import Dict, List


class BlueprintFilterEngine:
    
    def classify_blueprint(self, home_odds: float, draw_odds: float, away_odds: float) -> Dict:
        """Classify match using YOUR original 7 blueprint rules"""
        
        # BP1: Home 1.20-1.29, Away >= 10.0
        if 1.20 <= home_odds <= 1.29 and away_odds >= 10.0:
            return {'bp': 'BP1', 'play': 'Straight Home Win', 'risk': 'Ultra-Low', 'color': '🟢'}
        
        # BP2: Home 1.30-1.36, Away >= 9.0
        if 1.30 <= home_odds <= 1.36 and away_odds >= 9.0:
            return {'bp': 'BP2', 'play': 'Home Win', 'risk': 'Low', 'color': '🟢'}
        
        # BP3: Home 1.30-1.36, Away 7.0-8.99
        if 1.30 <= home_odds <= 1.36 and 7.0 <= away_odds <= 8.99:
            return {'bp': 'BP3', 'play': '1X & Over 1.5 Goals', 'risk': 'Low-Moderate', 'color': '🟡'}
        
        # BP4: Home 1.72-1.80
        if 1.72 <= home_odds <= 1.80:
            return {'bp': 'BP4', 'play': 'Over 1.5 Goals', 'risk': 'Moderate', 'color': '🟡'}
        
        # BP5: Home 1.90-2.02
        if 1.90 <= home_odds <= 2.02:
            return {'bp': 'BP5', 'play': '1X & Under 3.5 FT', 'risk': 'Moderate (Value Pick)', 'color': '🟡'}
        
        # BP6: Draw 2.75-3.39
        if 2.75 <= draw_odds <= 3.39:
            return {'bp': 'BP6', 'play': 'Full Time Draw (X) Potential', 'risk': 'High (Strategic)', 'color': '🔴'}
        
        # BP7A: Draw 3.40-3.56
        if 3.40 <= draw_odds <= 3.56:
            return {'bp': 'BP7', 'play': 'GG / Over 2.5 Goals', 'risk': 'Moderate-High', 'color': '🟡'}
        
        # BP7B: Draw 3.60-3.75
        if 3.60 <= draw_odds <= 3.75:
            return {'bp': 'BP7', 'play': 'HT 0.5 Goals / Over 2.5 Goals', 'risk': 'Moderate-High', 'color': '🟡'}
        
        return None
    
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Parse blueprint text into matches"""
        matches = []
        lines = text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Find blueprint header
            if line and any(bp in line for bp in ['BP1', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7']):
                bp_match = re.search(r'(BP[1-7])', line)
                blueprint = bp_match.group(1) if bp_match else "Unknown"
                
                if '🟢' in line:
                    color = '🟢'
                elif '🔴' in line:
                    color = '🔴'
                else:
                    color = '🟡'
                
                i += 1
                
                # Teams line
                teams_line = lines[i].strip() if i < len(lines) else ""
                teams_match = re.search(r'🏟️\s*(.+?)\s*vs\s*(.+)', teams_line)
                if teams_match:
                    match_name = f"{teams_match.group(1).strip()} vs {teams_match.group(2).strip()}"
                else:
                    match_name = "Unknown vs Unknown"
                
                i += 1
                
                # League line
                league_line = lines[i].strip() if i < len(lines) else ""
                league = league_line.replace('🏆', '').strip()
                
                i += 1
                
                # Odds line
                odds_line = lines[i].strip() if i < len(lines) else ""
                odds_match = re.search(r'([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)', odds_line)
                if odds_match:
                    home_odds = float(odds_match.group(1))
                    draw_odds = float(odds_match.group(2))
                    away_odds = float(odds_match.group(3))
                else:
                    home_odds = draw_odds = away_odds = 0
                
                i += 1
                
                # Play line
                play_line = lines[i].strip() if i < len(lines) else ""
                play = play_line.replace('🎯', '').replace('Play:', '').strip()
                
                i += 1
                
                # Risk line
                risk_line = lines[i].strip() if i < len(lines) else ""
                risk = risk_line.replace('⚠️', '').replace('Risk:', '').strip()
                
                i += 2  # Skip empty line
                
                if home_odds > 0:
                    matches.append({
                        'blueprint': blueprint,
                        'color': color,
                        'match': match_name,
                        'league': league,
                        'home_odds': home_odds,
                        'draw_odds': draw_odds,
                        'away_odds': away_odds,
                        'play': play,
                        'risk': risk
                    })
            else:
                i += 1
        
        return matches
    
    def calculate_confidence(self, blueprint: str) -> int:
        scores = {'BP1': 95, 'BP2': 90, 'BP3': 85, 'BP4': 75, 'BP5': 70, 'BP6': 50, 'BP7': 60}
        return scores.get(blueprint, 50)
    
    def process_matches(self, matches: List[Dict]) -> pd.DataFrame:
        results = []
        for match in matches:
            confidence = self.calculate_confidence(match['blueprint'])
            
            if confidence >= 85:
                tier = "🔥 GOLD"
            elif confidence >= 70:
                tier = "✅ SILVER"
            else:
                tier = "⚠️ BRONZE"
            
            results.append({
                'Tier': tier,
                'Confidence': confidence,
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
