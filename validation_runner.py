# validation_runner.py
import os
import sys
import json
import pandas as pd
from datetime import datetime

from results_validator import ResultsValidator
from telegram_sender import TelegramSender
from email_sender import EmailSender
from config import Config

class ValidationRunner:
    def __init__(self):
        self.validator = ResultsValidator()
        self.telegram = TelegramSender(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)
        self.email = EmailSender(
            Config.SMTP_HOST,
            Config.SMTP_PORT,
            Config.SMTP_USER,
            Config.SMTP_PASSWORD
        )

    def load_validation_results(self):
        """Loads actual match outputs from results.txt if available."""
        if not os.path.exists("results.txt"):
            return {}
        
        results = {}
        with open("results.txt", 'r') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if ' vs ' in line and 'RESULT:' not in line:
                match_name = line
                i += 1
                while i < len(lines) and 'RESULT:' not in lines[i]:
                    i += 1
                if i < len(lines) and 'RESULT:' in lines[i]:
                    import re
                    score_match = re.search(r'(\d+)-(\d+)', lines[i])
                    if score_match:
                        results[match_name] = {
                            'home_score': int(score_match.group(1)),
                            'away_score': int(score_match.group(2))
                        }
            i += 1
        return results

    def run_validation(self):
        print("\n" + "="*60)
        print("🔄 SOCCER BLUEPRINT SYSTEM - FULL VALIDATION PIPELINE")
        print("="*60)

        # 1. Load predictions
        if not os.path.exists("predictions.json"):
            print("❌ predictions.json not found.")
            return False

        with open("predictions.json", 'r') as f:
            predictions = json.load(f)

        # 2. Load actual match results map
        actual_results_map = self.load_validation_results()
        
        print(f"📥 Loaded {len(predictions)} total predictions.")
        print(f"🌐 Loaded {len(actual_results_map)} actual results for matching.")

        # 3. Perform match evaluation across all 85 predictions
        validated = self.validator.validate_predictions(predictions, actual_results_map)

        # 4. Generate Blueprint performance & email body
        email_body, accuracy, wins, total_completed = self.validator.generate_blueprint_and_full_report(validated)

        # 5. Route Full Report via Email
        print("\n📧 Sending full 85-prediction report to Email...")
        self.email.send_report(
            recipient_email=Config.NOTIFICATION_EMAIL,
            subject=f"System & Blueprint Performance Report - {datetime.now().strftime('%Y-%m-%d')}",
            content=email_body
        )

        # 6. Route Top 30 Digest to Telegram
        print("\n📱 Sending Top 30 summary to Telegram...")
        top_30 = validated[:30]
        top_30_wins = sum(1 for r in top_30 if r['is_correct'])
        
        telegram_msg = f"⚽ <b>DAILY PERFORMANCE SUMMARY</b>\n"
        telegram_msg += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
        telegram_msg += f"📊 <b>Full System Accuracy:</b> {accuracy:.1f}% ({wins}/{total_completed})\n"
        telegram_msg += f"🎯 <b>Top 30 Digest Accuracy:</b> {(top_30_wins/30)*100:.1f}%\n\n"
        telegram_msg += "<b>Top Matches Sample:</b>\n"
        
        for r in top_30[:10]:
            icon = "✅" if r['is_correct'] else ("❌" if r['status'] == 'LOSS' else "⏳")
            telegram_msg += f"{icon} {r['match']} -> {r['play']}\n"
            
        telegram_msg += "\n📩 <i>Full 85-prediction report with Blueprint analytics has been sent to your email.</i>"
        self.telegram.send_message(telegram_msg)

        # 7. Save output CSV
        pd.DataFrame(validated).to_csv("validated_results.csv", index=False)
        print("\n✅ Validated outputs saved to validated_results.csv")
        return True
