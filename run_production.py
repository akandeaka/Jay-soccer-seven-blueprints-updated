#!/usr/bin/env python3
"""
PRODUCTION: Reads YOUR CSV format
Columns: Competition, Home Team, Away Team, Odds Home, Odds Draw, Odds Away
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🚀 PRODUCTION MODE - YOUR CSV FORMAT")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# ============================================================
# READ YOUR CSV FILE
# ============================================================

CSV_FILE = "matches_today.csv"

print(f"\n📂 Reading: {CSV_FILE}")

if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: {CSV_FILE} not found!")
    sys.exit(1)

# Read CSV
df = pd.read_csv(CSV_FILE)
print(f"✅ Loaded {len(df)} rows")
print(f"   Columns: {list(df.columns)}")

# ============================================================
# FILTER ONLY MATCHES WITH ODDS (remove - or empty odds)
# ============================================================

# Remove rows where odds are missing or '-'
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

# Convert odds to float
df['Odds Home'] = pd.to_numeric(df['Odds Home'], errors='coerce')
df['Odds Draw'] = pd.to_numeric(df['Odds Draw'], errors='coerce')
df['Odds Away'] = pd.to_numeric(df['Odds Away'], errors='coerce')

# Remove rows with NaN odds
df = df.dropna(subset=['Odds Home', 'Odds Draw', 'Odds Away'])

print(f"✅ After filtering: {len(df)} matches with valid odds")

if len(df) == 0:
    print("❌ No matches with valid odds!")
    sys.exit(1)

# ============================================================
# SHOW FIRST FEW MATCHES
# ============================================================

print(f"\n📊 First 5 matches from your CSV:")
for i in range(min(5, len(df))):
    row = df.iloc[i]
    print(f"   {i+1}. {row['Home Team']} vs {row['Away Team']}")
    print(f"      League: {row['Competition']}")
    print(f"      Odds: {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}")

# ============================================================
# CONVERT TO BLUEPRINT FORMAT
# ============================================================

print("\n🔄 Converting to blueprint format...")

blueprint_lines = []
blueprint_lines.append("📊 Summary:")
blueprint_lines.append(f"   Total qualifying matches: {len(df)}")
blueprint_lines.append("")

for idx, row in df.iterrows():
    home_team = str(row['Home Team'])
    away_team = str(row['Away Team'])
    league = str(row['Competition'])
    home_odds = float(row['Odds Home'])
    draw_odds = float(row['Odds Draw'])
    away_odds = float(row['Odds Away'])
    
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
    
    bp_names = {
        "🟢 BP1": "THE ELITE HOME BANKER",
        "🟢 BP2": "THE PRIMARY FAVORITE",
        "🟡 BP3": "THE MODERATE FAVORITE SAFETY",
        "🔴 BP6": "THE STRONG DRAW",
        "🟡 BP7": "THE HIGH-SCORING SIGNALS"
    }
    
    blueprint_lines.append(f"{blueprint} {idx+1}. {bp_names.get(blueprint, 'MATCH')}")
    blueprint_lines.append(f"   🏟️ {home_team} vs {away_team}")
    blueprint_lines.append(f"   🏆 {league}")
    blueprint_lines.append(f"   📊 Odds: {home_odds} | {draw_odds} | {away_odds}")
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
    print("\n❌ No matches parsed! Check blueprint format.")
    print("\nBlueprint preview:")
    print(blueprint_text[:500])
    sys.exit(1)

results_df = engine.process_matches(matches)

# ============================================================
# BUILD ACCUMULATORS
# ============================================================

print("\n🔨 Building accumulators...")

try:
    from accumulator_builder import AccumulatorBuilder
    builder = AccumulatorBuilder()
    top_matches = results_df.head(20).to_dict('records')
    accumulators = builder.build_all_accumulators(top_matches)
    
    for name, acc in accumulators.items():
        if acc:
            odds = 1.0
            for m in acc:
                odds *= builder.calculate_match_odds(m)
            print(f"   {name}: {len(acc)} picks @ {odds:.2f}x")
except Exception as e:
    print(f"⚠️ Accumulator error: {e}")
    accumulators = {}

# ============================================================
# SEND TO TELEGRAM
# ============================================================

print("\n📤 Sending to Telegram...")

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

# Main filtered message
filtered_message = telegram.build_telegram_message(results_df, blueprint_text, len(df))

# Add accumulators
if accumulators:
    from accumulator_builder import AccumulatorBuilder
    temp = AccumulatorBuilder()
    acc_message = temp.format_accumulator_message(accumulators, len(top_matches))
    final_message = filtered_message + "\n" + acc_message
else:
    final_message = filtered_message

# Send
success = telegram.send_telegram_message(final_message)

if success:
    print("✅ Results sent to Telegram!")
else:
    print("❌ Failed to send to Telegram")

# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv('filtered_results.csv', index=False)
results_df.head(20).to_csv('top_20_picks.csv', index=False)
print("\n📁 Saved: filtered_results.csv, top_20_picks.csv")

print("\n" + "="*60)
print("✅ PRODUCTION BOT EXECUTION COMPLETE")
print(f"   Processed {len(df)} matches from your CSV")
print("="*60)
