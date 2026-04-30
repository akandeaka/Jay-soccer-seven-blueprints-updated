#!/usr/bin/env python3
"""
PRODUCTION - READS ONLY FROM CSV, NO HARDCODED DATA
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🚀 PRODUCTION BOT")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# ============================================================
# ONLY READ FROM CSV - NO HARDCODED DATA
# ============================================================

CSV_FILE = "matches_today.csv"

if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: {CSV_FILE} not found!")
    sys.exit(1)

# Read CSV
df = pd.read_csv(CSV_FILE)
print(f"✅ Loaded {len(df)} matches from CSV")

# Remove rows without odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = pd.to_numeric(df['Odds Home'])
df['Odds Draw'] = pd.to_numeric(df['Odds Draw'])
df['Odds Away'] = pd.to_numeric(df['Odds Away'])
df = df.dropna()

print(f"✅ {len(df)} matches with valid odds")

if len(df) == 0:
    print("❌ No valid matches")
    sys.exit(1)

# Build blueprint text from CSV
blueprint_text = "📊 Summary:\n"
blueprint_text += f"   Total qualifying matches: {len(df)}\n\n"

for idx, row in df.iterrows():
    h_odds = row['Odds Home']
    d_odds = row['Odds Draw']
    a_odds = row['Odds Away']
    
    if h_odds < 1.40:
        bp, play = "🟢 BP1", "Straight Home Win"
    elif h_odds < 1.70:
        bp, play = "🟢 BP2", "Home Win"
    elif h_odds < 2.00:
        bp, play = "🟡 BP3", "1X & Over 1.5"
    elif d_odds < 3.20:
        bp, play = "🔴 BP6", "Full Time Draw"
    else:
        bp, play = "🟡 BP7", "GG / Over 2.5"
    
    blueprint_text += f"{bp} {idx+1}. MATCH\n"
    blueprint_text += f"   🏟️ {row['Home Team']} vs {row['Away Team']}\n"
    blueprint_text += f"   🏆 {row['Competition']}\n"
    blueprint_text += f"   📊 Odds: {h_odds} | {d_odds} | {a_odds}\n"
    blueprint_text += f"   🎯 Play: {play}\n"
    blueprint_text += f"   ⚠️ Risk: Moderate\n\n"

# Apply filter
from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
results_df = engine.process_matches(matches)

# Send to Telegram
telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

message = telegram.build_telegram_message(results_df, blueprint_text, len(df))
telegram.send_telegram_message(message)

print(f"✅ Sent {len(results_df)} filtered matches to Telegram")
