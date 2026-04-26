"""
Telegram Bot for Jay Soccer Blueprints - DEBUG VERSION
Logs all API calls and saves raw responses for troubleshooting
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict
from jay_soccer_blueprints import JaySoccerBlueprints, Match, BlueprintResult, GlobalOddsFetcher


class DebugTelegramSender:
    """Handles sending messages to Telegram with debug logging"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.debug_logs = []
    
    def log(self, message: str):
        """Add to debug log and print"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.debug_logs.append(log_entry)
        print(log_entry)
    
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
            self.log(f"Telegram response: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log(f"Error sending message: {e}")
            return False
    
    def send_debug_report(self, debug_data: Dict) -> bool:
        """Send debug report to Telegram"""
        message = f"""
🔍 <b>DEBUG REPORT - Jay Soccer Bot</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>API Status:</b>
• Status Code: {debug_data.get('status_code', 'N/A')}
• Response Size: {debug_data.get('response_size', 0)} bytes
• Error Message: {debug_data.get('error', 'None')}

<b>Raw Response Preview:</b>
<code>{debug_data.get('raw_preview', 'No data')[:500]}</code>

<b>Leagues Found:</b> {debug_data.get('leagues_found', 0)}
<b>Matches Found:</b> {debug_data.get('matches_found', 0)}

