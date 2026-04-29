"""
Telegram Integration for Filter Engine
"""

import requests
from datetime import datetime
from typing import Optional


class TelegramIntegrator:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send_telegram_message(self, message: str) -> bool:
        """Actually send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram credentials missing!")
            print("   Bot token:", "SET" if self.bot_token else "MISSING")
            print("   Chat ID:", "SET" if self.chat_id else "MISSING")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            print(f"📤 Sending to Telegram...")
            print(f"   URL: {url[:50]}...")
            print(f"   Chat ID: {self.chat_id}")
            
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Message sent to Telegram successfully!")
                return True
            else:
                print(f"❌ Telegram API error: {result}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Timeout: Telegram request took too long")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Connection error: Could not reach Telegram")
            return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False
    
    def build_telegram_message(self, results_df, original_text: str, total_qualified: int) -> str:
        """Build formatted Telegram message"""
        # Get counts
        high_conf = len(results_df[results_df['Confidence'] >= 65])
        medium_conf = len(results_df[(results_df['Confidence'] >= 50) & (results_df['Confidence'] < 65)])
        
        # Build message
        message = f"""
⚽ JAY SOCCER BLUEPRINTS - FILTERED RESULTS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 STAGE 1: BLUEPRINT SCAN
   Total qualifying: {total_qualified} matches

📊 STAGE 2: FILTER ENGINE
   🔥 High confidence (65%+): {high_conf} matches
   ⚠️ Medium confidence (50-64%): {medium_conf} matches

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP {min(20, len(results_df))} HIGHEST CONFIDENCE PICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add top matches
        for idx, row in results_df.head(20).iterrows():
            # Choose emoji based on confidence
            if row['Confidence'] >= 80:
                emoji = "🔥"
            elif row['Confidence'] >= 65:
                emoji = "✅"
            else:
                emoji = "⚠️"
            
            # Get blueprint name
            bp_names = {
                'BP1': 'ELITE HOME BANKER',
                'BP2': 'PRIMARY FAVORITE',
                'BP3': 'MODERATE FAVORITE SAFETY',
                'BP4': 'GOAL ENGINE',
                'BP5': 'DEFENSIVE TRAP',
                'BP6': 'STRONG DRAW',
                'BP7': 'HIGH-SCORING SIGNALS'
            }
            bp_name = bp_names.get(row['Blueprint'], row['Blueprint'])
            
            message += f"""
{emoji} {row['Blueprint']}: {bp_name}
   🏟️ {row['Match']}
   🏆 {row['League']}
   📊 {row['Home Odds']} | {row['Draw Odds']} | {row['Away Odds']}
   🎯 {row['Play']}
   📈 Confidence: {row['Confidence']:.0f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        message += f"""
📊 SUMMARY:
   🔥 Recommended bets: {high_conf} matches
   ⚠️ Small stake: {medium_conf} matches

⚠️ Always bet responsibly!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return message
    
    def process_and_send(self, results_df, original_text: str, total_qualified: int, send: bool = True) -> bool:
        """Process results and optionally send to Telegram"""
        message = self.build_telegram_message(results_df, original_text, total_qualified)
        
        if send:
            print("\n📤 Sending to Telegram...")
            return self.send_telegram_message(message)
        else:
            print("\n📱 TELEGRAM MESSAGE PREVIEW (NOT SENT):")
            print("="*50)
            print(message[:1000])
            if len(message) > 1000:
                print(f"\n... (message continues, total {len(message)} characters)")
            print("="*50)
            print("\n⚠️ To actually send, set send=True")
            return True
