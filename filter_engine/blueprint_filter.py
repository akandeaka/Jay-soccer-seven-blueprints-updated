"""
Blueprint Filter Engine - Updated with 8 Blueprint Rules (BP1-BP8)
"""

import re
import pandas as pd
from typing import Dict, List, Optional


class BlueprintFilterEngine:
    
    # Define high-scoring leagues for BP8
    HIGH_SCORING_LEAGUES = [
        'Bundesliga', 'Eredivisie', 'Premier League', 
        'Serie A', 'Ligue 1', 'Bundesliga', 'EPL',
        'Premiership', 'Serie A', 'Ligue 1'
    ]
    
    def classify_blueprint(self, home_odds: float, draw_odds: float, away_odds: float, 
                          league: str = "", btts_record: Optional[str] = None) -> Dict:
        """
        Classify match using 8 blueprint rules
        
        Parameters:
        - home_odds: Home team odds
        - draw_odds: Draw odds
        - away_odds: Away team odds
        - league: League name (for BP8 filtering)
        - btts_record: GG record e.g., "3/5" or "7/10" (for BP7)
        """
        
        # BP1: Home 1.20-1.29, Away >= 10.0
        if 1.20 <= home_odds <= 1.29 and away_odds >= 10.0:
            return {'bp': 'BP1', 'play': 'Straight Home Win', 'risk': 'Ultra-Low', 'color': '🟢', 'confidence': 95}
        
        # BP2: Home 1.30-1.36, Away >= 9.0
        if 1.30 <= home_odds <= 1.36 and away_odds >= 9.0:
            return {'bp': 'BP2', 'play': 'Home Win', 'risk': 'Low', 'color': '🟢', 'confidence': 90}
        
        # BP3: Home 1.30-1.36, Away 7.0-8.99
        if 1.30 <= home_odds <= 1.36 and 7.0 <= away_odds <= 8.99:
            return {'bp': 'BP3', 'play': '1X & Over 1.5 Goals', 'risk': 'Low-Moderate', 'color': '🟡', 'confidence': 85}
        
        # BP4: Home 1.72-1.80
        if 1.72 <= home_odds <= 1.80:
            return {'bp': 'BP4', 'play': 'Over 1.5 Goals', 'risk': 'Moderate', 'color': '🟡', 'confidence': 75}
        
        # BP5: Home 1.90-2.02
        if 1.90 <= home_odds <= 2.02:
            return {'bp': 'BP5', 'play': '1X & Under 3.5 FT', 'risk': 'Moderate (Value Pick)', 'color': '🟡', 'confidence': 70}
        
        # BP6: Draw 2.75-3.39
        if 2.75 <= draw_odds <= 3.39:
            return {'bp': 'BP6', 'play': 'Full Time Draw (X) Potential', 'risk': 'High (Strategic)', 'color': '🔴', 'confidence': 50}
        
        # BP7: BTTS Value Spot - Odds 1.40-1.69 with GG record
        if 1.40 <= draw_odds <= 1.69:  # Using draw_odds as BTTS odds
            if self.check_btts_record(btts_record):
                return {'bp': 'BP7', 'play': 'Both Teams to Score (GG)', 'risk': 'Low-Moderate', 'color': '🟡', 'confidence': 75}
        
        # BP8: High-Scoring Signals - Draw 3.60-3.75 + High-scoring league
        if 3.60 <= draw_odds <= 3.75:
            if self.is_high_scoring_league(league):
                return {'bp': 'BP8', 'play': 'HT 0.5 Goals / Over 2.5 Goals', 'risk': 'Moderate-High', 'color': '🟡', 'confidence': 60}
        
        return None
    
    def check_btts_record(self, btts_record: Optional[str]) -> bool:
        """Check if GG record meets BP7 criteria (3/5 or 7/10)"""
        if btts_record is None:
            return False
        
        try:
            if '/' in btts_record:
                hits, total = map(int, btts_record.split('/'))
                if total == 5 and hits >= 3:
                    return True
                if total == 10 and hits >= 7:
                    return True
        except:
            pass
        
        return False
    
    def is_high_scoring_league(self, league: str) -> bool:
        """Check if league is considered high-scoring for BP8"""
        if not league:
            return False
        
        for high_league in self.HIGH_SCORING_LEAGUES:
            if high_league.lower() in league.lower():
                return True
        
        return False
    
    def parse_blueprint_text(self, text: str) -> List[Dict]:
        """Parse blueprint text into matches"""
        matches = []
        lines = text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Find blueprint header
            if line and any(bp in line for bp in ['BP1', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7', 'BP8']):
                bp_match = re.search(r'(BP[1-8])', line)
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
        """Calculate confidence score for each blueprint"""
        scores = {
            'BP1': 95, 'BP2': 90, 'BP3': 85, 
            'BP4': 75, 'BP5': 70, 'BP6': 50, 
            'BP7': 75, 'BP8': 60
        }
        return scores.get(blueprint, 50)
    
    def get_risk_level(self, blueprint: str) -> str:
        """Get risk level for each blueprint"""
        risks = {
            'BP1': 'Ultra-Low',
            'BP2': 'Low',
            'BP3': 'Low-Moderate',
            'BP4': 'Moderate',
            'BP5': 'Moderate (Value Pick)',
            'BP6': 'High (Strategic)',
            'BP7': 'Low-Moderate',
            'BP8': 'Moderate-High'
        }
        return risks.get(blueprint, 'Unknown')
    
    def get_play_description(self, blueprint: str) -> str:
        """Get play description for each blueprint"""
        plays = {
            'BP1': 'Straight Home Win',
            'BP2': 'Home Win',
            'BP3': '1X & Over 1.5 Goals',
            'BP4': 'Over 1.5 Goals',
            'BP5': '1X & Under 3.5 FT',
            'BP6': 'Full Time Draw (X) Potential',
            'BP7': 'Both Teams to Score (GG)',
            'BP8': 'HT 0.5 Goals / Over 2.5 Goals'
        }
        return plays.get(blueprint, 'Unknown')
    
    def process_matches(self, matches: List[Dict]) -> pd.DataFrame:
        """Process matches and create results DataFrame"""
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


# Quick test function
def test_8_blueprints():
    """Test the 8 blueprint classifications"""
    engine = BlueprintFilterEngine()
    
    test_cases = [
        # BP1
        {'home': 1.25, 'draw': 5.00, 'away': 11.00, 'league': 'EPL', 'expected': 'BP1'},
        # BP2
        {'home': 1.33, 'draw': 4.50, 'away': 9.50, 'league': 'La Liga', 'expected': 'BP2'},
        # BP3
        {'home': 1.35, 'draw': 4.80, 'away': 7.50, 'league': 'Serie A', 'expected': 'BP3'},
        # BP4
        {'home': 1.75, 'draw': 3.60, 'away': 4.50, 'league': 'Bundesliga', 'expected': 'BP4'},
        # BP5
        {'home': 1.95, 'draw': 3.40, 'away': 4.00, 'league': 'Ligue 1', 'expected': 'BP5'},
        # BP6
        {'home': 2.10, 'draw': 3.00, 'away': 3.80, 'league': 'EPL', 'expected': 'BP6'},
        # BP7
        {'home': 2.20, 'draw': 1.55, 'away': 3.20, 'league': 'Bundesliga', 'expected': 'BP7', 'btts_record': '3/5'},
        # BP8
        {'home': 2.40, 'draw': 3.65, 'away': 2.80, 'league': 'Eredivisie', 'expected': 'BP8'},
    ]
    
    print("\n" + "="*60)
    print("TESTING 8 BLUEPRINTS")
    print("="*60)
    
    for test in test_cases:
        result = engine.classify_blueprint(
            test['home'], 
            test['draw'], 
            test['away'],
            test.get('league', ''),
            test.get('btts_record')
        )
        
        if result and result['bp'] == test['expected']:
            print(f"✅ {test['expected']}: {result['play']} (Confidence: {result['confidence']}%)")
        else:
            print(f"❌ Expected {test['expected']}, got {result['bp'] if result else 'None'}")


if __name__ == "__main__":
    test_8_blueprints()
