"""
RUN VALIDATION - Validate predictions after matches are played
"""

import os
import sys
import pandas as pd
from results_validator import ResultsValidator


def main():
    print("\n" + "="*60)
    print("⚽ RUNNING MATCH VALIDATION")
    print("BP6: Full Time Draw (X)")
    print("="*60)
    
    validator = ResultsValidator()
    
    # Load predictions
    predictions = validator.load_predictions("predictions.json")
    
    if not predictions:
        print("❌ No predictions found")
        return 1
    
    # Load actual results
    actual_results = validator.load_actual_results("actual_results.csv")
    
    if actual_results.empty:
        print("\n❌ actual_results.csv not found!")
        print("\n📝 Please create actual_results.csv:")
        print("   match,home_score,away_score,result")
        print("   Bayern Munich vs Dortmund,3,0,Home Win")
        return 1
    
    # Validate
    validated = validator.validate_predictions(predictions, actual_results)
    
    # Calculate stats
    total = len([v for v in validated if v['actual_result'] != 'NO_RESULT_FOUND'])
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"   Total matches: {total}")
    print(f"   Correct: {correct}")
    print(f"   Wrong: {total - correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    # Generate report
    report = validator.generate_performance_report(validated)
    validator.update_history(validated)
    
    print(f"\n✅ Report saved to: performance_report.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
