"""
Blueprint Engine - 8 Blueprints with Enhanced Logic
- BP6: Draw/Draw or BTTS with scoring ability
- BP4/BP8: Over 2.5 validation using correct score odds
- Dynamic learning from past results
"""

import json
import os
from typing import Dict, List, Optional

# ============================================================
# DYNAMIC LEARNING - Load past performance
# ============================================================

def load_blueprint_performance():
    """Load historical blueprint performance to adjust weights"""
    history_file = "prediction_history.json"
    default_performance = {
        'BP1': 0.85, 'BP2': 0.82, 'BP3': 0.70,
        'BP4': 0.75, 'BP5': 0.68, 'BP6': 0.35,
        'BP7': 0.60, 'BP8': 0.65
    }
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Calculate rolling accuracy (last 30 days)
            bp_stats = {}
            for day in history[-30:]:
                for detail in day.get('details', []):
                    bp = detail.get('blueprint')
                    if bp:
                        if bp not in bp_stats:
                            bp_stats[bp] = {'total': 0, 'correct': 0}
                        bp_stats[bp]['total'] += 1
                        if detail.get('is_correct'):
                            bp_stats[bp]['correct'] += 1
            
            # Update performance based on actual results
            for bp, stats in bp_stats.items():
                if stats['total'] > 10:  # Only adjust with sufficient data
                    default_performance[bp] = stats['correct'] / stats['total']
            
            print("📊 Dynamic learning: Loaded blueprint performance from history")
        except:
            pass
    
    return default_performance

BLUEPRINT_PERFORMANCE = load_blueprint_performance()

# ============================================================
# HIGH SCORING LEAGUES
# ============================================================

HIGH_SCORING_LEAGUES = [
    'bundesliga', 'eredivisie', 'premier league', 'epl',
    'serie a', 'ligue 1', 'la liga', 'championship',
    'league one', 'league two', '2. bundesliga', '3. liga',
    'serie b', 'liga 2', 'scottish championship',
    'women\'s super league', 'frauen bundesliga', 'nwsl'
]

# ============================================================
# BP6: ENHANCED DRAW LOGIC
# ============================================================

def check_enhanced_bp6(home_odds, draw_odds, away_odds, league, 
                        home_team_goals_avg, away_team_goals_avg,
                        home_team_form, away_team_form):
    """
    BP6: Enhanced Draw Prediction
    Different patterns based on team scoring ability:
    
    Pattern A: Draw/Draw (HT Draw + FT Draw) - For high scoring teams
    Pattern B: Draw & Under 2.5 - For low scoring/defensive teams
    """
    
    # Base draw trigger
    if not (2.75 <= draw_odds <= 3.39):
        return None
    
    # Calculate team scoring averages
    home_goals = home_team_goals_avg or 1.2
    away_goals = away_team_goals_avg or 1.2
    avg_goals = (home_goals + away_goals) / 2
    
    # Calculate form (goals scored/conceded in last 5)
    home_form_goals = sum(home_team_form) if home_team_form else 0
    away_form_goals = sum(away_team_form) if away_team_form else 0
    
    # Pattern A: High scoring teams -> Draw/Draw (HT Draw + FT Draw)
    if avg_goals >= 1.3 and home_form_goals >= 5 and away_form_goals >= 5:
        return {
            'blueprint': 'BP6',
            'play': 'Draw/Draw (HT Draw + FT Draw)',
            'confidence': 65,
            'risk': 'Medium',
            'reasoning': f'Both teams have scoring ability (avg {avg_goals:.1f} goals). Draw/Draw pattern recommended.'
        }
    
    # Pattern B: Low scoring/defensive teams -> Draw & Under 2.5
    elif avg_goals <= 1.0 or home_form_goals <= 3 or away_form_goals <= 3:
        return {
            'blueprint': 'BP6',
            'play': 'Draw & Under 2.5 Goals',
            'confidence': 70,
            'risk': 'Medium',
            'reasoning': f'Teams have defensive/low-scoring trends (avg {avg_goals:.1f} goals). Draw & Under 2.5 recommended.'
        }
    
    # Pattern C: Standard Draw
    else:
        return {
            'blueprint': 'BP6',
            'play': 'Full Time Draw (X)',
            'confidence': 55,
            'risk': 'High',
            'reasoning': f'Standard draw prediction with odds {draw_odds}.'
        }

# ============================================================
# BP4/BP8: OVER 2.5 GOALS WITH CORRECT SCORE VALIDATION
# ============================================================

def validate_over_25_with_correct_score(match_data):
    """
    Validate Over 2.5 prediction using correct score odds
    If 0-0 has odds > 20, it indicates goals are expected
    """
    correct_scores = match_data.get('correct_scores', {})
    
    # Get 0-0 odds (indicates likelihood of no goals)
    odds_00 = correct_scores.get('0-0', 0)
    
    # Get other common scoring odds
    odds_11 = correct_scores.get('1-1', 0)
    odds_21 = correct_scores.get('2-1', 0)
    odds_12 = correct_scores.get('1-2', 0)
    odds_22 = correct_scores.get('2-2', 0)
    
    # If 0-0 odds > 20, bookmakers expect goals (0-0 is unlikely)
    # This strongly supports Over 2.5
    if odds_00 > 20:
        return True, f"0-0 odds {odds_00} (>20) indicates goals expected"
    
    # If 2-1, 1-2, 2-2 odds are reasonable (<15), supports Over 2.5
    if odds_21 < 15 and odds_12 < 15:
        return True, f"Likely scoring (2-1 odds {odds_21}, 1-2 odds {odds_12})"
    
    # Default - rely on standard odds
    return None, "Standard over 2.5 analysis"


