#!/usr/bin/env python3
"""
PRODUCTION: Filtered Blueprint Bot
FORCES reading from CSV file - NO DEMO DATA
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🚀 FILTERED BLUEPRINT BOT - PRODUCTION MODE")
print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

# ============================================================
# STEP 1: READ FROM CSV FILE - NO DEMO DATA
# ============================================================

csv_file = "matches_today.csv"

print(f"\n📂 Looking for CSV file: {csv_file}")
print(f"   Current directory: {os.getcwd()}")

# Check if CSV exists
if not os.path.exists(csv_file):
    print(f"\n❌ ERROR: {csv_file} not found!")
    print("\n📁 Files in current directory:")
    for f in os.listdir('.'):
        if f.endswith('.csv'):
            print(f"   - {f}")
    sys.exit(1)

print(f"✅ Found {csv_file}")

# Read CSV
try:
    df = pd.read_csv(csv_file)
    print(f"✅ Read {len(df)} rows from CSV")
    print(f"   Columns: {list(df.columns)}")
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    sys.exit(1)

if len(df) == 0:
    print("❌ CSV file is empty!")
    sys.exit(1)

# Show first few rows
print(f"\n📊 CSV Preview (first 3 rows):")
print(df.head(3).to_string())

# ============================================================
# STEP 2: CONVERT CSV TO BLUEPRINT FORMAT
# ============================================================

print("\n🔄 Converting CSV to blueprint format...")

blueprint_lines = []
blueprint_lines.append("📊 Summary:")
blueprint_lines.append(f"   Total qualifying matches: {len(df)}")
blueprint_lines.append("")
blueprint_lines.append("📊 Total scanned: 251")
blueprint_lines.append("")

for idx, row in df.iterrows():
    # Get values with fallbacks
    home_team = str(row.get('Home Team', row.get('home_team', 'Unknown')))
    away_team = str(row.get('Away Team', row.get('away_team', 'Unknown')))
    league = str(row.get('League', row.get('league', 'Unknown')))
    
    home_odds = float(row.get('Home Odds', row.get('home_odds', 2.0)))
    draw_odds = float(row.get('Draw Odds', row.get('draw_odds', 3.0)))
    away_odds = float(row.get('Away Odds', row.get('away_odds', 3.0)))
    
    # Determine blueprint based on odds
    if home_odds < 1.40:
        blueprint = "🟢 BP1"
        play = "Straight Home Win"
        risk = "Ultra-Low"
    elif home_odds < 1.70:
        blueprint = "🟢 BP2"
        play = "Home Win"
        risk = "Low"
    elif home_odds < 2.00:
        blueprint = "🟡 BP3"
        play = "1X & Over 1.5 Goals"
        risk = "Low-Moderate"
    elif draw_odds < 3.20:
        blueprint = "🔴 BP6"
        play = "Full Time Draw"
        risk = "High (Strategic)"
    else:
        blueprint = "🟡 BP7"
        play = "GG / Over 2.5 Goals"
        risk = "Moderate-High"
    
    # Get blueprint name
    bp_names = {
        "🟢 BP1": "THE ELITE HOME BANKER",
        "🟢 BP2": "THE PRIMARY FAVORITE",
        "🟡 BP3": "THE MODERATE FAVORITE SAFETY",
        "🔴 BP6": "THE STRONG DRAW",
        "🟡 BP7": "THE HIGH-SCORING SIGNALS"
    }
    bp_name = bp_names.get(blueprint, "MATCH")
    
    blueprint_lines.append(f"{blueprint} {idx+1}. {bp_name}")
    blueprint_lines.append(f"   🏟️ {home_team} vs {away_team}")
    blueprint_lines.append(f"   🏆 {league}")
    blueprint_lines.append(f"   📊 Odds: {home_odds} | {draw_odds} | {away_odds}")
    blueprint_lines.append(f"   🎯 Play: {play}")
    blueprint_lines.append(f"   ⚠️ Risk: {risk}")
    blueprint_lines.append("")

blueprint_text = "\n".join(blueprint_lines)
print(f"✅ Converted {len(df)} matches to blueprint format")

# ============================================================
# STEP 3: APPLY FILTER ENGINE
# ============================================================

print("\n🔄 Applying filter engine...")

# Import filter engine
try:
    from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig
    print("✅ Filter engine imported")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Parse and process
engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
print(f"✅ Parsed {len(matches)} matches")

if len(matches) == 0:
    print("❌ No matches parsed! Check blueprint format.")
    sys.exit(1)

results_df = engine.process_matches(matches)
print(f"✅ Processed {len(results_df)} results")

# ============================================================
# STEP 4: BUILD ACCUMULATORS
# ============================================================

print("\n🔨 Building accumulators...")

try:
    from accumulator_builder import AccumulatorBuilder
    builder = AccumulatorBuilder()
    top_matches = results_df.head(20).to_dict('records')
    accumulators = builder.build_all_accumulators(top_matches)
    print(f"✅ Built accumulators from {len(top_matches)} top matches")
except Exception as e:
    print(f"⚠️ Accumulator builder error: {e}")
    accumulators = {}

# ============================================================
# STEP 5: SEND TO TELEGRAM
# ============================================================

print("\n📤 Sending to Telegram...")

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

# Build message
filtered_message = telegram.build_telegram_message(results_df, blueprint_text, len(df))

# Add accumulators if available
if accumulators:
    from accumulator_builder import AccumulatorBuilder
    temp_builder = AccumulatorBuilder()
    accumulator_message = temp_builder.format_accumulator_message(accumulators, len(top_matches))
    final_message = filtered_message + "\n" + accumulator_message
else:
    final_message = filtered_message

# Send
success = telegram.send_telegram_message(final_message)

if success:
    print("✅ Results sent to Telegram successfully!")
else:
    print("❌ Failed to send to Telegram")

# ============================================================
# STEP 6: SAVE RESULTS
# ============================================================

results_df.to_csv('filtered_results.csv', index=False)
results_df.head(20).to_csv('top_20_picks.csv', index=False)
print("\n📁 Results saved:")
print("   - filtered_results.csv")
print("   - top_20_picks.csv")

print("\n" + "="*60)
print("✅ PRODUCTION BOT EXECUTION COMPLETE")
print("="*60)
