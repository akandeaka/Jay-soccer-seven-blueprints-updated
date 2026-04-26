"""
Telegram Bot for Jay Soccer Blueprints - Sportmonks Version
Sends daily predictions to your Telegram chat using REAL odds
"""

import os
import requests
from datetime import datetime
from typing import List
from jay_soccer_blueprints import JaySoccerBlueprints, BlueprintResult
from sportmonks_fetcher import SportmonksFetcher


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
❌ <b>JAY SOCCER BLUEPRINTS - NO QUALIFYING MATCHES TODAY</b>

No matches met the blueprint criteria.
Check back tomorrow for new opportunities.
"""
            return self.send_message(message)
        
        # Count by blueprint
        bp_counts = {}
        for res in results:
            key = f"BP{res.blueprint_number}"
            bp_counts[key] = bp_counts.get(key, 0) + 1
        
        # Header
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        message = f"""
⚽ <b>JAY SOCCER PREDICTION SYSTEM</b> ⚽
<b>Version 4.0 - The 7 Master Blueprints</b>
📅 {current_time}
<b>Data Source: Sportmonks (RapidAPI) - REAL ODDS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Blueprint Summary:</b>
"""
        for bp, count in sorted(bp_counts.items()):
            message += f"   • {bp}: {count} matches\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "<b>🔍 Detailed Matches:</b>\n\n"
        
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
        bp_counts = {}
        for res in results:
            key = f"BP{res.blueprint_number}"
            bp_counts[key] = bp_counts.get(key, 0) + 1
        
        bp_lines = "\n".join([f"   • {k}: {v}" for k, v in sorted(bp_counts.items())])
        
        summary = f"""
📊 <b>DAILY SCAN SUMMARY</b>
📅 {datetime.now().strftime('%Y-%m-%d')}
🔍 Matches scanned: {matches_scanned}
✅ Qualifying matches: {len(results)}

<b>Blueprints Triggered:</b>
{bp_lines}

📨 Full details above. Good luck!

💡 <i>Always bet responsibly.</i>
"""
        return self.send_message(summary)


def run_daily_scan():
    """Main function to run daily scan and send to Telegram"""
    
    # Get credentials from environment variables
    RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    print("="*60)
    print("JAY SOCCER BLUEPRINTS - DAILY SCAN")
    print(f"Started at: {datetime.now()}")
    print("="*60)
    
    # Check credentials
    if not RAPIDAPI_KEY:
        print("❌ ERROR: RAPIDAPI_KEY is missing!")
        print("   Add it to GitHub Secrets")
        return
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: Telegram credentials missing!")
        return
    
    # Step 1: Fetch matches with odds
    print("\n[1/3] Fetching today's matches with REAL odds from Sportmonks...")
    fetcher = SportmonksFetcher(RAPIDAPI_KEY)
    
    # Use the simplified endpoint (fewer API calls)
    matches = fetcher.fetch_todays_odds_simple()
    
    if not matches:
        # Fallback to the detailed method
        print("   Trying detailed fixture fetch...")
        matches = fetcher.fetch_todays_matches_with_odds()
    
    print(f"Fetched {len(matches)} matches with REAL odds")
    
    # Step 2: Run blueprints
    print("\n[2/3] Running 7 blueprints on all matches...")
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
    print(f"Telegram notifications sent")


if __name__ == "__main__":
    run_daily_scan()