def check_enhanced_bp4(home_odds, draw_odds, away_odds, league, correct_scores=None):
    """
    BP4: Goal Engine - Over 1.5 Goals
    Enhanced with correct score validation if available
    """
    
    if not (1.72 <= home_odds <= 1.80):
        return None
    
    is_high_scoring = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
    
    # Try to validate with correct scores if available
    if correct_scores:
        validated, reason = validate_over_25_with_correct_score(correct_scores)
        if validated:
            return {
                'blueprint': 'BP4',
                'play': 'Over 1.5 Goals',
                'confidence': 78,
                'risk': 'Moderate',
                'reasoning': f'Over 1.5 Goals - {reason}'
            }
    
    conf = 75 if is_high_scoring else 68
    return {
        'blueprint': 'BP4',
        'play': 'Over 1.5 Goals',
        'confidence': conf,
        'risk': 'Moderate',
        'reasoning': f'Home odds {home_odds} in {league} league.'
    }


def check_enhanced_bp8(draw_odds, league, correct_scores=None):
    """
    BP8: High-Scoring Signals - Over 2.5 Goals / HT 0.5
    Enhanced with correct score validation
    """
    
    is_high_scoring = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
    
    if not (3.60 <= draw_odds <= 3.75 and is_high_scoring):
        return None
    
    # Validate with correct scores if available
    if correct_scores:
        validated, reason = validate_over_25_with_correct_score(correct_scores)
        if validated:
            return {
                'blueprint': 'BP8',
                'play': 'Over 2.5 Goals',
                'confidence': 68,
                'risk': 'Moderate',
                'reasoning': f'Over 2.5 Goals - {reason}'
            }
    
    return {
        'blueprint': 'BP8',
        'play': 'HTML 0.5 / Over 2.5 Goals',
        'confidence': 62,
        'risk': 'Moderate-High',
        'reasoning': f'Draw odds {draw_odds} in high-scoring {league} league.'
    }

# ============================================================
# MAIN BLUEPRINT CLASSIFIER
# ============================================================

class BlueprintEngine:
    """Updated Blueprint Engine with enhanced logic"""
    
    HIGH_SCORING_LEAGUES = HIGH_SCORING_LEAGUES
    
    def __init__(self):
        self.blueprint_stats = {f'BP{i}': 0 for i in range(1, 9)}
        self.performance = BLUEPRINT_PERFORMANCE
    
    def classify_blueprint(self, match: Dict) -> Optional[Dict]:
        """Classify match with enhanced logic"""
        
        home = match.get('home_odds', 0)
        draw = match.get('draw_odds', 0)
        away = match.get('away_odds', 0)
        league = match.get('league', '')
        correct_scores = match.get('correct_scores', {})
        
        # Get team form data if available
        home_form = match.get('home_form', [])
        away_form = match.get('away_form', [])
        home_goals_avg = match.get('home_goals_avg', 1.2)
        away_goals_avg = match.get('away_goals_avg', 1.2)
        
        result = None
        
        # BP1: Elite Home Banker
        if 1.20 <= home <= 1.29 and away >= 10.0:
            result = {
                'blueprint': 'BP1',
                'play': 'Straight Home Win',
                'confidence': int(95 * self.performance.get('BP1', 0.85)),
                'risk': 'Ultra-Low'
            }
        
        # BP2: Primary Favorite
        elif 1.30 <= home <= 1.36 and away >= 9.0:
            result = {
                'blueprint': 'BP2',
                'play': 'Home Win',
                'confidence': int(90 * self.performance.get('BP2', 0.82)),
                'risk': 'Low'
            }
        
        # BP3: Moderate Favorite Safety
        elif 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
            result = {
                'blueprint': 'BP3',
                'play': '1X & Over 1.5 Goals',
                'confidence': int(85 * self.performance.get('BP3', 0.70)),
                'risk': 'Low-Moderate'
            }
        
        # BP4: Goal Engine (Enhanced)
        elif 1.72 <= home <= 1.80:
            enhanced = check_enhanced_bp4(home, draw, away, league, correct_scores)
            if enhanced:
                result = enhanced
        
        # BP5: Defensive Trap
        elif 1.90 <= home <= 2.02:
            result = {
                'blueprint': 'BP5',
                'play': '1X & Under 3.5 FT',
                'confidence': int(70 * self.performance.get('BP5', 0.68)),
                'risk': 'Moderate'
            }
        
        # BP6: Enhanced Draw Logic
        elif 2.75 <= draw <= 3.39:
            enhanced = check_enhanced_bp6(
                home, draw, away, league,
                home_goals_avg, away_goals_avg,
                home_form, away_form
            )
            if enhanced:
                result = enhanced
        
        # BP7: BTTS Value Spot
        elif 1.40 <= home <= 1.69:
            is_high_scoring = any(hl in league.lower() for hl in self.HIGH_SCORING_LEAGUES)
            if is_high_scoring:
                result = {
                    'blueprint': 'BP7',
                    'play': 'Both Teams to Score - YES',
                    'confidence': int(75 * self.performance.get('BP7', 0.60)),
                    'risk': 'Low-Moderate'
                }
            else:
                result = {
                    'blueprint': 'BP7',
                    'play': 'Both Teams to Score - NO',
                    'confidence': int(65 * self.performance.get('BP7', 0.60)),
                    'risk': 'Low-Moderate'
                }
        
        # BP8: High-Scoring Signals (Enhanced)
        elif 3.60 <= draw <= 3.75:
            enhanced = check_enhanced_bp8(draw, league, correct_scores)
            if enhanced:
                result = enhanced
        
        if result:
            result['match'] = match.get('match', 'Unknown')
            result['league'] = league
            result['home_odds'] = home
            result['draw_odds'] = draw
            result['away_odds'] = away
            self.blueprint_stats[result['blueprint']] += 1
        
        return result
