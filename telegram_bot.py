"""
Telegram Bot for Jay Soccer Blueprints
Sends daily predictions to your Telegram chat
"""

import os
import requests
from datetime import datetime
from typing import List
from jay_soccer_blueprints import JaySoccerBlueprints, Match, BlueprintResult


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
            response = requests.post(url, json=payload)
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
Check back tomorrow for new opportunities.
"""
            return self.send_message(message)
        
        # Header
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        message = f"""
⚽ <b>JAY SOCCER PREDICTION SYSTEM</b> ⚽
<b>Version 4.0 - The 7 Master Blueprints</b>
📅 {current_time}
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
💡 <i>Always bet responsibly. Past performance does not guarantee future results.</i>
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

📨 Full details sent above. Good luck!
"""
        return self.send_message(summary)


class OddsFetcher:
    """Fetches match odds from The Odds API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def fetch_matches(self, sports: List[str] = None) -> List[Match]:
        """Fetch matches from The Odds API"""
        
        if sports is None:
            sports = [
                "soccer_epl",
                "soccer_spain_la_liga", 
                "soccer_germany_bundesliga",
                "soccer_italy_serie_a",
                "soccer_france_ligue_one",
                "soccer_netherlands_eredivisie",
                "soccer_portugal_primeira_liga",
                "soccer_uefa_champs_league"
            ]
        
        matches = []
        
        for sport in sports:
            try:
                url = f"{self.base_url}/sports/{sport}/odds"
                params = {
                    "apiKey": self.api_key,
                    "regions": "eu,uk",
                    "markets": "h2h",
                    "oddsFormat": "decimal"
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Fetched {len(data)} matches from {sport}")
                    
                    for event in data:
                        # Get first bookmaker's odds
                        bookmakers = event.get("bookmakers", [])
                        if not bookmakers:
                            continue
                        
                        markets = bookmakers[0].get("markets", [])
                        if not markets:
                            continue
                        
                        outcomes = markets[0].get("outcomes", [])
                        
                        home_odds = None
                        draw_odds = None
                        away_odds = None
                        
                        home_team = event.get("home_team", "")
                        away_team = event.get("away_team", "")
                        
                        for outcome in outcomes:
                            if outcome.get("name") == home_team:
                                home_odds = outcome.get("price")
                            elif outcome.get("name") == "Draw":
                                draw_odds = outcome.get("price")
                            elif outcome.get("name") == away_team:
                                away_odds = outcome.get("price")
                        
                        if home_odds and draw_odds and away_odds:
                            commence_time = event.get("commence_time", "")
                            date = commence_time.split("T")[0] if commence_time else ""
                            time = commence_time.split("T")[1][:5] if commence_time else ""
                            
                            match = Match(
                                league=sport.replace("_", " ").title(),
                                home_team=home_team,
                                away_team=away_team,
                                home_odds=home_odds,
                                draw_odds=draw_odds,
                                away_odds=away_odds,
                                time=time,
                                date=date
                            )
                            matches.append(match)
                            
                    # Print remaining requests (for monitoring)
                    remaining = response.headers.get("x-requests-remaining", "Unknown")
                    print(f"  Requests remaining: {remaining}")
                    
            except Exception as e:
                print(f"Error fetching {sport}: {e}")
        
        return matches


def run_daily_scan():
    """Main function to run daily scan and send to Telegram"""
    
    # Get credentials from environment variables (set in GitHub Secrets)
    API_KEY = os.environ.get("ODDS_API_KEY")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not all([API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("ERROR: Missing environment variables!")
        print("Required: ODDS_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        return
    
    print("="*60)
    print("JAY SOCCER BLUEPRINTS - DAILY SCAN")
    print(f"Started at: {datetime.now()}")
    print("="*60)
    
    # Step 1: Fetch odds
    print("\n[1/4] Fetching odds from The Odds API...")
    fetcher = OddsFetcher(API_KEY)
    matches = fetcher.fetch_matches()
    print(f"Fetched {len(matches)} total matches")
    
    # Step 2: Run blueprints
    print("\n[2/4] Running blueprints...")
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(matches)
    print(f"Found {len(results)} qualifying matches across blueprints")
    
    # Step 3: Format and send to Telegram
    print("\n[3/4] Sending to Telegram...")
    bot = TelegramSender(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Send detailed results
    bot.send_formatted_results(results)
    
    # Send summary
    bot.send_daily_summary(results, len(matches))
    
    # Step 4: Save CSV for archive (optional)
    print("\n[4/4] Saving CSV archive...")
    csv_data = scanner.to_csv_format(results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f"blueprint_results_{timestamp}.csv", "w") as f:
        f.write(csv_data)
    print(f"Saved to blueprint_results_{timestamp}.csv")
    
    print("\n✅ Daily scan complete!")
    print(f"Telegram notifications sent to chat ID: {TELEGRAM_CHAT_ID}")


if __name__ == "__main__":
    run_daily_scan()
