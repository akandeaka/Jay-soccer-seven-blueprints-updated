import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 DEBUG - CHECKING ALL BLUEPRINTS")
print("="*60)

CSV_FILE = "matches_today.csv"
df = pd.read_csv(CSV_FILE)

# Filter odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = df['Odds Home'].astype(float)
df['Odds Draw'] = df['Odds Draw'].astype(float)
df['Odds Away'] = df['Odds Away'].astype(float)

print(f"Total matches with odds: {len(df)}")

# Check each blueprint separately
bp1_matches = []
bp2_matches = []
bp3_matches = []
bp4_matches = []
bp5_matches = []
bp6_matches = []
bp7_matches = []

for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # BP1: Home 1.20-1.29, Away >= 10.0
    if 1.20 <= h <= 1.29 and a >= 10.0:
        bp1_matches.append(row)
    
    # BP2: Home 1.30-1.36, Away >= 9.0
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        bp2_matches.append(row)
    
    # BP3: Home 1.30-1.36, Away 7.0-8.99
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        bp3_matches.append(row)
    
    # BP4: Home 1.72-1.80
    elif 1.72 <= h <= 1.80:
        bp4_matches.append(row)
    
    # BP5: Home 1.90-2.02
    elif 1.90 <= h <= 2.02:
        bp5_matches.append(row)
    
    # BP6: Draw 2.75-3.39
    elif 2.75 <= d <= 3.39:
        bp6_matches.append(row)
    
    # BP7: Draw 3.40-3.75
    elif 3.40 <= d <= 3.75:
        bp7_matches.append(row)

print(f"\nBP1 (Home 1.20-1.29, Away>=10): {len(bp1_matches)}")
for m in bp1_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Home: {m['Odds Home']}, Away: {m['Odds Away']}")

print(f"\nBP2 (Home 1.30-1.36, Away>=9): {len(bp2_matches)}")
for m in bp2_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Home: {m['Odds Home']}, Away: {m['Odds Away']}")

print(f"\nBP3 (Home 1.30-1.36, Away 7-8.99): {len(bp3_matches)}")
for m in bp3_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Home: {m['Odds Home']}, Away: {m['Odds Away']}")

print(f"\nBP4 (Home 1.72-1.80): {len(bp4_matches)}")
for m in bp4_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Home: {m['Odds Home']}")

print(f"\nBP5 (Home 1.90-2.02): {len(bp5_matches)}")
for m in bp5_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Home: {m['Odds Home']}")

print(f"\nBP6 (Draw 2.75-3.39): {len(bp6_matches)}")
for m in bp6_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Draw: {m['Odds Draw']}")

print(f"\nBP7 (Draw 3.40-3.75): {len(bp7_matches)}")
for m in bp7_matches:
    print(f"   {m['Home Team']} vs {m['Away Team']} - Draw: {m['Odds Draw']}")

# Combine all
all_matches = bp1_matches + bp2_matches + bp3_matches + bp4_matches + bp5_matches + bp6_matches + bp7_matches
print(f"\n TOTAL QUALIFIED: {len(all_matches)}")

if all_matches:
    # Build message
    msg = f"⚽ ALL BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, row in enumerate(all_matches[:30], 1):
        h, d, a = row['Odds Home'], row['Odds Draw'], row['Odds Away']
        
        # Determine which BP
        if 2.75 <= d <= 3.39:
            bp = "BP6 - STRONG DRAW"
            play = "Full Time Draw"
        elif 3.40 <= d <= 3.75:
            bp = "BP7 - HIGH SCORING"
            play = "GG / Over 2.5" if d <= 3.56 else "HT 0.5 / Over 2.5"
        else:
            bp = "BP1-5"
            play = "Home Win"
        
        msg += f"\n{i}. {bp}\n"
        msg += f"   {row['Home Team']} vs {row['Away Team']}\n"
        msg += f"   {row['Competition']}\n"
        msg += f"   Odds: {h}|{d}|{a}\n"
        msg += f"   Play: {play}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)
    telegram.send_telegram_message(msg)
    print("Sent to Telegram")
else:
    print("No matches for any blueprint")
