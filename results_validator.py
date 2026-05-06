"""
Results Validator - Check prediction accuracy and generate reports
"""

import pandas as pd
from typing import List, Dict
from datetime import datetime
import json


class ResultsValidator:
    """Validate predictions against actual results"""
    
    def __init__(self):
        self.history_file = "prediction_history.json"
        self.results = []
    
    def load_actual_results(self, results_file: str = "actual_results.csv") -> pd.DataFrame:
        """
        Load actual match results
        Expected columns: match, home_score, away_score, result
        """
        try:
            df = pd.read_csv(results_file)
            print(f"✅ Loaded {len(df)} actual results")
            return df
        except Exception as e:
            print(f"⚠️ No actual results found: {e}")
            return pd.DataFrame()
    
    def validate_prediction(self, prediction: Dict, actual: Dict) -> Dict:
        """Validate a single prediction against actual result"""
        
        predicted_play = prediction.get('play', '')
        home_score = actual.get('home_score', 0)
        away_score = actual.get('away_score', 0)
        
        is_correct = False
        actual_result = ""
        
        # Determine if prediction was correct
        if 'Home Win' in predicted_play:
            is_correct = home_score > away_score
            actual_result = f"{home_score}-{away_score} (Home Win)"
        elif 'Draw' in predicted_play:
            is_correct = home_score == away_score
            actual_result = f"{home_score}-{away_score} (Draw)"
        elif 'BTTS' in predicted_play:
            is_correct = home_score > 0 and away_score > 0
            actual_result = f"{home_score}-{away_score} (BTTS: {'Yes' if is_correct else 'No'})"
        elif 'Over 1.5' in predicted_play:
            total = home_score + away_score
            is_correct = total > 1
            actual_result = f"{home_score}-{away_score} (Total: {total})"
        elif 'Over 2.5' in predicted_play:
            total = home_score + away_score
            is_correct = total > 2
            actual_result = f"{home_score}-{away_score} (Total: {total})"
        elif 'Under 3.5' in predicted_play:
            total = home_score + away_score
            is_correct = total < 4
            actual_result = f"{home_score}-{away_score} (Total: {total})"
        
        return {
            'match': prediction.get('match'),
            'blueprint': prediction.get('blueprint'),
            'predicted_play': predicted_play,
            'ai_confidence': prediction.get('ai_confidence', 0),
            'actual_result': actual_result,
            'is_correct': is_correct
        }
    
    def validate_batch(self, predictions: List[Dict], actual_results: pd.DataFrame) -> List[Dict]:
        """Validate all predictions"""
        validated = []
        
        for pred in predictions:
            # Find matching actual result
            match_name = pred.get('match', '')
            actual = actual_results[actual_results['match'].str.contains(match_name[:30])]
            
            if not actual.empty:
                validation = self.validate_prediction(pred, actual.iloc[0].to_dict())
                validated.append(validation)
        
        return validated
    
    def generate_report(self, validated_results: List[Dict]) -> str:
        """Generate performance report"""
        
        if not validated_results:
            return "No results to validate"
        
        total = len(validated_results)
        correct = sum(1 for r in validated_results if r['is_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Breakdown by confidence
        high_conf = [r for r in validated_results if r['ai_confidence'] >= 75]
        high_acc = sum(1 for r in high_conf if r['is_correct']) / len(high_conf) * 100 if high_conf else 0
        
        medium_conf = [r for r in validated_results if 60 <= r['ai_confidence'] < 75]
        medium_acc = sum(1 for r in medium_conf if r['is_correct']) / len(medium_conf) * 100 if medium_conf else 0
        
        # Breakdown by blueprint
        bp_performance = {}
        for r in validated_results:
            bp = r['blueprint']
            if bp not in bp_performance:
                bp_performance[bp] = {'total': 0, 'correct': 0}
            bp_performance[bp]['total'] += 1
            if r['is_correct']:
                bp_performance[bp]['correct'] += 1
        
        # Generate report
        report = f"""
# 📊 SOCCER BLUEPRINT SYSTEM - PERFORMANCE REPORT

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Total Predictions:** {total}
**Correct Predictions:** {correct}
**Overall Accuracy:** {accuracy:.1f}%

---

## 📈 Accuracy by Confidence Level

| Confidence | Predictions | Accuracy |
|------------|-------------|----------|
| High (75%+) | {len(high_conf)} | {high_acc:.1f}% |
| Medium (60-74%) | {len(medium_conf)} | {medium_acc:.1f}% |

---

## 🎯 Accuracy by Blueprint

| Blueprint | Predictions | Correct | Accuracy |
|-----------|-------------|---------|----------|
"""
        
        for bp in sorted(bp_performance.keys()):
            stats = bp_performance[bp]
            bp_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report += f"| {bp} | {stats['total']} | {stats['correct']} | {bp_acc:.1f}% |\n"
        
        report += f"""
---

## 📝 Detailed Results

| Match | Blueprint | Prediction | AI Conf | Result | Status |
|-------|-----------|------------|---------|--------|--------|
"""
        
        for r in validated_results[:20]:  # Show top 20
            status = "✅" if r['is_correct'] else "❌"
            report += f"| {r['match'][:30]} | {r['blueprint']} | {r['predicted_play'][:20]} | {r['ai_confidence']:.0f}% | {r['actual_result'][:20]} | {status} |\n"
        
        report += f"""
---

**Summary:** The system achieved {accuracy:.1f}% accuracy on {total} predictions.
Highest performing blueprint: {max(bp_performance.keys(), key=lambda x: bp_performance[x]['correct']/bp_performance[x]['total'] if bp_performance[x]['total']>0 else 0)}

*Report generated automatically by Soccer Blueprint System*
"""
        
        # Save report
        with open("performance_report.md", "w") as f:
            f.write(report)
        
        print(f"✅ Report saved to performance_report.md")
        
        return report
