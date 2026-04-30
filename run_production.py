#!/usr/bin/env python3
"""
PRODUCTION SYSTEM - SIMPLE BLUEPRINT FORMAT
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("📊 PRODUCTION SYSTEM")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# Read CSV
CSV_FILE = "matches_today.csv"
df = pd.read_csv(CSV_FILE)

# Filter valid odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = pd.to_numeric(df['Odds Home'])
df['Odds Draw'] = pd.to_numeric(df['Odds Draw'])
df['Odds Away'] = pd.to_numeric(df['Odds Away'])
df = df.dropna()

print(f"✅ {len(df)} matches with valid odds")

# Build simple blueprint format that parser can read
blueprint_lines = []

for idx, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # Determine BP number
    if h < 1.40:
        bp = "BP1"
        play = "Straight Home Win"
    elif h < 1.70:
        bp = "BP2"
        play = "Home Win"
    elif h < 2.00:
        bp = "BP3"
        play = "1X & Over 1.5 Goals"
    elif d < 3.20:
        bp = "BP6"
        play = "Full Time Draw"
    else:
        bp = "BP7"
        play = "GG / Over 2.5 Goals"
    
    # Simple format that parser can read
    blueprint_lines.append(f"{bp} {idx+1}. MATCH")
    blueprint_lines.append(f"{row['Home Team']} vs {row['Away Team']}")
    blueprint_lines.append(f"{row['Competition']}")
    blueprint_lines.append(f"Odds: {h} | {d} | {a}")
    blueprint_lines.append(f"Play: {play}")
    blueprint_lines.append(f"Risk: Moderate")
    blueprint_lines.append("")

blueprint_text = "\n".join(blueprint_lines)

print("\n📋 Blueprint preview:")
print("-" * 40)
print(blueprint_text[:500])
print("-" * 40)

# Apply filter engine
from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
print(f"\n✅ Parsed {len(matches)} matches")

if len(matches) == 0:
    print("❌ Still no matches parsed. Debug info:")
    print(f"Blueprint text length: {len(blueprint_text)}")
    sys.exit(1)

results_df = engine.process_matches(matches)

# Send to Telegram
telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

message = f"""
⚽ FILTER ENGINE RESULTS - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total matches: {len(df)}
✅ Filtered matches: {len(results_df)}

🏆 TOP PICKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

for idx, row in results_df.head(20).iterrows():
    message += f"""
{row['Tier']} {row['Blueprint']}: {row['Match']}
   🏆 {row['League']}
   📊 {row['Home Odds']} | {row['Draw Odds']} | {row['Away Odds']}
   🎯 {row['Play']}
   📈 Confidence: {row['Confidence']:.0f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

telegram.send_telegram_message(message)
results_df.to_csv('filtered_results.csv', index=False)
print(f"\n✅ Done! Results saved.")
