"""
Enhanced AI Analyzer - Team Form Integrated
Validates blueprint picks with team form data and provides AI decisions
"""

from typing import List, Dict, Optional


class EnhancedAIAnalyzer:
    """AI-based match analyzer integrated with team form data"""
    
    def __init__(self, team_db=None):
        """Initialize with optional TeamDatabase connection"""
        self.team_db = team_db
        
        # League goal averages for trend analysis
        self.league_avg_goals = {
            'bundesliga': 3.2,
            'eredivisie': 3.1,
            'premier league': 2.8,
            'epl': 2.8,
            'serie a': 2.6,
            'ligue 1': 2.7,
            'la liga': 2.5,
            'championship': 2.6,
        }
        
        # Blueprint-specific validation thresholds
        self.validation_thresholds = {
            'BP1': {'home_strength': 0.75, 'required_win': True},
            'BP2': {'home_strength': 0.65, 'h2h_advantage': 0.40},
            'BP3': {'home_strength': 0.60, 'expected_goals': 1.5},
            'BP4': {'combined_scoring': 1.6},
            'BP5': {'home_strength': 0.55, 'away_concedes': 1.5},
            'BP6': {'strength_diff': 0.3},
            'BP7': {'btts_probability': 0.50},
            'BP8': {'expected_goals': 2.5},
        }
    
    def analyze_match(self, match: Dict) -> Dict:
        """
        Analyze a single match with AI
        Validates or suggests alternative picks
        """
        blueprint = match.get('blueprint', '')
        base_confidence = match.get('confidence', 50)
        league = match.get('league', '')
        match_str = match.get('match', '')
        home_team = match_str.split(' vs ')[0] if ' vs ' in match_str else ''
        away_team = match_str.split(' vs ')[1] if ' vs ' in match_str else ''
        
        # Extract context if available
        context = match.get('team_context', {})
        
        # Calculate league trend factor
        league_factor = self._calculate_league_factor(league)
        
        # Calculate team form factor
        team_factor = self._calculate_team_factor(context, blueprint)
        
        # Calculate trend bonus
        trend_bonus = self._calculate_trend_bonus(context)
        
        # Validate blueprint with team data
        is_valid = self._validate_blueprint(blueprint, context)
        validation_penalty = 0 if is_valid else -0.10
        
        # Calculate final AI confidence
        ai_confidence = base_confidence * (0.60 + league_factor * 0.15 + 
                                          team_factor * 0.15 + trend_bonus * 0.10)
        ai_confidence = min(98, max(35, ai_confidence + validation_penalty * base_confidence))
        
        # Determine AI decision
        ai_decision, decision_emoji = self._get_ai_decision(ai_confidence, is_valid)
        
        # Predict outcome
        predicted_outcome = self._predict_outcome(context)
        
        # Get accumulator score
        accumulator_score = self._calculate_accumulator_score(
            match, ai_confidence, context, is_valid
        )
        
        return {
            **match,
            'ai_confidence': round(ai_confidence, 1),
            'ai_decision': ai_decision,
            'decision_emoji': decision_emoji,
            'league_factor': round(league_factor, 2),
            'team_factor': round(team_factor, 2),
            'trend_bonus': round(trend_bonus, 2),
            'validation': is_valid,
            'predicted_outcome': predicted_outcome,
            'expected_goals': round(context.get('expected_goals', 0), 1),
            'accumulator_score': round(accumulator_score, 1),
            'home_strength': round(context.get('home_team_strength', 0), 2),
            'away_strength': round(context.get('away_team_strength', 0), 2),
        }
    
    def _calculate_league_factor(self, league: str) -> float:
        """Calculate factor based on league characteristics"""
        league_lower = league.lower()
        
        for key, avg_goals in self.league_avg_goals.items():
            if key in league_lower:
                if avg_goals >= 3.0:
                    return 0.95
                elif avg_goals >= 2.7:
                    return 0.80
                else:
                    return 0.60
        
        return 0.70  # Default neutral factor
    
    def _calculate_team_factor(self, context: Dict, blueprint: str) -> float:
        """Calculate factor based on team strength and blueprint type"""
        if not context:
            return 0.50
        
        home_strength = context.get('home_team_strength', 0.5)
        away_strength = context.get('away_team_strength', 0.5)
        
        factor = 0.50  # Default neutral
        
        # Blueprint-specific adjustments
        if blueprint in ['BP1', 'BP2', 'BP3']:  # Home win focused
            if home_strength >= 0.75:
                factor = 0.90
            elif home_strength >= 0.65:
                factor = 0.75
            elif home_strength >= 0.55:
                factor = 0.60
            else:
                factor = 0.40
        
        elif blueprint in ['BP4', 'BP7', 'BP8']:  # Goal-related
            combined_scoring = context.get('combined_goals_avg', 0)
            if combined_scoring >= 2.0:
                factor = 0.90
            elif combined_scoring >= 1.5:
                factor = 0.75
            elif combined_scoring >= 1.0:
                factor = 0.60
            else:
                factor = 0.35
        
        elif blueprint == 'BP5':  # 1X & Under
            if home_strength >= 0.55 and away_strength <= 0.65:
                factor = 0.75
            else:
                factor = 0.50
        
        elif blueprint == 'BP6':  # Draw
            strength_diff = abs(home_strength - away_strength)
            if strength_diff <= 0.2:
                factor = 0.80
            elif strength_diff <= 0.3:
                factor = 0.65
            else:
                factor = 0.40
        
        return factor
    
    def _calculate_trend_bonus(self, context: Dict) -> float:
        """Calculate bonus based on form trends"""
        if not context:
            return 0.0
        
        home_trend = context.get('home_team_trend', 'STABLE')
        away_trend = context.get('away_team_trend', 'STABLE')
        
        bonus = 0.0
        
        if home_trend == 'IMPROVING':
            bonus += 0.05
        elif home_trend == 'DECLINING':
            bonus -= 0.05
        
        if away_trend == 'DECLINING':
            bonus += 0.03
        elif away_trend == 'IMPROVING':
            bonus -= 0.02
        
        return max(-0.08, min(0.08, bonus))  # Clamp between -0.08 and +0.08
    
    def _validate_blueprint(self, blueprint: str, context: Dict) -> bool:
        """Validate blueprint with team-specific rules"""
        if not context:
            return True  # No data to validate
        
        thresholds = self.validation_thresholds.get(blueprint, {})
        
        if blueprint == 'BP1':
            home_strength = context.get('home_team_strength', 0)
            last_match_won = context.get('home_team_last_match') == 'W'
            return home_strength >= 0.75 and last_match_won
        
        elif blueprint == 'BP2':
            home_strength = context.get('home_team_strength', 0)
            h2h_advantage = context.get('h2h_home_win_pct', 0)
            return home_strength >= 0.65 and h2h_advantage >= 0.40
        
        elif blueprint == 'BP3':
            expected_goals = context.get('expected_goals', 0)
            return expected_goals >= 1.5
        
        elif blueprint == 'BP4':
            combined_scoring = context.get('combined_goals_avg', 0)
            return combined_scoring >= 1.6
        
        elif blueprint == 'BP5':
            home_strength = context.get('home_team_strength', 0)
            away_concedes = context.get('away_team_goals_conceded_avg', 2.0)
            return home_strength >= 0.55 and away_concedes <= 1.5
        
        elif blueprint == 'BP6':
            strength_diff = abs(context.get('home_team_strength', 0.5) - 
                               context.get('away_team_strength', 0.5))
            return strength_diff <= 0.3
        
        elif blueprint == 'BP7':
            home_scoring = context.get('home_team_goals_avg', 0.9)
            away_scoring = context.get('away_team_goals_avg', 0.9)
            return (home_scoring + away_scoring) / 2 >= 0.9
        
        elif blueprint == 'BP8':
            expected_goals = context.get('expected_goals', 0)
            return expected_goals >= 2.5
        
        return True
    
    def _get_ai_decision(self, confidence: float, is_valid: bool) -> tuple:
        """Get AI decision classification"""
        if not is_valid:
            return ("❌ RISKY", "❌")
        
        if confidence >= 90:
            return ("🔥 STRONG BUY", "🔥")
        elif confidence >= 80:
            return ("✅ VALIDATED", "✅")
        elif confidence >= 70:
            return ("🟢 CONFIRMED", "🟢")
        elif confidence >= 60:
            return ("🟡 CONSIDER", "🟡")
        else:
            return ("⚠️ CAUTION", "⚠️")
    
    def _predict_outcome(self, context: Dict) -> str:
        """Predict match outcome with probabilities"""
        if not context:
            return "Home: 50% | Draw: 25% | Away: 25%"
        
        home_prob = context.get('home_win_prob', 50)
        draw_prob = context.get('draw_prob', 25)
        away_prob = context.get('away_win_prob', 25)
        
        # Determine most likely outcome
        outcomes = {
            'Home': home_prob,
            'Draw': draw_prob,
            'Away': away_prob
        }
        
        likely = max(outcomes, key=outcomes.get)
        emoji = {'Home': '1️⃣', 'Draw': '🤝', 'Away': '2️⃣'}[likely]
        
        return f"{emoji} {likely} ({max(outcomes.values()):.0f}%) | D: {draw_prob:.0f}% | Other: {min(outcomes.values()):.0f}%"
    
    def _calculate_accumulator_score(self, match: Dict, ai_confidence: float, 
                                     context: Dict, is_valid: bool) -> float:
        """Calculate 0-100 score for accumulator inclusion"""
        
        # Data quality (0-40)
        league = match.get('league', '').lower()
        if any(tier1 in league for tier1 in ['premier', 'bundesliga', 'la liga', 'serie a']):
            data_quality = 40
        elif any(tier2 in league for tier2 in ['championship', 'eredivisie', 'segunda']):
            data_quality = 35
        else:
            data_quality = 25
        
        # Blueprint reliability (0-30)
        bp = match.get('blueprint', '')
        bp_weights = {
            'BP1': 30, 'BP2': 28, 'BP3': 21,
            'BP4': 22, 'BP5': 20, 'BP6': 10,
            'BP7': 18, 'BP8': 19
        }
        blueprint_score = bp_weights.get(bp, 15)
        
        # Validation factor (0-20)
        validation_score = 20 if is_valid else 5
        
        # Form consistency (0-10)
        form_consistency = 0
        if context:
            home_form = context.get('home_team_form_score', 0.5)
            away_form = context.get('away_team_form_score', 0.5)
            form_consistency = min(10, (home_form + away_form) * 10)
        
        total = data_quality + blueprint_score + validation_score + form_consistency
        
        return round(total, 1)
    
    def analyze_batch(self, matches: List[Dict]) -> List[Dict]:
        """Analyze multiple matches"""
        if not matches:
            return []
        
        analyzed = [self.analyze_match(match) for match in matches]
        analyzed.sort(key=lambda x: x.get('ai_confidence', 0), reverse=True)
        
        print(f"✅ Enhanced AI analyzed {len(analyzed)} matches")
        return analyzed
    
    def get_summary(self, analyzed_matches: List[Dict]) -> Dict:
        """Get summary statistics from analyzed matches"""
        if not analyzed_matches:
            return {}
        
        total = len(analyzed_matches)
        confidences = [m.get('ai_confidence', 0) for m in analyzed_matches]
        avg_confidence = sum(confidences) / total if total > 0 else 0
        
        # Count by decision
        decisions = {}
        for match in analyzed_matches:
            decision = match.get('ai_decision', 'Unknown')
            decisions[decision] = decisions.get(decision, 0) + 1
        
        # High confidence picks
        high_confidence = sum(1 for c in confidences if c >= 80)
        validated = sum(1 for c in confidences if c >= 75)
        
        return {
            'total_matches': total,
            'avg_confidence': round(avg_confidence, 1),
            'high_confidence': high_confidence,
            'validated': validated,
            'decisions': decisions,
            'confidence_range': {
                'min': round(min(confidences), 1),
                'max': round(max(confidences), 1),
                'std_dev': round(self._calculate_std_dev(confidences), 1)
            }
        }
    
    @staticmethod
    def _calculate_std_dev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
