"""
Telegram Bot for Jay Soccer Blueprints
Sends results from manual data processing to Telegram
"""

import os
import json
import glob
import requests
from datetime import datetime


def send_telegram_results():
    """Send the latest blueprint results to Telegram"""
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram credentials not set")
        return
    
    # Find the latest results file
    files = glob.glob("./output/blueprint_results_*.json")
    if not files:
        print("⚠️ No results file found")
        return
    
    latest_file = max(files, key=os.path.getctime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    summary = data.get("summary", {})
    blueprints = data.get("blueprints", [])
    
    if not blueprints:
        message = f"""
⚽ <b>JAY SOCCER BLUEPRINTS</b>
📅 {datetime.now().strftime('%Y-%m-%d')}
❌ <b>NO QUALIFYING MATCHES</b>

No matches met the 7 Blueprint criteria.
"""
    else:
        bp_counts = summary.get("blueprint_counts", {})
        
        message = f"""
⚽ <b>JAY SOCCER PREDICTION SYSTEM</b> ⚽
<b>Version 4.0 - The 7 Master Blueprints</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Blueprint Summary:</b>
"""
        for bp in range(1, 8):
            count = bp_counts.get(str(bp), 0)
            if count > 0:
                emoji = "🟢" if bp in [1,2] else "🟡" if bp in [3,4,5] else "🔴"
                message += f"   {emoji} Blueprint {bp}: {count} matches\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "<b>🔍 Top Matches:</b>\n\n"
        
        for res in blueprints[:5]:
            m = res["match"]
            message += f"""
🔹 <b>BP{res['blueprint_number']}: {res['blueprint_name']}</b>
   🏟️ {m['home_team']} vs {m['away_team']}
   🏆 {m['league']}
   📊 Odds: {m['home_odds']} | {m['draw_odds']} | {m['away_odds']}
   🎯 Play: {res['target_market']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Send to Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"✓ Telegram notification sent: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send: {e}")


if __name__ == "__main__":
    send_telegram_results()
