"""
Blueprint Filter Engine - Using YOUR Original 7 Blueprint Rules
"""

import pandas as pd
from typing import Dict, List


class BlueprintFilterEngine:
    
    def classify_blueprint(self, match: Dict) -> Dict:
        """Classify a match into one of YOUR 7 blueprints"""
        
        home_odds = match.get('home_odds', 0)
        draw_odds = match.get('draw_odds', 0)
        away_odds = match.get('away_odds', 0)
        
        # BP1: Home 1.20-1.29, Away ≥ 10.0
        if 1.20 <= home_odds <= 1.29 and away_odds >= 10.0:
            return {
                'blueprint': 'BP1',
                'name': 'THE ELITE HOME BANKER',
                'play': 'Straight Home Win',
                'risk': 'Ultra-Low',
                'color': '🟢'
            }
        
        # BP2: Home 1.30-1.36, Away ≥ 9.0
        if 1.30 <= home_odds <= 1.36 and away_odds >= 9.0:
            return {
                'blueprint': 'BP2',
                'name': 'THE PRIMARY FAVORITE',
                'play': 'Home Win',
                'risk': 'Low',
                'color': '🟢'
            }
        
        # BP3: Home 1.30-1.36, Away 7.0-8.99
        if 1.30 <= home_odds <= 1.36 and 7.0 <= away_odds <= 8.99:
            return {
                'blueprint': 'BP3',
                'name': 'THE MODERATE FAVORITE SAFETY',
                'play': '1X & Over 1.5 Goals',
                'risk': 'Low-Moderate',
                'color': '🟡'
            }
        
        # BP4: Home 1.72-1.80
        if 1.72 <= home_odds <= 1.80:
            return {
                'blueprint': 'BP4',
                'name': 'THE GOAL ENGINE',
                'play': 'Over 1.5 Goals',
                'risk': 'Moderate',
                'color': '🟡'
            }
        
        # BP5: Home 1.90-2.02
        if 1.90 <= home_odds <= 2.02:
            return {
                'blueprint': 'BP5',
                'name': 'THE DEFENSIVE TRAP',
                'play': '1X & Under 3.5 FT',
                'risk': 'Moderate (Value Pick)',
                'color': '🟡'
            }
        
        # BP6: Draw 2.75-3.39
        if 2.75 <= draw_odds <= 3.39:
            return {
                'blueprint': 'BP6',
                'name': 'THE STRONG DRAW',
                'play': 'Full Time Draw (X) Potential',
                'risk': 'High (Strategic)',
                'color': '🔴'
            }
        
        # BP7A: Draw 3.40-3.56
        if 3.40 <= draw_odds <= 3.56:
            return {
                'blueprint': 'BP7',
                'name': 'THE HIGH-SCORING SIGNALS (A)',
                'play': 'GG / Over 2.5 Goals',
                'risk': 'Moderate-High',
                'color': '🟡'
            }
        
        # BP7B: Draw 3.60-3.75
        if 3.60 <= draw_odds <= 3.75:
            return {
                'blueprint': 'BP7',
                'name': 'THE HIGH-SCORING SIGNALS (B)',
                'play': 'HT 0.5 Goals / Over 2.5 Goals',
                'risk': 'Moderate-High',
                'color': '🟡'
            }
        
        # Not qualified for any blueprint
        return None
    
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Parse blueprint text into match objects"""
        matches = []
        lines = text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for match data
            if ' vs ' in line and not line.startswith('📊'):
                # This line has teams
                teams = line
                i += 1
                
                # Get league
                league = lines[i].strip() if i < len(lines) else "Unknown"
                i += 1
                
                # Get odds
                odds_line = lines[i].strip() if i < len(lines) else ""
                i += 1
                
                # Parse odds
                import re
                odds_match = re.search(r'([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)', odds_line)
                if odds_match:
                    home_odds = float(odds_match.group(1))
                    draw_odds = float(odds_match.group(2))
                    away_odds = float(odds_match.group(3))
                    
                    # Get play
                    play_line = lines[i].strip() if i < len(lines) else ""
                    i += 1
                    
                    teams_parts = teams.split(' vs ')
                    home_team = teams_parts[0] if len(teams_parts) > 0 else ""
                    away_team = teams_parts[1] if len(teams_parts) > 1 else ""
                    
                    match_obj = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'match': f"{home_team} vs {away_team}",
                        'league': league,
                        'home_odds': home_odds,
                        'draw_odds': draw_odds,
                        'away_odds': away_odds,
                        'play': play_line.replace('Play:', '').strip() if 'Play:' in play_line else ""
                    }
                    
                    # Classify using your rules
                    bp_info = self.classify_blueprint(match_obj)
                    if bp_info:
                        match_obj.update(bp_info)
                        matches.append(match_obj)
            
            i += 1
        
        return matches
    
    def calculate_confidence_score(self, match: Dict) -> float:
        """Calculate confidence based on blueprint type"""
        confidence_map = {
            'BP1': 95,
            'BP2': 90,
            'BP3': 85,
            'BP4': 75,
            'BP5': 70,
            'BP6': 50,
            'BP7': 60
        }
        return confidence_map.get(match.get('blueprint', 'BP7'), 50)
    
    def process_matches(self, matches: List[Dict]) -> pd.DataFrame:
        """Process matches and return ranked results"""
        results = []
        
        for match in matches:
            confidence = self.calculate_confidence_score(match)
            
            if confidence >= 85:
                tier = "🔥 GOLD"
            elif confidence >= 70:
                tier = "✅ SILVER"
            elif confidence >= 50:
                tier = "⚠️ BRONZE"
            else:
                tier = "❌ REJECT"
            
            results.append({
                'Tier': tier,
                'Confidence': confidence,
                'Blueprint': match.get('blueprint', 'Unknown'),
                'Match': match.get('match', ''),
                'League': match.get('league', 'Unknown'),
                'Play': match.get('play', ''),
                'Home Odds': match.get('home_odds', 0),
                'Draw Odds': match.get('draw_odds', 0),
                'Away Odds': match.get('away_odds', 0),
                'Risk': match.get('risk', ''),
                'Blueprint Name': match.get('name', '')
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('Confidence', ascending=False)
