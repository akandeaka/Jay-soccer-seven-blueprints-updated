"""
Telegram Bot - Full Results Version
Sends complete results as a file
"""

import os
import json
import glob
import requests
from datetime import datetime


def send_full_results_as_file():
    """Send the complete CSV file to Telegram"""
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram credentials not set")
        return
    
    # Find the latest results file
    csv_files = glob.glob("./output/blueprint_results_*.csv")
    if not csv_files:
        print("⚠️ No results CSV found")
        return
    
    latest_csv = max(csv_files, key=os.path.getctime)
    json_files = glob.glob("./output/blueprint_results_*.json")
    latest_json = max(json_files, key=os.path.getctime) if json_files else None
    
    # Send summary first
    with open(latest_json, 'r') as f:
        data = json.load(f)
    
    summary = data.get("summary", {})
    bp_counts = summary.get("blueprint_counts", {})
    
    message = f"""
⚽ <b>JAY SOCCER BLUEPRINTS - FULL RESULTS</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Blueprint Summary:</b>
"""
    for bp in range(1, 8):
        count = bp_counts.get(str(bp), 0)
        if count > 0:
            emoji = "🟢" if bp in [1,2] else "🟡" if bp in [3,4,5] else "🔴"
            message += f"   {emoji} Blueprint {bp}: {count} matches\n"
    
    message += f"\n<b>📁 Total qualifying matches:</b> {summary.get('qualifying_matches', 0)}"
    message += f"\n<b>📊 Total matches scanned:</b> {summary.get('total_matches', 0)}"
    message += "\n\n📎 <b>CSV file attached with ALL matches</b>"
    
    # Send message
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    
    # Send CSV file
    with open(latest_csv, 'rb') as f:
        files = {'document': (f'blueprint_results_{datetime.now().strftime("%Y%m%d")}.csv', f, 'text/csv')}
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        requests.post(url, data={'chat_id': chat_id}, files=files)
    
    print(f"✓ Full results sent to Telegram")


def send_detailed_breakdown():
    """Send a detailed breakdown by blueprint"""
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return
    
    json_files = glob.glob("./output/blueprint_results_*.json")
    if not json_files:
        return
    
    latest_json = max(json_files, key=os.path.getctime)
    
    with open(latest_json, 'r') as f:
        data = json.load(f)
    
    blueprints_by_number = data.get("blueprints_by_number", {})
    
    for bp_num in range(1, 8):
        matches = blueprints_by_number.get(str(bp_num), [])
        if not matches:
            continue
        
        # Get blueprint name from first match
        bp_name = matches[0].get("blueprint_name", f"Blueprint {bp_num}")
        target = matches[0].get("target_market", "")
        
        message = f"""
<b>📋 BLUEPRINT {bp_num}: {bp_name}</b>
<b>🎯 Play:</b> {target}
<b>✅ {len(matches)} matches qualify:</b>
"""
        
        for i, match_data in enumerate(matches[:10], 1):  # Limit to 10 per message
            m = match_data.get("match", {})
            message += f"\n{i}. {m.get('home_team', '')} vs {m.get('away_team', '')}"
            message += f"\n   📊 Odds: {m.get('home_odds', '')} | {m.get('draw_odds', '')} | {m.get('away_odds', '')}"
        
        if len(matches) > 10:
            message += f"\n\n... and {len(matches) - 10} more matches"
        
        # Send message for this blueprint
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        
        print(f"✓ Sent Blueprint {bp_num} ({len(matches)} matches)")


if __name__ == "__main__":
    send_full_results_as_file()
    send_detailed_breakdown()
