"""
RUN VALIDATION - Call the validator after matches are played
Run this at 1 AM next day
"""

import os
import sys
from results_validator import ResultsValidator

def main():
    print("\n" + "="*60)
    print("⚽ RUNNING MATCH VALIDATION")
    print("="*60)
    
    # Create validator instance
    validator = ResultsValidator()
    
    # Load predictions from yesterday
    predictions = validator.load_predictions("predictions.json")
    
    if not predictions:
        print("❌ No predictions found to validate")
        return 1
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Load actual results (YOU MUST CREATE THIS FILE)
    actual_results = validator.load_actual_results("actual_results.csv")
    
    if actual_results.empty:
        print("\n❌ actual_results.csv not found!")
        print("\n📝 Please create actual_results.csv with this format:")
        print("   match,home_score,away_score,result")
        print("   Manchester United vs Liverpool,2,1,Home Win")
        print("   Real Madrid vs Barcelona,1,1,Draw")
        return 1
    
    # Validate predictions
    validated = validator.validate_predictions(predictions, actual_results)
    
    # Calculate accuracy
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
    
    # Update history
    validator.update_history(validated)
    
    print(f"\n✅ Validation complete!")
    print(f"   Report saved to: performance_report.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
