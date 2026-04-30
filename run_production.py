#!/usr/bin/env python3
"""
PRODUCTION: NO DEMO DATA - READS ONLY FROM CSV
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🚀 PRODUCTION MODE - NO DEMO DATA")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# ============================================================
# MUST READ FROM CSV - NO FALLBACK TO DEMO
# ============================================================

CSV_FILE = "matches_today.csv"

print(f"\n📂 Reading from: {CSV_FILE}")

if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: {CSV_FILE} not found!")
    print("\n📁 Available files:")
    for f in os.listdir('.'):
        if f.endswith('.csv'):
            print(f"   - {f}")
    sys.exit(1)

# Read CSV
df = pd.read_csv(CSV_FILE)
print(f"✅ Loaded {len(df)} matches")

if len(df) == 0:
    print("❌ CSV is empty!")
    sys.exit(1)

# Show what we loaded
print(f"\n📊 First 3 matches:")
for i in range(min(3, len(df))):
    row = df.iloc[i]
    print(f"   {i+1}. {row.get('Home Team', '?')} vs {row.get('Away Team', '?')} - {row.get('League', '?')}")

# ============================================================
# Convert to blueprint format
# ============================================================

print("\n🔄 Converting to blueprint format...")

blueprint_lines = []
blueprint_lines.append("📊 Summary:")
blueprint_lines.append(f"   Total qualifying matches: {len(df)}")
blueprint_lines.append("")

for idx, row in df.iterrows():
    home = str(row.get('Home Team', row.get('home_team', 'Unknown')))
    away = str(row.get('Away Team', row.get('away_team', 'Unknown')))
    league = str(row.get('League', row.get('league', 'Unknown')))
    h_odds = float(row.get('Home Odds', row.get('home_odds', 2.0)))
    d_odds = float(row.get('Draw Odds', row.get('draw_odds', 3.0)))
    a_odds = float(row.get('Away Odds', row.get('away_odds', 3.0)))
    
    # Determine blueprint
    if h_odds < 1.40:
        bp = "🟢 BP1"
        play = "Straight Home Win"
        risk = "Ultra-Low"
    elif h_odds < 1.70:
        bp = "🟢 BP2"
        play = "Home Win"
        risk = "Low"
    elif h_odds < 2.00:
        bp = "🟡 BP3"
        play = "1X & Over 1.5"
        risk = "Low-Moderate"
    elif d_odds < 3.20:
        bp = "🔴 BP6"
        play = "Full Time Draw"
        risk = "High"
    else:
        bp = "🟡 BP7"
        play = "GG / Over 2.5"
        risk = "Moderate-High"
    
    bp_names = {
        "🟢 BP1": "THE ELITE HOME BANKER",
        "🟢 BP2": "THE PRIMARY FAVORITE",
        "🟡 BP3": "THE MODERATE FAVORITE SAFETY",
        "🔴 BP6": "THE STRONG DRAW",
        "🟡 BP7": "THE HIGH-SCORING SIGNALS"
    }
    
    blueprint_lines.append(f"{bp} {idx+1}. {bp_names.get(bp, 'MATCH')}")
    blueprint_lines.append(f"   🏟️ {home} vs {away}")
    blueprint_lines.append(f"   🏆 {league}")
    blueprint_lines.append(f"   📊 Odds: {h_odds} | {d_odds} | {a_odds}")
    blueprint_lines.append(f"   🎯 Play: {play}")
    blueprint_lines.append(f"   ⚠️ Risk: {risk}")
    blueprint_lines.append("")

blueprint_text = "\n".join(blueprint_lines)

# ============================================================
# Apply filter engine
# ============================================================

print("\n🔄 Applying filter engine...")

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
print(f"✅ Parsed {len(matches)} matches")

results_df = engine.process_matches(matches)

# ============================================================
# Build accumulators
# ============================================================

print("\n🔨 Building accumulators...")

try:
    from accumulator_builder import AccumulatorBuilder
    builder = AccumulatorBuilder()
    top_matches = results_df.head(20).to_dict('records')
    accumulators = builder.build_all_accumulators(top_matches)
    
    # Print accumulator summary
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
# Send to Telegram
# ============================================================

print("\n📤 Sending to Telegram...")

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

# Main message
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
    print("✅ Sent to Telegram!")
else:
    print("❌ Failed to send")

# Save results
results_df.to_csv('filtered_results.csv', index=False)
results_df.head(20).to_csv('top_20_picks.csv', index=False)
print("\n📁 Saved: filtered_results.csv, top_20_picks.csv")

print("\n✅ DONE - NO DEMO DATA USED")
