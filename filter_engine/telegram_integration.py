"""
Telegram Integration for Filter Engine
"""

from datetime import datetime


class TelegramIntegrator:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def build_telegram_message(self, results_df, original_text, total_qualified):
        """Build Telegram message"""
        message = f"""
⚽ FILTER ENGINE RESULTS
📅 {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total scanned: {total_qualified}
✅ High confidence: {len(results_df[results_df['Confidence'] >= 65])}
⚠️ Medium confidence: {len(results_df[(results_df['Confidence'] >= 50) & (results_df['Confidence'] < 65)])}

🏆 TOP PICKS:
"""
        for idx, row in results_df.head(5).iterrows():
            message += f"\n{row['Tier']} {row['Blueprint']}: {row['Match'][:40]}\n"
            message += f"   Confidence: {row['Confidence']}%\n"
        
        return message
    
    def send_to_telegram(self, message):
        """Send to Telegram (placeholder for testing)"""
        print("\n" + "="*50)
        print("TELEGRAM MESSAGE (TEST MODE - NOT SENT)")
        print("="*50)
        print(message[:500])
        print("="*50)
        return True
    
    def process_and_send(self, results_df, original_text, total_qualified, send=True):
        """Process and send results"""
        message = self.build_telegram_message(results_df, original_text, total_qualified)
        if send:
            return self.send_to_telegram(message)
        else:
            print(message)
            return True