"""
Results Validator - Check prediction accuracy and generate reports
"""

import pandas as pd
from typing import List, Dict
from datetime import datetime
import json
import os


class ResultsValidator:
    """Validate predictions against actual results"""
    
    def __init__(self):
        self.history_file = "prediction_history.json"
        self.results = []
    
    def load_predictions(self, predictions_file: str = "predictions.json") -> List[Dict]:
        """Load previously saved predictions"""
        try:
            with open(predictions_file, 'r') as f:
                predictions = json.load(f)
            print(f"✅ Loaded {len(predictions)} predictions from {predictions_file}")
            return predictions
        except Exception as e:
            print(f"❌ Could not load predictions: {e}")
            return []
    
    def load_actual_results(self, results_file: str = "actual_results.csv") -> pd.DataFrame:
        """Load actual match results"""
        try:
            if os.path.exists(results_file):
                df = pd.read_csv(results_file)
                print(f"✅ Loaded {len(df)} actual results from {results_file}")
                return df
            else:
                print(f"⚠️ No actual results found at {results_file}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return pd.DataFrame()
    
    def validate_predictions(self, predictions: List[Dict], actual_results: pd.DataFrame) -> List[Dict]:
        """Validate all predictions against actual results"""
        validated = []
        
        for pred in predictions:
            match_name = pred.get('match', '')
            
            # Find matching actual result
            actual = actual_results[actual_results['match'].str.contains(match_name[:40], case=False, na=False)]
            
            if not actual.empty:
                validation = self._validate_single_prediction(pred, actual.iloc[0].to_dict())
                validated.append(validation)
            else:
                # No result found for this match
                validated.append({
                    'match': match_name,
                    'blueprint': pred.get('blueprint', ''),
                    'predicted_play': pred.get('play', ''),
                    'ai_confidence': pred.get('ai_confidence', 0),
                    'actual_result': 'NO_RESULT_FOUND',
                    'is_correct': False
                })
        
        return validated
    
    def _validate_single_prediction(self, prediction: Dict, actual: Dict) -> Dict:
        """Validate a single prediction against actual result"""
        
        predicted_play = prediction.get('play', '')
        home_score = actual.get('home_score', 0)
        away_score = actual.get('away_score', 0)
        
        is_correct = False
        actual_result = ""
        
        # Determine if prediction was correct
        if 'Home Win' in predicted_play:
            is_correct = home_score > away_score
            actual_result = f"{home_score}-{away_score}"
        elif 'Away Win' in predicted_play:
            is_correct = away_score > home_score
            actual_result = f"{home_score}-{away_score}"
        elif 'Draw' in predicted_play:
            is_correct = home_score == away_score
            actual_result = f"{home_score}-{away_score}"
        elif 'BTTS' in predicted_play or 'Both Teams to Score' in predicted_play:
            is_correct = home_score > 0 and away_score > 0
            btts_status = "Yes" if is_correct else "No"
            actual_result = f"{home_score}-{away_score} (BTTS: {btts_status})"
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
        elif '1X & Over 1.5' in predicted_play:
            total = home_score + away_score
            home_not_lost = home_score >= away_score
            is_correct = home_not_lost and total > 1
            actual_result = f"{home_score}-{away_score}"
        elif '1X & Under 3.5' in predicted_play:
            total = home_score + away_score
            home_not_lost = home_score >= away_score
            is_correct = home_not_lost and total < 4
            actual_result = f"{home_score}-{away_score}"
        
        return {
            'match': prediction.get('match'),
            'blueprint': prediction.get('blueprint'),
            'predicted_play': predicted_play,
            'ai_confidence': prediction.get('ai_confidence', 0),
            'actual_result': actual_result,
            'is_correct': is_correct,
            'home_score': home_score,
            'away_score': away_score
        }
    
    def generate_performance_report(self, validated_results: List[Dict]) -> str:
        """Generate detailed performance report"""
        
        if not validated_results:
            return "No results to validate"
        
        total = len(validated_results)
        valid_results = [r for r in validated_results if r['actual_result'] != 'NO_RESULT_FOUND']
        total_valid = len(valid_results)
        correct = sum(1 for r in valid_results if r['is_correct'])
        accuracy = (correct / total_valid * 100) if total_valid > 0 else 0
        
        # Breakdown by confidence level
        high_conf = [r for r in valid_results if r['ai_confidence'] >= 75]
        high_acc = sum(1 for r in high_conf if r['is_correct']) / len(high_conf) * 100 if high_conf else 0
        
        medium_conf = [r for r in valid_results if 60 <= r['ai_confidence'] < 75]
        medium_acc = sum(1 for r in medium_conf if r['is_correct']) / len(medium_conf) * 100 if medium_conf else 0
        
        low_conf = [r for r in valid_results if r['ai_confidence'] < 60]
        low_acc = sum(1 for r in low_conf if r['is_correct']) / len(low_conf) * 100 if low_conf else 0
        
        # Breakdown by blueprint
        bp_performance = {}
        for r in valid_results:
            bp = r['blueprint']
            if bp not in bp_performance:
                bp_performance[bp] = {'total': 0, 'correct': 0}
            bp_performance[bp]['total'] += 1
            if r['is_correct']:
                bp_performance[bp]['correct'] += 1
        
        # Best and worst performing blueprints
        best_bp = max(bp_performance.keys(), key=lambda x: bp_performance[x]['correct']/bp_performance[x]['total'] if bp_performance[x]['total']>0 else 0, default='N/A')
        worst_bp = min(bp_performance.keys(), key=lambda x: bp_performance[x]['correct']/bp_performance[x]['total'] if bp_performance[x]['total']>0 else 1, default='N/A')
        best_acc = (bp_performance[best_bp]['correct']/bp_performance[best_bp]['total']*100) if best_bp != 'N/A' else 0
        worst_acc = (bp_performance[worst_bp]['correct']/bp_performance[worst_bp]['total']*100) if worst_bp != 'N/A' else 0
        
        # Generate markdown report
        report = f"""# 📊 SOCCER BLUEPRINT SYSTEM - PERFORMANCE REPORT

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Predictions:** {total}
**Matches Validated:** {total_valid}
**Correct Predictions:** {correct}
**Overall Accuracy:** {accuracy:.1f}%

---

## 📈 Accuracy by Confidence Level

| Confidence Level | Predictions | Correct | Accuracy |
|-----------------|-------------|---------|----------|
| High (75%+) | {len(high_conf)} | {sum(1 for r in high_conf if r['is_correct'])} | {high_acc:.1f}% |
| Medium (60-74%) | {len(medium_conf)} | {sum(1 for r in medium_conf if r['is_correct'])} | {medium_acc:.1f}% |
| Low (<60%) | {len(low_conf)} | {sum(1 for r in low_conf if r['is_correct'])} | {low_acc:.1f}% |

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

## 🏆 Best & Worst Performers

| Category | Blueprint | Accuracy |
|----------|-----------|----------|
| Best Performer | {best_bp} | {best_acc:.1f}% |
| Worst Performer | {worst_bp} | {worst_acc:.1f}% |

---

## 📝 Detailed Results

| Match | Blueprint | Prediction | AI Conf | Result | Status |
|-------|-----------|------------|---------|--------|--------|
"""

        for r in valid_results[:20]:
            status = "✅" if r['is_correct'] else "❌"
            report += f"| {r['match'][:35]} | {r['blueprint']} | {r['predicted_play'][:20]} | {r['ai_confidence']:.0f}% | {r['actual_result'][:20]} | {status} |\n"
        
        # Add summary of matches not found
        not_found = [r for r in validated_results if r['actual_result'] == 'NO_RESULT_FOUND']
        if not_found:
            report += f"\n---\n## ⚠️ Matches Not Found ({len(not_found)})\n\n"
            for r in not_found[:10]:
                report += f"- {r['match']}\n"
        
        report += f"""
---

## 📊 Summary Statistics

- **Total ROI if betting 1 unit per pick:** {correct - (total_valid - correct)} units
- **Profit/Loss:** {'+' if correct > (total_valid - correct) else ''}{correct - (total_valid - correct)} units
- **Best Match:** {max(valid_results, key=lambda x: x['ai_confidence'] if x['is_correct'] else 0)['match'] if valid_results else 'N/A'}

---

*Report generated automatically by Soccer Blueprint System*
"""
        
        # Save report
        with open("performance_report.md", "w") as f:
            f.write(report)
        
        print(f"✅ Performance report saved to performance_report.md")
        
        return report
    
    def update_history(self, validated_results: List[Dict]):
        """Update historical performance data"""
        history = []
        
        # Load existing history
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        # Add today's results
        today = datetime.now().strftime('%Y-%m-%d')
        total = len(validated_results)
        correct = sum(1 for r in validated_results if r['is_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        history.append({
            'date': today,
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'details': validated_results[:50]  # Store last 50
        })
        
        # Keep only last 30 days
        history = history[-30:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"✅ History updated with today's results")