Check GitHub Actions logs for full details.
"""
        return self.send_message(message)


class DebugOddsFetcher(GlobalOddsFetcher):
    """Debug version that logs everything and saves raw responses"""
    
    def __init__(self, api_key: str, debug_dir: str = "./debug_logs"):
        super().__init__(api_key)
        self.debug_dir = debug_dir
        os.makedirs(debug_dir, exist_ok=True)
        self.debug_logs = []
    
    def log(self, message: str):
        """Log debug message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.debug_logs.append(log_entry)
        print(log_entry)
    
    def save_raw_response(self, filename: str, data: any):
        """Save raw API response to file"""
        filepath = os.path.join(self.debug_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                f.write(str(data))
        self.log(f"Saved raw response to {filepath}")
        return filepath
    
    def test_api_connection(self) -> Dict:
        """
        Test basic API connectivity and return debug info
        """
        self.log("="*60)
        self.log("TESTING API CONNECTION")
        self.log("="*60)
        
        debug_info = {
            "status_code": None,
            "response_size": 0,
            "error": None,
            "raw_preview": "",
            "leagues_found": 0,
            "matches_found": 0,
            "full_logs": []
        }
        
        # Test 1: Get all sports
        self.log("\n[TEST 1] Fetching all sports from API...")
        try:
            url = f"{self.base_url}/sports"
            params = {"apiKey": self.api_key}
            
            self.log(f"Request URL: {url}")
            self.log(f"API Key (first 10 chars): {self.api_key[:10]}...")
            
            response = requests.get(url, params=params, timeout=30)
            
            debug_info["status_code"] = response.status_code
            debug_info["response_size"] = len(response.content)
            
            self.log(f"Response Status Code: {response.status_code}")
            self.log(f"Response Size: {debug_info['response_size']} bytes")
            
            if response.status_code == 200:
                data = response.json()
                debug_info["raw_preview"] = json.dumps(data[:3] if isinstance(data, list) else data, indent=2)[:500]
                
                # Filter soccer leagues
                if isinstance(data, list):
                    soccer_leagues = [s for s in data if s.get('key', '').startswith('soccer')]
                    debug_info["leagues_found"] = len(soccer_leagues)
                    self.log(f"✓ Total sports found: {len(data)}")
                    self.log(f"✓ Soccer leagues found: {len(soccer_leagues)}")
                    
                    # Save full list
                    self.save_raw_response("all_sports.json", data)
                    self.save_raw_response("soccer_leagues.json", soccer_leagues)
                    
                    # List first 10 soccer leagues
                    self.log("\nFirst 10 soccer leagues:")
                    for league in soccer_leagues[:10]:
                        self.log(f"  - {league.get('key')}: {league.get('title')}")
                else:
                    self.log(f"⚠️ Unexpected data format: {type(data)}")
                    
            elif response.status_code == 401:
                debug_info["error"] = "Invalid API key (401 Unauthorized)"
                self.log(f"❌ {debug_info['error']}")
                self.log("   Please check your ODDS_API_KEY secret in GitHub")
                
            elif response.status_code == 429:
                debug_info["error"] = "Rate limit exceeded (429)"
                self.log(f"❌ {debug_info['error']}")
                
            else:
                debug_info["error"] = f"HTTP {response.status_code}"
                self.log(f"❌ Unexpected status code: {response.status_code}")
                self.log(f"Response body: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            debug_info["error"] = "Connection timeout"
            self.log(f"❌ {debug_info['error']}")
            
        except requests.exceptions.ConnectionError as e:
            debug_info["error"] = f"Connection error: {str(e)[:100]}"
            self.log(f"❌ {debug_info['error']}")
            
        except Exception as e:
            debug_info["error"] = str(e)
            self.log(f"❌ Unexpected error: {e}")
        
        # Save debug info
        self.save_raw_response("debug_info.json", debug_info)
        self.save_raw_response("debug_logs.txt", "\n".join(self.debug_logs))
        
        debug_info["full_logs"] = self.debug_logs
        
        return debug_info
    
    def fetch_all_matches(self, max_leagues: int = None, league_filter: List[str] = None) -> List[Match]:
        """
        Fetch ALL football matches with extensive debug logging
        """
        self.log("\n" + "="*80)
        self.log("GLOBAL SOCCER SCAN - DEBUG MODE")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("="*80)
        
        # Step 1: Get all soccer leagues
        self.log("\n[STEP 1] Getting all soccer leagues...")
        all_leagues = self.get_all_soccer_leagues()
        
        self.log(f"Raw leagues response type: {type(all_leagues)}")
        self.log(f"Number of leagues found: {len(all_leagues) if all_leagues else 0}")
        
        if not all_leagues:
            self.log("❌ No leagues found! This suggests API connection issue.")
            self.log("   Check:")
            self.log("   1. API key is valid")
            self.log("   2. Network can reach api.the-odds-api.com")
            self.log("   3. Free tier hasn't been exceeded")
            return []
        
        # Save league list for debugging
        self.save_raw_response("all_leagues_list.json", all_leagues)
        
        # Log first 10 leagues
        self.log("\nFirst 10 soccer leagues detected:")
        for i, league in enumerate(all_leagues[:10], 1):
            league_key = league.get('key', 'unknown')
            league_title = league.get('title', 'unknown')
            self.log(f"  {i}. {league_key} - {league_title}")
        
        # Apply filter if specified
        if league_filter:
            original_count = len(all_leagues)
            all_leagues = [l for l in all_leagues if l.get('key') in league_filter]
            self.log(f"\nFiltered from {original_count} to {len(all_leagues)} specified leagues")
        
        if max_leagues:
            all_leagues = all_leagues[:max_leagues]
            self.log(f"\nLimited to first {max_leagues} leagues")
        
        # Step 2: Fetch matches for each league
        self.log("\n[STEP 2] Fetching matches from each league...")
        all_matches = []
        leagues_with_matches = 0
        leagues_without_matches = 0
        
        for i, league in enumerate(all_leagues, 1):
            league_key = league.get('key', '')
            league_name = league.get('title', league_key)
            display_name = league_name.replace('Soccer - ', '')
            
            self.log(f"\n  [{i}/{len(all_leagues)}] Processing: {display_name}")
            self.log(f"    League Key: {league_key}")
            
            matches = self.fetch_matches_for_league_debug(league_key, display_name)
            
            if matches:
                all_matches.extend(matches)
                leagues_with_matches += 1
                self.log(f"    ✓ Found {len(matches)} matches")
            else:
                leagues_without_matches += 1
                self.log(f"    ✗ No matches (no games today or API issue)")
        
        # Step 3: Summary
        self.log("\n" + "="*80)
        self.log("SCAN SUMMARY")
        self.log("="*80)
        self.log(f"   Leagues scanned: {len(all_leagues)}")
        self.log(f"   Leagues with matches: {leagues_with_matches}")
        self.log(f"   Leagues without matches: {leagues_without_matches}")
        self.log(f"   Total matches found: {len(all_matches)}")
        
        if len(all_matches) == 0:
            self.log("\n⚠️ NO MATCHES FOUND - Possible reasons:")
            self.log("   1. No games scheduled for today")
            self.log("   2. API region settings don't include your location")
            self.log("   3. Free tier has limited league access")
            self.log("   4. Timezone issue (games might start later)")
        
        self.log("="*80)
        
        # Save all matches to debug file
        if all_matches:
            matches_debug = []
            for m in all_matches:
                matches_debug.append({
                    "league": m.league,
                    "league_key": m.league_key,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "home_odds": m.home_odds,
                    "draw_odds": m.draw_odds,
                    "away_odds": m.away_odds,
                    "time": m.time,
                    "date": m.date
                })
            self.save_raw_response("all_matches_found.json", matches_debug)
        
        return all_matches
    
    def fetch_matches_for_league_debug(self, league_key: str, league_name: str) -> List[Match]:
        """
        Fetch matches for a specific league with debug logging
        """
        matches = []
        
        try:
            url = f"{self.base_url}/sports/{league_key}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,uk,us,au",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            
            self.log(f"    Request URL: {url}")
            
            response = requests.get(url, params=params, timeout=30)
            
            self.log(f"    Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"    Events in response: {len(data) if isinstance(data, list) else 'not a list'}")
                
                if isinstance(data, list):
                    for event in data:
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
                            time = commence_time.split("T")[1][:5] if commence_time and len(commence_time.split("T")) > 1 else ""
                            
                            match = Match(
                                league=league_name,
                                league_key=league_key,
                                home_team=home_team,
                                away_team=away_team,
                                home_odds=home_odds,
                                draw_odds=draw_odds,
                                away_odds=away_odds,
                                time=time,
                                date=date,
                                commence_time=commence_time,
                                bookmaker=bookmakers[0].get("key", "")
                            )
                            matches.append(match)
                    
                    # Track API usage
                    remaining = response.headers.get("x-requests-remaining", "Unknown")
                    used = response.headers.get("x-requests-used", "Unknown")
                    self.log(f"    API Usage - Remaining: {remaining}, Used: {used}")
                    
                else:
                    self.log(f"    ⚠️ Response data is not a list: {type(data)}")
                    
            elif response.status_code == 401:
                self.log(f"    ❌ Invalid API key")
            elif response.status_code == 429:
                self.log(f"    ❌ Rate limit exceeded")
            else:
                self.log(f"    ❌ HTTP {response.status_code}")
                self.log(f"    Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            self.log(f"    ❌ Timeout for {league_key}")
        except Exception as e:
            self.log(f"    ❌ Error: {e}")
        
        return matches


def run_debug_scan():
    """
    Run a debug scan to troubleshoot API issues
    """
    # Get credentials from environment variables
    API_KEY = os.environ.get("ODDS_API_KEY")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    print("\n" + "🔍"*40)
    print("JAY SOCCER BLUEPRINTS - DEBUG MODE")
    print("🔍"*40)
    
    # Check environment variables
    print("\n[CHECK] Environment Variables:")
    print(f"  ODDS_API_KEY: {'✓ Set' if API_KEY else '✗ MISSING'}")
    print(f"  TELEGRAM_BOT_TOKEN: {'✓ Set' if TELEGRAM_BOT_TOKEN else '✗ MISSING'}")
    print(f"  TELEGRAM_CHAT_ID: {'✓ Set' if TELEGRAM_CHAT_ID else '✗ MISSING'}")
    
    if not API_KEY:
        print("\n❌ ERROR: ODDS_API_KEY is missing!")
        print("   Please add it to GitHub Secrets")
        return
    
    # Initialize debug fetcher
    fetcher = DebugOddsFetcher(API_KEY)
    
    # Test API connection
    debug_info = fetcher.test_api_connection()
    
    # If API test passed, fetch matches
    if debug_info["status_code"] == 200 and debug_info["leagues_found"] > 0:
        print("\n[STEP 3] Fetching matches for today...")
        matches = fetcher.fetch_all_matches(max_leagues=10)  # Limit to 10 leagues for debug
        
        print(f"\n✓ Total matches fetched: {len(matches)}")
        
        # Run blueprints on matches
        if matches:
            scanner = JaySoccerBlueprints()
            results = scanner.scan_matches(matches)
            print(f"✓ Blueprint matches found: {len(results)}")
        else:
            print("✗ No matches found to run blueprints on")
    else:
        print("\n❌ API test failed. Check debug output above.")
    
    # Send debug report to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        bot = DebugTelegramSender(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        bot.send_debug_report(debug_info)
        print("\n✓ Debug report sent to Telegram")
    
    print("\n" + "="*60)
    print("Debug complete. Check the 'debug_logs' folder for raw API responses.")
    print("="*60)


if __name__ == "__main__":
    run_debug_scan()
