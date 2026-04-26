"""
Telegram Bot for Jay Soccer Blueprints - Football-Data.org Version
Sends daily predictions to your Telegram chat
"""

import os
import requests
from datetime import datetime
from typing import List
from jay_soccer_blueprints import JaySoccerBlueprints, Match, BlueprintResult
from football_data_fetcher import FootballDataFetcher


class TelegramSender:
    """Handles sending messages to Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a plain text message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def send_formatted_results(self, results: List[BlueprintResult]) -> bool:
        """Format and send blueprint results as a nice Telegram message"""
        
        if not results:
            message = """
❌ <b>JAY SOCCER BLUEPRINTS - NO MATCHES TODAY</b>

No matches qualified for any blueprint.
Possible reasons:
• No games scheduled today
• Check tomorrow's matches
• API rate limit may be exceeded

Check back tomorrow for new opportunities.
"""
            return self.send_message(message)
        
        # Header
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        message = f"""
⚽ <b>JAY SOCCER PREDICTION SYSTEM</b> ⚽
<b>Version 4.0 - The 7 Master Blueprints</b>
📅 {current_time}
<b>Data Source: Football-Data.org</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Group results by blueprint
        for i, res in enumerate(results, 1):
            # Emoji based on risk level
            risk_emoji = {
                "Ultra-Low": "🟢",
                "Low": "🟢",
                "Low-Moderate": "🟡",
                "Moderate": "🟡",
                "Moderate (Value Pick)": "🟡",
                "Moderate-High": "🟠",
                "High (Strategic)": "🔴"
            }.get(res.risk_level, "⚪")
            
            # Market emoji
            market_emoji = {
                "Straight Home Win": "🏠",
                "Home Winning (Straight Win)": "🏠",
                "1X & Over 1.5 Goals": "🎯",
                "Over 1.5 Goals": "⚽⚽",
                "1X & Under 3.5 FT": "🛡️",
                "Full Time Draw (X) Potential": "🤝",
                "GG / Over 2.5 Goals": "🎯⚽",
                "HT 0.5 Goals / Over 2.5 Goals": "⏱️⚽"
            }.get(res.target_market, "📊")
            
            message += f"""
{risk_emoji} <b>{i}. BLUEPRINT {res.blueprint_number}</b>
   📋 {res.blueprint_name}
   🏟️ {res.match.home_team} vs {res.match.away_team}
   🏆 {res.match.league}
   📊 Odds: {res.match.home_odds} | {res.match.draw_odds} | {res.match.away_odds}
   {market_emoji} <b>Play:</b> {res.target_market}
   ⚠️ <b>Risk:</b> {res.risk_level}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Footer
        message += """
💡 <i>Important Notes:</i>
• Football-Data.org free tier provides match data only (no live odds)
• Odds shown are implied estimates
• Upgrade to paid tier for real-time odds

<i>Always bet responsibly.</i>
"""
        
        return self.send_message(message)
    
    def send_daily_summary(self, results: List[BlueprintResult], matches_scanned: int) -> bool:
        """Send a concise daily summary"""
        
        if not results:
            summary = f"""
📊 <b>DAILY SCAN SUMMARY</b>
📅 {datetime.now().strftime('%Y-%m-%d')}
🔍 Matches scanned: {matches_scanned}
❌ Qualifying matches: 0

No blueprints triggered today.
"""
            return self.send_message(summary)
        
        # Count by blueprint
        blueprint_counts = {}
        for res in results:
            key = f"BP{res.blueprint_number}"
            blueprint_counts[key] = blueprint_counts.get(key, 0) + 1
        
        blueprint_lines = "\n".join([f"   • {k}: {v}" for k, v in blueprint_counts.items()])
        
        summary = f"""
📊 <b>DAILY SCAN SUMMARY</b>
📅 {datetime.now().strftime('%Y-%m-%d')}
🔍 Matches scanned: {matches_scanned}
✅ Qualifying matches: {len(results)}

<b>Blueprints Triggered:</b>
{blueprint_lines}

📨 Full details above. Good luck!
"""
        return self.send_message(summary)


def run_daily_scan():
    """Main function to run daily scan and send to Telegram"""
    
    # Get credentials from environment variables
    FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    print("="*60)
    print("JAY SOCCER BLUEPRINTS - DAILY SCAN")
    print(f"Started at: {datetime.now()}")
    print("="*60)
    
    # Check credentials
    if not FOOTBALL_DATA_KEY:
        print("❌ ERROR: FOOTBALL_DATA_KEY is missing!")
        print("   Add it to GitHub Secrets")
        return
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: Telegram credentials missing!")
        return
    
    # Step 1: Fetch matches
    print("\n[1/3] Fetching today's matches from Football-Data.org...")
    fetcher = FootballDataFetcher(FOOTBALL_DATA_KEY)
    matches = fetcher.fetch_all_todays_matches()
    print(f"Fetched {len(matches)} total matches")
    
    # Step 2: Run blueprints
    print("\n[2/3] Running blueprints...")
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(matches)
    print(f"Found {len(results)} qualifying matches across blueprints")
    
    # Step 3: Send to Telegram
    print("\n[3/3] Sending to Telegram...")
    bot = TelegramSender(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Send detailed results
    bot.send_formatted_results(results)
    
    # Send summary
    bot.send_daily_summary(results, len(matches))
    
    print("\n✅ Daily scan complete!")
    print(f"Telegram notifications sent to chat ID: {TELEGRAM_CHAT_ID}")


if __name__ == "__main__":
    run_daily_scan()
