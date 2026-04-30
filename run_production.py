#!/usr/bin/env python3
"""
PRODUCTION SYSTEM - TOP 20 ONLY (Fixes "message too long" error)
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

# ============================================================
# CLASSIFY USING YOUR ORIGINAL 7 BLUEPRINTS
# ============================================================

matches = []

for idx, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # YOUR EXACT BLUEPRINT RULES
    if 1.20 <= h <= 1.29 and a >= 10.0:
        matches.append({
            'bp': 'BP1', 'name': 'THE ELITE HOME BANKER',
            'play': 'Straight Home Win', 'risk': 'Ultra-Low',
            'confidence': 95, 'color': '🟢',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        matches.append({
            'bp': 'BP2', 'name': 'THE PRIMARY FAVORITE',
            'play': 'Home Win', 'risk': 'Low',
            'confidence': 90, 'color': '🟢',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        matches.append({
            'bp': 'BP3', 'name': 'THE MODERATE FAVORITE SAFETY',
            'play': '1X & Over 1.5 Goals', 'risk': 'Low-Moderate',
            'confidence': 85, 'color': '🟡',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 1.72 <= h <= 1.80:
        matches.append({
            'bp': 'BP4', 'name': 'THE GOAL ENGINE',
            'play': 'Over 1.5 Goals', 'risk': 'Moderate',
            'confidence': 75, 'color': '🟡',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 1.90 <= h <= 2.02:
        matches.append({
            'bp': 'BP5', 'name': 'THE DEFENSIVE TRAP',
            'play': '1X & Under 3.5 FT', 'risk': 'Moderate',
            'confidence': 70, 'color': '🟡',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 2.75 <= d <= 3.39:
        matches.append({
            'bp': 'BP6', 'name': 'THE STRONG DRAW',
            'play': 'Full Time Draw', 'risk': 'High',
            'confidence': 50, 'color': '🔴',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 3.40 <= d <= 3.56:
        matches.append({
            'bp': 'BP7', 'name': 'THE HIGH-SCORING SIGNALS',
            'play': 'GG / Over 2.5 Goals', 'risk': 'Moderate-High',
            'confidence': 60, 'color': '🟡',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })
    elif 3.60 <= d <= 3.75:
        matches.append({
            'bp': 'BP7', 'name': 'THE HIGH-SCORING SIGNALS',
            'play': 'HT 0.5 Goals / Over 2.5 Goals', 'risk': 'Moderate-High',
            'confidence': 60, 'color': '🟡',
            'home': row['Home Team'], 'away': row['Away Team'],
            'league': row['Competition'], 'h_odds': h, 'd_odds': d, 'a_odds': a
        })

print(f"✅ {len(matches)} matches qualified")

if len(matches) == 0:
    print("❌ No matches qualified")
    sys.exit(1)

# ============================================================
# TAKE ONLY TOP 20 MATCHES
# ============================================================

matches = sorted(matches, key=lambda x: x['confidence'], reverse=True)
top_20 = matches[:20]

print(f"✅ Selected TOP 20 matches (from {len(matches)} total)")

# ============================================================
# BUILD TELEGRAM MESSAGE (ONLY TOP 20)
# ============================================================

message = f"""
⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total matches: {len(df)}
✅ Blueprint qualified: {len(matches)}
🏆 Showing TOP 20 picks below

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP 20 PICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

for idx, m in enumerate(top_20, 1):
    if m['confidence'] >= 85:
        tier = "🔥 GOLD"
    elif m['confidence'] >= 70:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"
    
    message += f"""
{idx}. {tier} {m['bp']}: {m['name']}
   🏟️ {m['home']} vs {m['away']}
   🏆 {m['league']}
   📊 {m['h_odds']} | {m['d_odds']} | {m['a_odds']}
   🎯 {m['play']}
   ⚠️ {m['risk']}
   📈 Confidence: {m['confidence']}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================
# SEND TO TELEGRAM
# ============================================================

print("\n📤 Sending to Telegram...")

from filter_engine import TelegramIntegrator, FilterConfig

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

# Check message length
if len(message) > 4096:
    print(f"⚠️ Message length: {len(message)} characters (exceeds 4096)")
    print("Splitting into 2 messages...")
    
    # Split into two messages
    split_point = message[:3500].rfind('\n')
    part1 = message[:split_point]
    part2 = "📊 CONTINUED...\n" + message[split_point:]
    
    telegram.send_telegram_message(part1)
    telegram.send_telegram_message(part2)
    print("✅ Sent in 2 parts")
else:
    print(f"✅ Message length: {len(message)} characters")
    telegram.send_telegram_message(message)
    print("✅ Sent successfully")

# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(top_20)
results_df.to_csv('top_20_picks.csv', index=False)
print(f"\n📁 Saved top_20_picks.csv")
print(f"✅ Done! Processed {len(df)} matches -> {len(matches)} qualified -> TOP 20 sent")
