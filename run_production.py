#!/usr/bin/env python3
"""
PRODUCTION SYSTEM - CORRECT BLUEPRINT FORMAT FOR FILTER ENGINE
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

# ============================================================
# READ CSV FILE
# ============================================================

CSV_FILE = "matches_today.csv"

if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: {CSV_FILE} not found!")
    sys.exit(1)

df = pd.read_csv(CSV_FILE)
print(f"📥 Read {len(df)} total rows")

# Filter valid odds
odds_home_col = 'Odds Home'
odds_draw_col = 'Odds Draw'
odds_away_col = 'Odds Away'

df = df[df[odds_home_col] != '-']
df = df[df[odds_draw_col] != '-']
df = df[df[odds_away_col] != '-']

df[odds_home_col] = pd.to_numeric(df[odds_home_col], errors='coerce')
df[odds_draw_col] = pd.to_numeric(df[odds_draw_col], errors='coerce')
df[odds_away_col] = pd.to_numeric(df[odds_away_col], errors='coerce')
df = df.dropna()

print(f"✅ {len(df)} matches with valid odds")

if len(df) == 0:
    print("❌ No valid matches")
    sys.exit(1)

# ============================================================
# BUILD BLUEPRINT TEXT IN THE EXACT FORMAT FILTER ENGINE EXPECTS
# ============================================================

print("\n🔄 Building blueprint text...")

blueprint_lines = []

for idx, row in df.iterrows():
    h = float(row['Odds Home'])
    d = float(row['Odds Draw'])
    a = float(row['Odds Away'])
    
    # Determine blueprint type
    if h < 1.40:
        bp_num = "1"
        bp_name = "THE ELITE HOME BANKER"
        play = "Straight Home Win"
        risk = "Ultra-Low"
    elif h < 1.70:
        bp_num = "2"
        bp_name = "THE PRIMARY FAVORITE"
        play = "Home Win"
        risk = "Low"
    elif h < 2.00:
        bp_num = "3"
        bp_name = "THE MODERATE FAVORITE SAFETY"
        play = "1X & Over 1.5 Goals"
        risk = "Low-Moderate"
    elif d < 3.20:
        bp_num = "6"
        bp_name = "THE STRONG DRAW"
        play = "Full Time Draw"
        risk = "High (Strategic)"
    else:
        bp_num = "7"
        bp_name = "THE HIGH-SCORING SIGNALS"
        play = "GG / Over 2.5 Goals"
        risk = "Moderate-High"
    
    # EXACT FORMAT THAT FILTER ENGINE EXPECTS
    blueprint_lines.append(f"🟡 {idx+1}. BP{bp_num}: {bp_name}")
    blueprint_lines.append(f"   🏟️ {row['Home Team']} vs {row['Away Team']}")
    blueprint_lines.append(f"   🏆 {row['Competition']}")
    blueprint_lines.append(f"   📊 Odds: {h} | {d} | {a}")
    blueprint_lines.append(f"   🎯 Play: {play}")
    blueprint_lines.append(f"   ⚠️ Risk: {risk}")
    blueprint_lines.append("")  # Empty line between matches

blueprint_text = "\n".join(blueprint_lines)

# Add summary at the top
summary = f"""📊 Summary:
   🟢 Blueprint 1: 0 matches
   🟢 Blueprint 2: 0 matches
   🟡 Blueprint 3: 0 matches
   🟡 Blueprint 4: 0 matches
   🟡 Blueprint 5: 0 matches
   🔴 Blueprint 6: 0 matches
   🔴 Blueprint 7: 0 matches

🔍 Total qualifying matches: {len(df)}
📊 Total scanned: {len(df)}
"""

blueprint_text = summary + "\n" + blueprint_text

print(f"✅ Built blueprint for {len(df)} matches")

# Show preview
print("\n📋 Blueprint preview (first 15 lines):")
print("-" * 40)
lines = blueprint_text.split('\n')
for i in range(min(15, len(lines))):
    print(lines[i])
print("-" * 40)

# ============================================================
# APPLY FILTER ENGINE
# ============================================================

print("\n🔄 Applying filter engine...")

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
print(f"✅ Parsed {len(matches)} matches")

if len(matches) == 0:
    print("\n❌ No matches parsed! Check the blueprint format.")
    print("\nFull blueprint text preview:")
    print(blueprint_text[:1000])
    sys.exit(1)

results_df = engine.process_matches(matches)

# ============================================================
# SEND TO TELEGRAM
# ============================================================

print("\n📤 Sending to Telegram...")

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

# Build message manually to avoid any formatting issues
high_conf = len(results_df[results_df['Confidence'] >= 65])
message = f"""
⚽ FILTER ENGINE RESULTS - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total matches scanned: {len(df)}
✅ High confidence matches (65%+): {high_conf}

🏆 TOP 20 PICKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

for idx, row in results_df.head(20).iterrows():
    message += f"""
{row['Tier']} {row['Blueprint']}: {row['Match']}
   🏆 {row['League']}
   📊 Odds: {row['Home Odds']} | {row['Draw Odds']} | {row['Away Odds']}
   🎯 Play: {row['Play']}
   📈 Confidence: {row['Confidence']:.0f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

success = telegram.send_telegram_message(message)

if success:
    print("✅ Results sent to Telegram!")
else:
    print("❌ Failed to send")

# Save results
results_df.to_csv('filtered_results.csv', index=False)
print(f"\n📁 Saved filtered_results.csv")
print(f"✅ Done! Processed {len(df)} matches -> {len(results_df)} filtered")
