#!/usr/bin/env python3
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

# Build blueprint text
blueprint_lines = []
for idx, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    if h < 1.40:
        bp, play = "BP1", "Straight Home Win"
    elif h < 1.70:
        bp, play = "BP2", "Home Win"
    elif h < 2.00:
        bp, play = "BP3", "1X & Over 1.5"
    elif d < 3.20:
        bp, play = "BP6", "Full Time Draw"
    else:
        bp, play = "BP7", "GG / Over 2.5"
    
    blueprint_lines.append(f"{bp} {idx+1}. MATCH")
    blueprint_lines.append(f"{row['Home Team']} vs {row['Away Team']}")
    blueprint_lines.append(f"{row['Competition']}")
    blueprint_lines.append(f"Odds: {h} | {d} | {a}")
    blueprint_lines.append(f"Play: {play}")
    blueprint_lines.append("")

blueprint_text = "\n".join(blueprint_lines)

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

print(f"✅ Done! Processed {len(df)} matches -> {len(results_df)} filtered")
