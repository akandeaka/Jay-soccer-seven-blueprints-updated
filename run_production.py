import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM - DRAWS INCLUDED")
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

# Store all qualified matches - SEPARATE CHECKS FOR DRAWS
all_matches = []

for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # CHECK DRAWS FIRST (so they are not blocked by home odds)
    
    # BP6: Draw 2.75-3.39
    if 2.75 <= d <= 3.39:
        all_matches.append(('BP6', 'THE STRONG DRAW', 'Full Time Draw (X)', 'High (Strategic)', 50, row))
    
    # BP7A: Draw 3.40-3.56
    elif 3.40 <= d <= 3.56:
        all_matches.append(('BP7', 'THE HIGH-SCORING SIGNALS (A)', 'GG / Over 2.5 Goals', 'Moderate-High', 60, row))
    
    # BP7B: Draw 3.60-3.75
    elif 3.60 <= d <= 3.75:
        all_matches.append(('BP7', 'THE HIGH-SCORING SIGNALS (B)', 'HT 0.5 Goals / Over 2.5 Goals', 'Moderate-High', 60, row))
    
    # THEN CHECK HOME ODDS (BP1-BP5)
    elif 1.20 <= h <= 1.29 and a >= 10.0:
        all_matches.append(('BP1', 'THE ELITE HOME BANKER', 'Straight Home Win', 'Ultra-Low', 95, row))
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        all_matches.append(('BP2', 'THE PRIMARY FAVORITE', 'Home Win', 'Low', 90, row))
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        all_matches.append(('BP3', 'THE MODERATE FAVORITE SAFETY', '1X & Over 1.5 Goals', 'Low-Moderate', 85, row))
    elif 1.72 <= h <= 1.80:
        all_matches.append(('BP4', 'THE GOAL ENGINE', 'Over 1.5 Goals', 'Moderate', 75, row))
    elif 1.90 <= h <= 2.02:
        all_matches.append(('BP5', 'THE DEFENSIVE TRAP', '1X & Under 3.5 FT', 'Moderate', 70, row))

print(f"Total qualified matches: {len(all_matches)}")

if len(all_matches) == 0:
    print("No matches qualified")
    sys.exit(1)

# Count by blueprint
bp_counts = {}
for m in all_matches:
    bp = m[0]
    bp_counts[bp] = bp_counts.get(bp, 0) + 1

print("\n📊 QUALIFIED BY BLUEPRINT:")
for bp, count in sorted(bp_counts.items()):
    print(f"   {bp}: {count} matches")

# Sort by confidence (higher first)
all_matches.sort(key=lambda x: x[4], reverse=True)

# Take top 25
top_matches = all_matches[:25]

print(f"\n📊 TOP 25 BREAKDOWN:")
for bp, count in sorted(bp_counts.items()):
    in_top = sum(1 for m in top_matches if m[0] == bp)
    print(f"   {bp}: {in_top} in top 25")

# Build message
msg = f"⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total qualified: {len(all_matches)} | Showing TOP 25\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

for i, m in enumerate(top_matches, 1):
    bp, name, play, risk, conf, row = m
    
    if bp == 'BP1':
        tier = "🔥 GOLD"
    elif bp in ['BP2', 'BP3', 'BP4', 'BP5']:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"
    
    msg += f"\n{i}. {tier} {bp}: {name}\n"
    msg += f"   🏟️ {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   🏆 {row['Competition']}\n"
    msg += f"   📊 {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}\n"
    msg += f"   🎯 {play}\n"
    msg += f"   ⚠️ {risk}\n"
    msg += f"   📈 Confidence: {conf}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# Send to Telegram
telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
    print("Sent in 2 parts")
else:
    telegram.send_telegram_message(msg)
    print("Sent successfully")

print("\n✅ Done!")
