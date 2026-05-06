"""
Telegram Sender - Send predictions to Telegram
"""

import requests
from typing import List, Dict
from datetime import datetime


class TelegramSender:
    """Send match predictions to Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram credentials missing")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"❌ Telegram error: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False
    
    def send_predictions(self, analyzed_matches: List[Dict], accumulators: Dict) -> bool:
        """Send full prediction report"""
        
        # Header
        message = f"""
⚽ <b>JAY SOCCER BLUEPRINTS - AI PREDICTIONS</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 AI ANALYZED PICKS</b>
"""
        
        # Top picks
        for i, match in enumerate(analyzed_matches[:10], 1):
            decision_emoji = "✅" if match['ai_decision'] == 'VALIDATED' else "🟡" if match['ai_decision'] == 'CONFIRMED' else "⚠️"
            message += f"\n{decision_emoji} <b>{match['blueprint']}</b>: {match['match']}\n"
            message += f"   🎯 {match['play']}\n"
            message += f"   📈 AI Confidence: {match['ai_confidence']}%\n"
            message += f"   🔍 Decision: {match['ai_decision']}\n"
        
        # Accumulators
        message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"<b>🎰 ACCUMULATOR PICKS</b>\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for acc_name, acc_data in accumulators.items():
            if 'error' not in acc_data and acc_data.get('matches'):
                message += f"\n<b>{acc_name.upper()}</b> (Target: {acc_data['target_odds']} odds)\n"
                message += f"Total Odds: <b>{acc_data['total_odds']}</b>\n"
                for i, match in enumerate(acc_data['matches'][:3], 1):
                    message += f"   {i}. {match['match'][:30]}...\n"
        
        # Footer
        message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"⚠️ <b>Always bet responsibly!</b>\n"
        message += f"📊 AI predictions for informational purposes only."
        
        return self.send_message(message)
