#!/usr/bin/env python3
"""
PRODUCTION SYSTEM - READS YOUR EXACT CSV FORMAT
Columns: Odds Home, Odds Draw, Odds Away (with spaces)
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

# Read CSV
df = pd.read_csv(CSV_FILE)
print(f"📥 Read {len(df)} total rows")

# Show column names for debugging
print(f"📋 Columns found: {list(df.columns)}")

# ============================================================
# FILTER MATCHES WITH VALID ODDS
# ============================================================

# Your columns: 'Odds Home', 'Odds Draw', 'Odds Away'
odds_home_col = 'Odds Home'
odds_draw_col = 'Odds Draw'
odds_away_col = 'Odds Away'

# Remove rows where odds are '-'
df = df[df[odds_home_col] != '-']
df = df[df[odds_draw_col] != '-']
df = df[df[odds_away_col] != '-']

# Convert to numeric
df[odds_home_col] = pd.to_numeric(df[odds_home_col], errors='coerce')
df[odds_draw_col] = pd.to_numeric(df[odds_draw_col], errors='coerce')
df[odds_away_col] = pd.to_numeric(df[odds_away_col], errors='coerce')

# Remove rows with NaN odds
df = df.dropna(subset=[odds_home_col, odds_draw_col, odds_away_col])

print(f"✅ {len(df)} matches with valid odds")

if len(df) == 0:
    print("❌ No valid matches found")
    print("💡 Check that your CSV has odds in columns: Odds Home, Odds Draw, Odds Away")
    sys.exit(1)

# ============================================================
# SHOW FIRST FEW MATCHES
# ============================================================

print(f"\n📊 First 5 matches:")
for i in range(min(5, len(df))):
    row = df.iloc[i]
    print(f"   {i+1}. {row['Home Team']} vs {row['Away Team']}")
    print(f"      Odds: {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}")

# ============================================================
# CONVERT TO BLUEPRINT FORMAT
# ============================================================

print("\n🔄 Converting to blueprint format...")

blueprint_lines = ["📊 Summary:", f"   Total qualifying matches: {len(df)}", ""]

for idx, row in df.iterrows():
    h = float(row['Odds Home'])
    d = float(row['Odds Draw'])
    a = float(row['Odds Away'])
    
    # Determine blueprint type based on odds
    if h < 1.40:
        bp = "🟢 BP1"
        play = "Straight Home Win"
        risk = "Ultra-Low"
    elif h < 1.70:
        bp = "🟢 BP2"
        play = "Home Win"
        risk = "Low"
    elif h < 2.00:
        bp = "🟡 BP3"
        play = "1X & Over 1.5 Goals"
        risk = "Low-Moderate"
    elif d < 3.20:
        bp = "🔴 BP6"
        play = "Full Time Draw"
        risk = "High (Strategic)"
    else:
        bp = "🟡 BP7"
        play = "GG / Over 2.5 Goals"
        risk = "Moderate-High"
    
    bp_names = {
        "🟢 BP1": "THE ELITE HOME BANKER",
        "🟢 BP2": "THE PRIMARY FAVORITE",
        "🟡 BP3": "THE MODERATE FAVORITE SAFETY",
        "🔴 BP6": "THE STRONG DRAW",
        "🟡 BP7": "THE HIGH-SCORING SIGNALS"
    }
    
    blueprint_lines.append(f"{bp} {idx+1}. {bp_names.get(bp, 'MATCH')}")
    blueprint_lines.append(f"   🏟️ {row['Home Team']} vs {row['Away Team']}")
    blueprint_lines.append(f"   🏆 {row['Competition']}")
    blueprint_lines.append(f"   📊 Odds: {h} | {d} | {a}")
    blueprint_lines.append(f"   🎯 Play: {play}")
    blueprint_lines.append(f"   ⚠️ Risk: {risk}")
    blueprint_lines.append("")

blueprint_text = "\n".join(blueprint_lines)
print(f"✅ Converted {len(df)} matches")

# ============================================================
# APPLY FILTER ENGINE
# ============================================================

print("\n🔄 Applying filter engine...")

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
print(f"✅ Parsed {len(matches)} matches")

if len(matches) == 0:
    print("\n❌ No matches parsed!")
    print("\nBlueprint preview:")
    print(blueprint_text[:800])
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

message = telegram.build_telegram_message(results_df, blueprint_text, len(df))
success = telegram.send_telegram_message(message)

if success:
    print("✅ Results sent to Telegram!")
else:
    print("❌ Failed to send")

# Save results
results_df.to_csv('filtered_results.csv', index=False)
print(f"\n📁 Saved filtered_results.csv")
print(f"✅ Done! Processed {len(df)} matches -> {len(results_df)} filtered")
