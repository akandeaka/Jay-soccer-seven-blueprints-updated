"""
AI Analyzer - Validates blueprint picks and suggests alternatives
"""

from typing import List, Dict


class AIAnalyzer:
    """AI-based match analyzer that validates blueprint picks"""
    
    def __init__(self):
        # League goal averages for trend analysis
        self.league_avg_goals = {
            'bundesliga': 3.2,
            'eredivisie': 3.1,
            'premier league': 2.8,
            'epl': 2.8,
            'serie a': 2.6,
            'ligue 1': 2.7,
            'la liga': 2.5
        }
    
    def analyze_match(self, match: Dict) -> Dict:
        """
        Analyze a single match with AI
        Validates or suggests alternative picks
        """
        blueprint = match.get('blueprint', '')
        base_confidence = match.get('confidence', 50)
        league = match.get('league', '')
        home_team = match.get('match', '').split(' vs ')[0] if ' vs ' in match.get('match', '') else ''
        away_team = match.get('match', '').split(' vs ')[1] if ' vs ' in match.get('match', '') else ''
        
        # Calculate league trend factor
        league_factor = self._calculate_league_factor(league)
        
        # Calculate team form factor (if available)
        team_factor = self._calculate_team_factor(home_team, away_team, blueprint)
        
        # Calculate final AI confidence
        ai_confidence = base_confidence * (0.7 + league_factor * 0.2 + team_factor * 0.1)
        ai_confidence = min(95, max(40, ai_confidence))
        
        # Determine AI decision
        if ai_confidence >= 80:
            ai_decision = "VALIDATED"
        elif ai_confidence >= 70:
            ai_decision = "CONFIRMED"
        elif ai_confidence >= 60:
            ai_decision = "CONSIDER"
        else:
            ai_decision = "ALTERNATIVE"
            match = self._suggest_alternative(match)
        
        return {
            **match,
            'ai_confidence': round(ai_confidence, 1),
            'ai_decision': ai_decision,
            'league_factor': round(league_factor, 2),
            'team_factor': round(team_factor, 2)
        }
    
    def _calculate_league_factor(self, league: str) -> float:
        """Calculate factor based on league characteristics"""
        league_lower = league.lower()
        
        for key, avg_goals in self.league_avg_goals.items():
            if key in league_lower:
                if avg_goals >= 3.0:
                    return 0.9
                elif avg_goals >= 2.7:
                    return 0.7
                else:
                    return 0.5
        
        return 0.6  # Default neutral factor
    
    def _calculate_team_factor(self, home_team: str, away_team: str, blueprint: str) -> float:
        """Calculate factor based on team characteristics"""
        factor = 0.5  # Default neutral
        
        # High-scoring teams get boost for goal-related blueprints
        high_scoring = ['bayern', 'dortmund', 'man city', 'liverpool', 'barcelona', 'real madrid', 'psg']
        defensive_teams = ['burnley', 'getafe', 'cadiz']
        
        if blueprint in ['BP4', 'BP7', 'BP8']:  # Goal-related blueprints
            if any(team.lower() in ht.lower() for ht in high_scoring for team in [home_team, away_team]):
                factor = 0.8
            elif any(team.lower() in dt.lower() for dt in defensive_teams for team in [home_team, away_team]):
                factor = 0.3
        
        return factor
    
    def _suggest_alternative(self, match: Dict) -> Dict:
        """Suggest alternative bet when original pick has low confidence"""
        blueprint = match.get('blueprint', '')
        
        alternatives = {
            'BP1': 'Double Chance Home/Draw',
            'BP2': 'Home Win or Draw',
            'BP3': 'Over 1.5 Goals',
            'BP4': 'Under 1.5 Goals',
            'BP5': 'Over 2.5 Goals',
            'BP6': 'Draw No Bet',
            'BP7': 'Over 2.5 Goals',
            'BP8': 'Under 2.5 Goals'
        }
        
        match['suggested_alternative'] = alternatives.get(blueprint, 'Value Bet')
        return match
    
    def analyze_batch(self, matches: List[Dict]) -> List[Dict]:
        """Analyze multiple matches"""
        if not matches:
            return []
        
        analyzed = [self.analyze_match(match) for match in matches]
        analyzed.sort(key=lambda x: x.get('ai_confidence', 0), reverse=True)
        
        print(f"✅ AI analyzed {len(analyzed)} matches")
        return analyzed
