"""
Results Validator - Check prediction accuracy and generate reports
BP6: Full Time Draw (X)
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
    
    def load_predictions(self, predictions_file: str = "predictions.json") -> List[Dict]:
        """Load previously saved predictions"""
        try:
            with open(predictions_file, 'r') as f:
                predictions = json.load(f)
            print(f"✅ Loaded {len(predictions)} predictions")
            return predictions
        except Exception as e:
            print(f"❌ Could not load predictions: {e}")
            return []
    
    def load_actual_results(self, results_file: str = "actual_results.csv") -> pd.DataFrame:
        """Load actual match results"""
        try:
            if os.path.exists(results_file):
                df = pd.read_csv(results_file)
                print(f"✅ Loaded {len(df)} actual results")
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
            actual = actual_results[actual_results['match'].str.contains(match_name[:40], case=False, na=False)]
            
            if not actual.empty:
                validation = self._validate_single_prediction(pred, actual.iloc[0].to_dict())
                validated.append(validation)
            else:
                validated.append({
                    'match': match_name,
                    'blueprint': pred.get('blueprint', ''),
                    'predicted_play': pred.get('play', ''),
                    'confidence': pred.get('confidence', 0),
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
        
        # BP1, BP2: Home Win
        if 'Home Win' in predicted_play and 'Draw' not in predicted_play:
            is_correct = home_score > away_score
            actual_result = f"{home_score}-{away_score}"
        
        # BP3, BP4, BP5, BP8: Goal based
        elif 'Over 1.5' in predicted_play:
            total = home_score + away_score
            is_correct = total > 1
            actual_result = f"{home_score}-{away_score} (Total: {total})"
        
        elif 'Under 3.5' in predicted_play:
            total = home_score + away_score
            is_correct = total < 4
            actual_result = f"{home_score}-{away_score} (Total: {total})"
        
        elif 'Over 2.5' in predicted_play:
            total = home_score + away_score
            is_correct = total > 2
            actual_result = f"{home_score}-{away_score} (Total: {total})"
        
        # BP6: Full Time Draw
        elif 'Full Time Draw' in predicted_play or 'Draw' in predicted_play:
            is_correct = home_score == away_score
            actual_result = f"{home_score}-{away_score}"
        
        # BP7: BTTS
        elif 'Both Teams to Score' in predicted_play or 'BTTS' in predicted_play:
            if 'YES' in predicted_play.upper():
                is_correct = home_score > 0 and away_score > 0
                actual_result = f"{home_score}-{away_score} (BTTS: {'Yes' if is_correct else 'No'})"
            elif 'NO' in predicted_play.upper():
                is_correct = home_score == 0 or away_score == 0
                actual_result = f"{home_score}-{away_score} (BTTS: {'No' if is_correct else 'Yes'})"
        
        return {
            'match': prediction.get('match'),
            'blueprint': prediction.get('blueprint'),
            'predicted_play': predicted_play,
            'confidence': prediction.get('confidence', 0),
            'actual_result': actual_result,
            'is_correct': is_correct,
            'home_score': home_score,
            'away_score': away_score
        }
    
    def generate_performance_report(self, validated_results: List[Dict]) -> str:
        """Generate detailed performance report"""
        
        if not validated_results:
            return "No results to validate"
        
        valid_results = [r for r in validated_results if r['actual_result'] != 'NO_RESULT_FOUND']
        total_valid = len(valid_results)
        correct = sum(1 for r in valid_results if r['is_correct'])
        accuracy = (correct / total_valid * 100) if total_valid > 0 else 0
        
        # Generate report
        report = f"""# 📊 SOCCER BLUEPRINT SYSTEM - PERFORMANCE REPORT

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Predictions:** {len(validated_results)}
**Matches Validated:** {total_valid}
**Correct Predictions:** {correct}
**Overall Accuracy:** {accuracy:.1f}%

---

## 📈 Accuracy by Blueprint

| Blueprint | Predictions | Correct | Accuracy |
|-----------|-------------|---------|----------|
"""

        # Group by blueprint
        bp_groups = {}
        for r in valid_results:
            bp = r['blueprint']
            if bp not in bp_groups:
                bp_groups[bp] = {'total': 0, 'correct': 0}
            bp_groups[bp]['total'] += 1
            if r['is_correct']:
                bp_groups[bp]['correct'] += 1
        
        for bp, stats in sorted(bp_groups.items()):
            bp_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report += f"| {bp} | {stats['total']} | {stats['correct']} | {bp_acc:.1f}% |\n"
        
        report += f"""

---

## 📝 Detailed Results

| Match | Blueprint | Prediction | Confidence | Result | Status |
|-------|-----------|------------|------------|--------|--------|
"""

        for r in valid_results[:20]:
            status = "✅" if r['is_correct'] else "❌"
            report += f"| {r['match'][:30]} | {r['blueprint']} | {r['predicted_play'][:20]} | {r['confidence']:.0f}% | {r['actual_result']} | {status} |\n"
        
        report += "\n---\n*Report generated automatically by Soccer Blueprint System*"
        
        with open("performance_report.md", "w") as f:
            f.write(report)
        
        return report
    
    def update_history(self, validated_results: List[Dict]):
        """Update historical performance data"""
        history = []
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        today = datetime.now().strftime('%Y-%m-%d')
        total = len(validated_results)
        correct = sum(1 for r in validated_results if r['is_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        history.append({
            'date': today,
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy
        })
        
        history = history[-30:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"✅ History updated")
