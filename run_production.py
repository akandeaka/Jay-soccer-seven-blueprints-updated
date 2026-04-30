import os
import sys
import pandas as pd
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
print(f"Loaded {len(df)} rows")

# Filter valid odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = df['Odds Home'].astype(float)
df['Odds Draw'] = df['Odds Draw'].astype(float)
df['Odds Away'] = df['Odds Away'].astype(float)

print(f"Matches with odds: {len(df)}")

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

print(f"Qualified: {len(matches)}")

if len(matches) == 0:
    print("No matches qualified")
    sys.exit(1)

matches.sort(key=lambda x: x[4], reverse=True)
top_matches = matches[:min(20, len(matches))]

msg = f"⚽ RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"Qualified: {len(matches)} | Showing: {len(top_matches)}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

for i, m in enumerate(top_matches, 1):
    bp, name, play, risk, conf, row = m
    tier = "🔥" if conf >= 85 else "✅" if conf >= 70 else "⚠️"
    msg += f"\n{i}. {tier} {bp}: {name}\n"
    msg += f"   {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   {row['Competition']}\n"
    msg += f"   Odds: {row['Odds Home']}|{row['Odds Draw']}|{row['Odds Away']}\n"
    msg += f"   Play: {play}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)
telegram.send_telegram_message(msg)
print("Done")
