"""
Telegram Integration for Filter Engine
"""

import re
import requests
from typing import Dict, List
from datetime import datetime
from .config import FilterConfig


class TelegramIntegrator:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or FilterConfig.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or FilterConfig.TELEGRAM_CHAT_ID
        self.top_matches = FilterConfig.TOP_MATCHES_TO_SHOW
        self.high_threshold = FilterConfig.HIGH_CONFIDENCE_THRESHOLD
        self.medium_threshold = FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD
    
    def extract_blueprint_summary(self, text: str) -> Dict[str, int]:
        """Extract BP1-BP7 counts from original blueprint message"""
        summary = {}
        patterns = {
            'BP1': r'🟢 Blueprint 1:\s*(\d+)\s*matches',
            'BP2': r'🟢 Blueprint 2:\s*(\d+)\s*matches',
            'BP3': r'🟡 Blueprint 3:\s*(\d+)\s*matches',
            'BP4': r'🟡 Blueprint 4:\s*(\d+)\s*matches',
            'BP5': r'🟡 Blueprint 5:\s*(\d+)\s*matches',
            'BP6': r'🔴 Blueprint 6:\s*(\d+)\s*matches',
            'BP7': r'🔴 Blueprint 7:\s*(\d+)\s*matches',
        }
        
        for bp, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                summary[bp] = int(match.group(1))
        
        # Extract total scanned
        total_scanned_match = re.search(r'📊 Total scanned:\s*(\d+)', text)
        total_scanned = int(total_scanned_match.group(1)) if total_scanned_match else 0
        
        return summary, total_scanned
    
    def get_blueprint_name(self, bp: str) -> str:
        """Return full blueprint name"""
        names = {
            'BP1': 'THE ELITE HOME BANKER',
            'BP2': 'THE PRIMARY FAVORITE',
            'BP3': 'THE MODERATE FAVORITE SAFETY',
            'BP4': 'THE GOAL ENGINE',
            'BP5': 'THE DEFENSIVE TRAP',
            'BP6': 'THE STRONG DRAW',
            'BP7': 'THE HIGH-SCORING SIGNALS'
        }
        return names.get(bp, bp)
    
    def get_confidence_emoji(self, confidence: float) -> str:
        """Return emoji based on confidence score"""
        if confidence >= 80:
            return "🔥"
        elif confidence >= 65:
            return "✅"
        else:
            return "⚠️"
    
    def build_telegram_message(self, results_df, original_blueprint_text: str, total_qualified: int) -> str:
        """Build complete Telegram message"""
        
        # Extract blueprint summary
        bp_summary, total_scanned = self.extract_blueprint_summary(original_blueprint_text)
        
        # Count filtered results
        high_confidence = len(results_df[results_df['Confidence'] >= self.high_threshold])
        medium_confidence = len(results_df[(results_df['Confidence'] >= self.medium_threshold) & 
                                           (results_df['Confidence'] < self.high_threshold)])
        rejected = total_qualified - (high_confidence + medium_confidence)
        
        # Build message
        message = f"""
⚽ JAY SOCCER BLUEPRINTS - STAGE 1 COMPLETE
📅 {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BLUEPRINT SCAN RESULTS:
   🟢 Blueprint 1: {bp_summary.get('BP1', 0)} matches
   🟢 Blueprint 2: {bp_summary.get('BP2', 0)} matches
   🟡 Blueprint 3: {bp_summary.get('BP3', 0)} matches
   🟡 Blueprint 4: {bp_summary.get('BP4', 0)} matches
   🟡 Blueprint 5: {bp_summary.get('BP5', 0)} matches
   🔴 Blueprint 6: {bp_summary.get('BP6', 0)} matches
   🔴 Blueprint 7: {bp_summary.get('BP7', 0)} matches

🔍 Total qualifying matches: {total_qualified}
📊 Total scanned: {total_scanned}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 STAGE 2: FILTER ENGINE PROCESSING...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 FILTER RESULTS SUMMARY:
   🔥 Passed with High Confidence ({self.high_threshold}%+): {high_confidence} matches
   ⚠️ Passed with Medium Confidence ({self.medium_threshold}-{self.high_threshold-1}%): {medium_confidence} matches
   ❌ Rejected (Below {self.medium_threshold}% or failed filters): {rejected} matches

✅ Total matches that passed filter engine: {high_confidence + medium_confidence}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 TOP {self.top_matches} HIGHEST CONFIDENCE PICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add top matches
        top_matches = results_df.head(self.top_matches)
        rank = 1
        
        for _, row in top_matches.iterrows():
            emoji = self.get_confidence_emoji(row['Confidence'])
            
            # Get the blueprint letter (BP1, BP2, etc.)
            bp_letter = row['Blueprint']
            
            message += f"""
{emoji} {rank}. {bp_letter}: {self.get_blueprint_name(bp_letter)}
   🏟️ {row['Match']}
   🏆 {row['League']}
   📊 Odds: {row['Home Odds']} | {row['Draw Odds']} | {row['Away Odds']}
   🎯 Play: {row['Play']}
   ⚠️ Risk: {row['Risk']}
   📈 Confidence: {row['Confidence']:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            rank += 1
        
        # Add final summary
        message += f"""
📊 FINAL SUMMARY:
   🔥 HIGH CONFIDENCE ({self.high_threshold}%+): {high_confidence} matches
   ⚠️ MEDIUM CONFIDENCE ({self.medium_threshold}-{self.high_threshold-1}%): {medium_confidence} matches
   ❌ FILTERED OUT: {rejected} matches

✅ Recommended bets: Top {high_confidence} ({self.high_threshold}%+ confidence)
⚠️ Small stake: Remaining {medium_confidence} matches ({self.medium_threshold}-{self.high_threshold-1}% confidence)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return message
    
    def send_to_telegram(self, message: str) -> bool:
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("⚠️ Telegram credentials not configured. Message not sent.")
            print("\n" + "="*50)
            print("MESSAGE PREVIEW:")
            print("="*50)
            print(message[:500] + "..." if len(message) > 500 else message)
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Message sent to Telegram successfully")
                return True
            else:
                print(f"❌ Failed to send: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False
    
    def process_and_send(self, results_df, original_blueprint_text: str, total_qualified: int, send: bool = True):
        """Process results and send to Telegram"""
        message = self.build_telegram_message(results_df, original_blueprint_text, total_qualified)
        
        if send:
            return self.send_to_telegram(message)
        else:
            print(message)
            return True
