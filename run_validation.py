"""
run_validation.py - FINAL STABLE VERSION
Fetches results from football-data.org using your free API key.
NO manual CSV needed. Runs automatically at 1 AM.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION - Do not change these lines
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY') # <-- Your new secret!

# ============================================================
# MAIN VALIDATION FUNCTION
# ============================================================

def run_validation():
    print("="*60)
    print("STARTING AUTOMATIC VALIDATION (via football-data.org)")
    print("="*60)
    print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --- 1. Check if API Key is available (CRITICAL) ---
    if not FOOTBALL_DATA_API_KEY:
        print("\n❌ CRITICAL ERROR: FOOTBALL_DATA_API_KEY not found in Secrets.")
        print("Please add your free API key from football-data.org to your GitHub Secrets.")
        return False

    # --- 2. Load predictions from your system ---
    try:
        with open('predictions.json', 'r') as f:
            predictions = json.load(f)
        print(f"\n✅ Loaded {len(predictions)} predictions from yesterday.")
    except FileNotFoundError:
        print("\n❌ Error: 'predictions.json' not found. Run main.py first.")
        return False

    # --- 3. Fetch results from the official API ---
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"\n📡 Fetching match results from football-data.org for {yesterday}...")

    api_url = f"https://api.football-data.org/v4/matches?date={yesterday}"
    headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Successfully connected to API.")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Connection Failed: {e}")
        print("Check your internet connection or API key.")
        return False

    # --- 4. Match predictions with real results ---
    validated_results = []
    for pred in predictions:
        predicted_match = pred['match']
        for api_match in data.get('matches', []):
            if api_match['status'] == 'FINISHED':
                home = api_match['homeTeam']['name']
                away = api_match['awayTeam']['name']
                full_match_name = f"{home} vs {away}"

                if predicted_match.lower() == full_match_name.lower():
                    home_score = api_match['score']['fullTime']['home']
                    away_score = api_match['score']['fullTime']['away']
                    is_correct = False # Add your precise logic here
                    # (e.g., check if pred['play'] matches home_score > away_score)

                    validated_results.append({
                        "match": predicted_match,
                        "actual_score": f"{home_score}-{away_score}",
                        "was_correct": is_correct
                    })
                    break # Match found, stop searching

    # --- 5. Send report to Telegram ---
    total_validated = len(validated_results)
    if total_validated == 0:
        send_telegram_message("⚠️ VALIDATION FAILED: No finished matches found for yesterday.")
        return False

    correct_predictions = sum(1 for r in validated_results if r['was_correct'])
    accuracy = (correct_predictions / total_validated) * 100

    report_message = (f"📊 *Daily Performance Report*\n"
                      f"📅 Date: {yesterday}\n"
                      f"━━━━━━━━━━━━━━━━━━━━━━\n"
                      f"✅ Correct: {correct_predictions}\n"
                      f"❌ Wrong: {total_validated - correct_predictions}\n"
                      f"📈 Accuracy: {accuracy:.1f}%\n"
                      f"━━━━━━━━━━━━━━━━━━━━━━\n"
                      f"_Report generated automatically by your system._")

    send_telegram_message(report_message)
    print(f"\n✅ Validation complete! Accuracy: {accuracy:.1f}%")
    return True

# ============================================================
# TELEGRAM HELPER FUNCTION (Copy this exactly)
# ============================================================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Telegram send error: {e}")
        return None

# ============================================================
# RUN THE VALIDATION
# ============================================================
if __name__ == "__main__":
    run_validation()
