import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("ðŸ“Š PRODUCTION SYSTEM - 25 MATCHES INCLUDING DRAWS")
print(f"â° {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

# Store all qualified matches
all_matches = []

for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # BP1: Home 1.20-1.29, Away >= 10.0
    if 1.20 <= h <= 1.29 and a >= 10.0:
        all_matches.append(('BP1', 'THE ELITE HOME BANKER', 'Straight Home Win', 'Ultra-Low', 95, row))
    
    # BP2: Home 1.30-1.36, Away >= 9.0
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        all_matches.append(('BP2', 'THE PRIMARY FAVORITE', 'Home Win', 'Low', 90, row))
    
    # BP3: Home 1.30-1.36, Away 7.0-8.99
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        all_matches.append(('BP3', 'THE MODERATE FAVORITE SAFETY', '1X & Over 1.5 Goals', 'Low-Moderate', 85, row))
    
    # BP4: Home 1.72-1.80
    elif 1.72 <= h <= 1.80:
        all_matches.append(('BP4', 'THE GOAL ENGINE', 'Over 1.5 Goals', 'Moderate', 75, row))
    
    # BP5: Home 1.90-2.02
    elif 1.90 <= h <= 2.02:
        all_matches.append(('BP5', 'THE DEFENSIVE TRAP', '1X & Under 3.5 FT', 'Moderate', 70, row))
    
    # BP6: Draw 2.75-3.39
    elif 2.75 <= d <= 3.39:
        all_matches.append(('BP6', 'THE STRONG DRAW', 'Full Time Draw (X)', 'High (Strategic)', 50, row))
    
    # BP7A: Draw 3.40-3.56
    elif 3.40 <= d <= 3.56:
        all_matches.append(('BP7', 'THE HIGH-SCORING SIGNALS (A)', 'GG / Over 2.5 Goals', 'Moderate-High', 60, row))
    
    # BP7B: Draw 3.60-3.75
    elif 3.60 <= d <= 3.75:
        all_matches.append(('BP7', 'THE HIGH-SCORING SIGNALS (B)', 'HT 0.5 Goals / Over 2.5 Goals', 'Moderate-High', 60, row))

print(f"Total qualified for all blueprints: {len(all_matches)}")

if len(all_matches) == 0:
    print("No matches qualified")
    sys.exit(1)

# Sort by confidence (higher first, but draws have lower confidence so they appear after)
all_matches.sort(key=lambda x: x[4], reverse=True)

# Take top 25 matches
top_matches = all_matches[:25]

print(f"\nðŸ“Š BREAKDOWN OF TOP 25:")
bp_count = {}
for m in top_matches:
    bp = m[0]
    bp_count[bp] = bp_count.get(bp, 0) + 1
for bp, count in sorted(bp_count.items()):
    print(f"   {bp}: {count} matches")

# Build message
msg = f"âš½ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
msg += f"ðŸ“Š Total qualified: {len(all_matches)} | Showing TOP 25\n"
msg += "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"

for i, m in enumerate(top_matches, 1):
    bp, name, play, risk, conf, row = m
    
    if conf >= 85:
        tier = "ðŸ”¥ GOLD"
    elif conf >= 70:
        tier = "âœ… SILVER"
    else:
        tier = "âš ï¸ BRONZE"
    
    msg += f"\n{i}. {tier} {bp}: {name}\n"
    msg += f"   ðŸŸï¸ {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   ðŸ† {row['Competition']}\n"
    msg += f"   ðŸ“Š {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}\n"
    msg += f"   ðŸŽ¯ {play}\n"
    msg += f"   âš ï¸ {risk}\n"
    msg += f"   ðŸ“ˆ Confidence: {conf}%\n"
    msg += "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"

# Send to Telegram
telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
    print("Sent in 2 parts")
else:
    telegram.send_telegram_message(msg)
    print("Sent successfully")

print("\nâœ… Done!")
