#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
import pandas as pd
import numpy as np
from datetime import datetime

# Force UTF-8 for console output (fixes mojibake)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import your Telegram module – adjust class name if needed
from telegram_integration.py import Telegram integration
from config import FilterConfig  # assumed to contain bot token & chat id

# ============================================================
# 1. LOAD AND CLEAN DATA
# ============================================================

df = pd.read_csv('matches_today (2).csv', encoding='utf-8')

# Clean odds columns: replace non-numeric with NaN
for col in ['Odds Home', 'Odds Draw', 'Odds Away']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Remove rows missing any odds or not scheduled (optional: keep only 'Scheduled')
df = df.dropna(subset=['Odds Home', 'Odds Draw', 'Odds Away'])
df = df[df['Status'].str.lower() == 'scheduled']

print(f"Loaded {len(df)} qualifying matches")

# ============================================================
# 2. BLUEPRINT CLASSIFICATION
# ============================================================

def classify_match(row):
    home = row['Odds Home']
    draw = row['Odds Draw']
    away = row['Odds Away']
    
    # GOLD BP1: ELITE HOME BANKER (odds ≤ 1.30)
    if home <= 1.30:
        return ('🔥 GOLD BP1: THE ELITE HOME BANKER',
                'Straight Home Win',
                'Ultra-Low',
                95)
    
    # GOLD BP2: PRIMARY FAVORITE (1.31 ≤ odds ≤ 1.45)
    if home <= 1.45:
        return ('🔥 GOLD BP2: THE PRIMARY FAVORITE',
                'Home Win',
                'Low',
                90)
    
    # GOLD BP3: MODERATE FAVORITE SAFETY (1.46 ≤ odds ≤ 1.70)
    if home <= 1.70:
        return ('🔥 GOLD BP3: THE MODERATE FAVORITE SAFETY',
                '1X & Over 1.5 Goals',
                'Low-Moderate',
                85)
    
    # SILVER BP4: GOAL ENGINE (home odds 1.71 – 2.10, draws > 3.0)
    if home <= 2.10 and draw > 3.0:
        return ('✅ SILVER BP4: THE GOAL ENGINE',
                'Over 1.5 Goals',
                'Moderate',
                75)
    
    # SILVER BP5: DEFENSIVE TRAP (home odds 1.90 – 2.20, home or draw)
    if 1.90 <= home <= 2.20:
        return ('✅ SILVER BP5: THE DEFENSIVE TRAP',
                '1X & Under 3.5 FT',
                'Moderate',
                70)
    
    # BRONZE BP7: HIGH-SCORING SIGNALS (odds > 2.20, both teams expected to score)
    # Simplified: home > 2.20 and away not too heavy favorite
    if home > 2.20 and away < 3.00:
        # Decide between A (GG/Over2.5) and B (HT 0.5/Over2.5) – take A for simplicity
        return ('⚠️ BRONZE BP7: THE HIGH-SCORING SIGNALS (A)',
                'GG / Over 2.5 Goals',
                'Moderate-High',
                60)
    
    # Fallback (should not happen with our filtered data)
    return ('⚪ UNCLASSIFIED',
            'None',
            'Unknown',
            50)

# Apply classification
results = []
for idx, row in df.iterrows():
    bp, play, risk, conf = classify_match(row)
    results.append((bp, play, risk, conf, row))

# Sort by confidence descending, then by odds home ascending
results.sort(key=lambda x: (-x[3], x[4]['Odds Home']))

all_matches = results
top_matches = all_matches[:25]

# ============================================================
# 3. DISPLAY BREAKDOWN
# ============================================================

print("\n📊 BREAKDOWN OF TOP 25:")
bp_count = {}
for m in top_matches:
    bp = m[0]
    bp_count[bp] = bp_count.get(bp, 0) + 1
for bp, count in sorted(bp_count.items()):
    print(f"   {bp}: {count} matches")

# ============================================================
# 4. BUILD TELEGRAM MESSAGE (CLEAN UTF-8)
# ============================================================

msg = f"⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total qualified: {len(all_matches)} | Showing TOP 25\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

for i, m in enumerate(top_matches, 1):
    bp, play, risk, conf, row = m

    # Determine tier (already in bp string, but we can keep)
    if "GOLD" in bp:
        tier = "🔥 GOLD"
    elif "SILVER" in bp:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"

    msg += f"\n{i}. {bp}\n"
    msg += f"   🏟️ {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   🏆 {row['Competition']}\n"
    msg += f"   📊 {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}\n"
    msg += f"   🎯 {play}\n"
    msg += f"   ⚠️ {risk}\n"
    msg += f"   📈 Confidence: {conf}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# ============================================================
# 5. SEND TO TELEGRAM
# ============================================================

telegram = TelegramIntegration(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
    print("Sent in 2 parts")
else:
    telegram.send_telegram_message(msg)
    print("Sent successfully")

print("\n✅ Done!")
