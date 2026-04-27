"""
Telegram Bot - Shows ALL qualifying matches in the message (not just summary)
"""

import os
import json
import glob
import requests
from datetime import datetime


def send_full_match_list():
    """Send a Telegram message with ALL qualifying matches listed."""
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram credentials not set")
        return
    
    # Find the latest results file
    json_files = glob.glob("./output/blueprint_results_*.json")
    if not json_files:
        print("⚠️ No results JSON found")
        return
    
    latest_json = max(json_files, key=os.path.getctime)
    csv_files = glob.glob("./output/blueprint_results_*.csv")
    latest_csv = max(csv_files, key=os.path.getctime) if csv_files else None
    
    with open(latest_json, 'r') as f:
        data = json.load(f)
    
    summary = data.get("summary", {})
    blueprints = data.get("blueprints", [])
    
    if not blueprints:
        # No qualifying matches
        message = f"""
⚽ <b>JAY SOCCER BLUEPRINTS</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ <b>NO MATCHES QUALIFIED TODAY</b>

<b>Total scanned:</b> {summary.get('total_matches', 0)}
<b>Qualifying:</b> 0

Check tomorrow's fixtures.
"""
        send_telegram_message(chat_id, bot_token, message)
        return
    
    # Count matches per blueprint for the header
    bp_counts = {}
    for bp in blueprints:
        num = bp['blueprint_number']
        bp_counts[num] = bp_counts.get(num, 0) + 1
    
    # Build header
    header = f"""
⚽ <b>JAY SOCCER BLUEPRINTS - FULL PREDICTIONS</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Summary:</b>
"""
    for bp in sorted(bp_counts.keys()):
        emoji = "🟢" if bp in [1,2] else "🟡" if bp in [3,4,5] else "🔴"
        header += f"   {emoji} Blueprint {bp}: {bp_counts[bp]} matches\n"
    
    header += f"\n<b>🔍 Total qualifying matches:</b> {len(blueprints)}"
    header += f"\n<b>📊 Total scanned:</b> {summary.get('total_matches', 0)}"
    header += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Build the list of matches
    match_lines = []
    for i, res in enumerate(blueprints, 1):
        m = res['match']
        bp_num = res['blueprint_number']
        bp_name = res['blueprint_name']
        target = res['target_market']
        risk = res['risk_level']
        
        # Emoji for risk level
        risk_emoji = "🟢" if "Low" in risk else "🟡" if "Moderate" in risk else "🔴"
        
        line = f"{risk_emoji} <b>{i}. BP{bp_num}: {bp_name}</b>\n"
        line += f"   🏟️ {m['home_team']} vs {m['away_team']}\n"
        line += f"   🏆 {m['league']}\n"
        line += f"   📊 Odds: {m['home_odds']} | {m['draw_odds']} | {m['away_odds']}\n"
        line += f"   🎯 <b>Play:</b> {target}\n"
        line += f"   ⚠️ Risk: {risk}\n"
        line += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        match_lines.append(line)
    
    # Combine header and matches
    full_message = header + "\n".join(match_lines)
    
    # Telegram has a 4096 character limit. Split if needed.
    if len(full_message) <= 4096:
        send_telegram_message(chat_id, bot_token, full_message)
    else:
        # Send header first
        send_telegram_message(chat_id, bot_token, header)
        # Then send matches in chunks
        chunk = ""
        for line in match_lines:
            if len(chunk) + len(line) + 100 > 4096:
                send_telegram_message(chat_id, bot_token, chunk)
                chunk = line
            else:
                chunk += line
        if chunk:
            send_telegram_message(chat_id, bot_token, chunk)
    
    # Also send the CSV file as attachment
    if latest_csv:
        send_csv_file(chat_id, bot_token, latest_csv)


def send_telegram_message(chat_id, bot_token, text):
    """Send a plain text message to Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=30)
        if response.status_code != 200:
            print(f"Failed to send message: {response.text}")
    except Exception as e:
        print(f"Error sending message: {e}")


def send_csv_file(chat_id, bot_token, file_path):
    """Send a CSV file as a document."""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': (os.path.basename(file_path), f, 'text/csv')}
        try:
            response = requests.post(url, data={'chat_id': chat_id}, files=files, timeout=30)
            if response.status_code != 200:
                print(f"Failed to send CSV: {response.text}")
        except Exception as e:
            print(f"Error sending CSV: {e}")


if __name__ == "__main__":
    send_full_match_list()
