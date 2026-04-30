#!/usr/bin/env python3
import sys, os, pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

CSV_FILE = "matches_today.csv"

if not os.path.exists(CSV_FILE):
    print(f"ERROR: {CSV_FILE} not found")
    sys.exit(1)

df = pd.read_csv(CSV_FILE)
print(f"Loaded {len(df)} total rows")

# Count rows with '-' odds
no_odds = df[df['Odds Home'] == '-'].shape[0]
print(f"Rows without odds (-): {no_odds}")

# Filter to only rows with actual odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = pd.to_numeric(df['Odds Home'])
df['Odds Draw'] = pd.to_numeric(df['Odds Draw'])
df['Odds Away'] = pd.to_numeric(df['Odds Away'])
df = df.dropna()

print(f"Matches with valid odds: {len(df)}")

if len(df) == 0:
    print("No matches with valid odds")
    sys.exit(1)

# Your 7 Blueprints
matches = []
for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    if 1.20 <= h <= 1.29 and a >= 10.0:
        matches.append(('BP1', 'THE ELITE HOME BANKER', 'Straight Home Win', 'Ultra-Low', 95, row))
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        matches.append(('BP2', 'THE PRIMARY FAVORITE', 'Home Win', 'Low', 90, row))
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        matches.append(('BP3', 'THE MODERATE FAVORITE SAFETY', '1X & Over 1.5 Goals', 'Low-Moderate', 85, row))
    elif 1.72 <= h <= 1.80:
        matches.append(('BP4', 'THE GOAL ENGINE', 'Over 1.5 Goals', 'Moderate', 75, row))
    elif 1.90 <= h <= 2.02:
        matches.append(('BP5', 'THE DEFENSIVE TRAP', '1X & Under 3.5 FT', 'Moderate', 70, row))
    elif 2.75 <= d <= 3.39:
        matches.append(('BP6', 'THE STRONG DRAW', 'Full Time Draw', 'High', 50, row))
    elif 3.40 <= d <= 3.56:
        matches.append(('BP7', 'HIGH-SCORING SIGNALS', 'GG / Over 2.5', 'Moderate-High', 60, row))
    elif 3.60 <= d <= 3.75:
        matches.append(('BP7', 'HIGH-SCORING SIGNALS', 'HT 0.5 / Over 2.5', 'Moderate-High', 60, row))

print(f"\nMatches that fit your blueprints: {len(matches)}")

if len(matches) == 0:
    print("\nNo matches fit your blueprint odds ranges.")
    print("\nYour blueprint ranges:")
    print("  BP1: Home 1.20-1.29, Away >= 10.0")
    print("  BP2: Home 1.30-1.36, Away >= 9.0")
    print("  BP3: Home 1.30-1.36, Away 7.0-8.99")
    print("  BP4: Home 1.72-1.80")
    print("  BP5: Home 1.90-2.02")
    print("  BP6: Draw 2.75-3.39")
    print("  BP7: Draw 3.40-3.75")
    print("\nShowing all matches with odds for review:")
    for _, row in df.iterrows():
        print(f"  {row['Home Team']} vs {row['Away Team']} - Home: {row['Odds Home']}, Draw: {row['Odds Draw']}, Away: {row['Odds Away']}")
    sys.exit(1)

# Top matches (up to 20, or all if less)
matches.sort(key=lambda x: x[4], reverse=True)
top_matches = matches[:min(20, len(matches))]

print(f"Sending {len(top_matches)} matches to Telegram")

# Build message
msg = f"⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total with odds: {len(df)} | Qualified: {len(matches)} | Showing: {len(top_matches)}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

for i, m in enumerate(top_matches, 1):
    bp, name, play, risk, conf, row = m
    tier = "🔥 GOLD" if conf >= 85 else "✅ SILVER" if conf >= 70 else "⚠️ BRONZE"
    msg += f"\n{i}. {tier} {bp}: {name}\n"
    msg += f"   🏟️ {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   🏆 {row['Competition']}\n"
    msg += f"   📊 {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}\n"
    msg += f"   🎯 {play}\n"
    msg += f"   ⚠️ {risk}\n"
    msg += f"   📈 Confidence: {conf}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# Send
telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
else:
    telegram.send_telegram_message(msg)

print("Done")
