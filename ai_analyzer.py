"""
AI Analyzer - Smart analysis of blueprint matches
NO DEMO DATA - Only analyzes real matches passed to it
"""

from typing import List, Dict


class AIAnalyzer:
    """AI-based match analyzer - ONLY processes real matches"""
    
    def __init__(self):
        self.league_avg_goals = {
            'bundesliga': 3.2,
            'eredivisie': 3.1,
            'premier league': 2.8,
            'serie a': 2.6,
            'ligue 1': 2.7,
            'la liga': 2.5
        }
    
    def analyze_match(self, match: Dict) -> Dict:
        """Analyze a single match with AI"""
        
        blueprint = match.get('blueprint', '')
        confidence = match.get('confidence', 50)
        league = match.get('league', '').lower()
        
        league_trend = self._calculate_league_trend(league)
        btts_record = match.get('btts_record', None)
        btts_boost = self._calculate_btts_boost(btts_record)
        
        adjusted_confidence = confidence * (0.8 + (league_trend * 0.2) + (btts_boost * 0.1))
        adjusted_confidence = min(95, max(60, adjusted_confidence))
        
        if adjusted_confidence >= 80:
            ai_decision = "VALIDATED"
        elif adjusted_confidence >= 70:
            ai_decision = "CONFIRMED"
        elif adjusted_confidence >= 60:
            ai_decision = "CONSIDER"
        else:
            ai_decision = "ALTERNATIVE"
        
        return {
            **match,
            'ai_confidence': round(adjusted_confidence, 1),
            'ai_decision': ai_decision,
            'ai_alternative': match.get('play', '')
        }
    
    def _calculate_league_trend(self, league: str) -> float:
        league_lower = league.lower()
        for key, avg_goals in self.league_avg_goals.items():
            if key in league_lower:
                if avg_goals >= 3.0:
                    return 0.9
                elif avg_goals >= 2.7:
                    return 0.7
                else:
                    return 0.5
        return 0.6
    
    def _calculate_btts_boost(self, btts_record: str) -> float:
        if not btts_record:
            return 0
        try:
            if '/' in btts_record:
                hits, total = map(int, btts_record.split('/'))
                rate = hits / total
                if rate >= 0.7:
                    return 0.15
                elif rate >= 0.6:
                    return 0.10
        except:
            pass
        return 0
    
    def analyze_batch(self, matches: List[Dict]) -> List[Dict]:
        """Analyze multiple matches - NO GENERATION"""
        if not matches:
            print("⚠️ No matches provided to AI analyzer")
            return []
        
        analyzed = [self.analyze_match(match) for match in matches]
        analyzed.sort(key=lambda x: x.get('ai_confidence', 0), reverse=True)
        
        print(f"✅ AI analyzed {len(analyzed)} real matches")
        return analyzed
