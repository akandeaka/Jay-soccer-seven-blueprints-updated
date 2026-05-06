"""
Validation Runner - Runs at 1 AM to automatically validate results
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

from result_fetcher import ResultFetcher
from results_validator import ResultsValidator
from telegram_sender import TelegramSender
from config import Config


class ValidationRunner:
    """Automatically validate predictions and send reports at 1 AM"""
    
    def __init__(self):
        self.fetcher = ResultFetcher()
        self.validator = ResultsValidator()
        self.telegram = TelegramSender(
            Config.TELEGRAM_BOT_TOKEN,
            Config.TELEGRAM_CHAT_ID
        )
    
    def run_validation(self):
        """Run complete validation pipeline"""
        
        print("\n" + "="*60)
        print("🔄 SOCCER BLUEPRINT SYSTEM - AUTOMATIC VALIDATION")
        print("="*60)
        print(f"📅 Validation run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Load predictions
        print("\n📥 Loading previous predictions...")
        predictions = self.validator.load_predictions("predictions.json")
        
        if not predictions:
            print("❌ No predictions found to validate")
            return False
        
        # Step 2: Fetch actual results
        print("\n🌐 Fetching actual match results...")
        actual_results = self.fetcher.validate_predictions("predictions.json")
        
        if actual_results.empty:
            print("❌ Could not fetch actual results")
            return False
        
        # Step 3: Validate predictions
        print("\n✅ Validating predictions...")
        validated = self.validator.validate_predictions(predictions, actual_results)
        
        # Step 4: Generate report
        print("\n📊 Generating performance report...")
        report = self.validator.generate_performance_report(validated)
        
        # Step 5: Update history
        print("\n📚 Updating historical data...")
        self.validator.update_history(validated)
        
        # Step 6: Send report to Telegram
        print("\n📱 Sending report to Telegram...")
        
        # Send summary
        total = len(validated)
        correct = sum(1 for r in validated if r['is_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        summary_message = f"""
⚽ <b>DAILY PERFORMANCE REPORT</b>
📅 {datetime.now().strftime('%Y-%m-%d')}

📊 <b>Summary</b>
   Total Picks: {total}
   Correct: {correct}
   Accuracy: {accuracy:.1f}%

🎯 <b>Top Performer</b>
   Check full report for details

📈 <b>30-Day Trend</b>
   View historical data for trends
"""
        
        self.telegram.send_message(summary_message)
        
        # Send full report (split if too long)
        if len(report) > 4000:
            # Split into parts
            parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
            for i, part in enumerate(parts, 1):
                self.telegram.send_message(f"📊 <b>Performance Report (Part {i}/{len(parts)})</b>\n\n{part}")
        else:
            self.telegram.send_message(f"📊 <b>Full Performance Report</b>\n\n{report}")
        
        # Step 7: Save validated results as CSV
        df = pd.DataFrame(validated)
        df.to_csv("validated_results.csv", index=False)
        print("✅ Validated results saved to validated_results.csv")
        
        print("\n" + "="*60)
        print("✅ VALIDATION COMPLETE")
        print("="*60)
        print(f"📊 Final Accuracy: {accuracy:.1f}% ({correct}/{total})")
        
        return True


def main():
    """Main entry point for validation runner"""
    runner = ValidationRunner()
    success = runner.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
