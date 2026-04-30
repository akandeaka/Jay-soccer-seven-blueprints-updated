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
print(f"Loaded {len(df)} rows")
print(f"Columns found: {list(df.columns)}")

# AUTO-DETECT column names
home_odds_col = None
draw_odds_col = None
away_odds_col = None
home_team_col = None
away_team_col = None
league_col = None

for col in df.columns:
    col_lower = col.lower()
    if 'home' in col_lower and 'odds' in col_lower:
        home_odds_col = col
    elif 'draw' in col_lower and 'odds' in col_lower:
        draw_odds_col = col
    elif 'away' in col_lower and 'odds' in col_lower:
        away_odds_col = col
    elif 'home' in col_lower and 'team' in col_lower:
        home_team_col = col
    elif 'away' in col_lower and 'team' in col_lower:
        away_team_col = col
    elif 'league' in col_lower or 'competition' in col_lower:
        league_col = col

print(f"Detected: Home Odds='{home_odds_col}', Draw Odds='{draw_odds_col}', Away Odds='{away_odds_col}'")

if not all([home_odds_col, draw_odds_col, away_odds_col]):
    print("ERROR: Could not find odds columns!")
    print("Available columns:", list(df.columns))
    sys.exit(1)

# Filter valid odds
df = df[df[home_odds_col] != '-']
df = df[df[draw_odds_col] != '-']
df = df[df[away_odds_col] != '-']

df[home_odds_col] = pd.to_numeric(df[home_odds_col])
df[draw_odds_col] = pd.to_numeric(df[draw_odds_col])
df[away_odds_col] = pd.to_numeric(df[away_odds_col])
df = df.dropna()

print(f"Matches with valid odds: {len(df)}")

if len(df) == 0:
    print("No valid matches")
    sys.exit(1)

# Your 7 Blueprints
matches = []
for _, row in df.iterrows():
    h = row[home_odds_col]
    d = row[draw_odds_col]
    a = row[away_odds_col]
    
    if 1.20 <= h <= 1.29 and a >= 10.0:
        matches.append(('BP1', 'THE ELITE HOME BANKER', 'Straight Home Win', 'Ultra-Low', 95, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        matches.append(('BP2', 'THE PRIMARY FAVORITE', 'Home Win', 'Low', 90, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        matches.append(('BP3', 'THE MODERATE FAVORITE SAFETY', '1X & Over 1.5 Goals', 'Low-Moderate', 85, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 1.72 <= h <= 1.80:
        matches.append(('BP4', 'THE GOAL ENGINE', 'Over 1.5 Goals', 'Moderate', 75, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 1.90 <= h <= 2.02:
        matches.append(('BP5', 'THE DEFENSIVE TRAP', '1X & Under 3.5 FT', 'Moderate', 70, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 2.75 <= d <= 3.39:
        matches.append(('BP6', 'THE STRONG DRAW', 'Full Time Draw', 'High', 50, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 3.40 <= d <= 3.56:
        matches.append(('BP7', 'HIGH-SCORING SIGNALS', 'GG / Over 2.5', 'Moderate-High', 60, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))
    elif 3.60 <= d <= 3.75:
        matches.append(('BP7', 'HIGH-SCORING SIGNALS', 'HT 0.5 / Over 2.5', 'Moderate-High', 60, row, home_team_col, away_team_col, league_col, home_odds_col, draw_odds_col, away_odds_col))

print(f"Qualified: {len(matches)}")

if len(matches) == 0:
    print("No matches qualified")
    sys.exit(1)

# Top 20
matches.sort(key=lambda x: x[4], reverse=True)
top20 = matches[:20]

# Build message
msg = f"⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total: {len(df)} | Qualified: {len(matches)} | TOP {len(top20)}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

for i, m in enumerate(top20, 1):
    bp, name, play, risk, conf, row, ht_col, at_col, lg_col, h_odds_col, d_odds_col, a_odds_col = m
    tier = "🔥 GOLD" if conf >= 85 else "✅ SILVER" if conf >= 70 else "⚠️ BRONZE"
    msg += f"\n{i}. {tier} {bp}: {name}\n"
    msg += f"   🏟️ {row[ht_col]} vs {row[at_col]}\n"
    msg += f"   🏆 {row[lg_col] if lg_col else 'Unknown'}\n"
    msg += f"   📊 {row[h_odds_col]} | {row[d_odds_col]} | {row[a_odds_col]}\n"
    msg += f"   🎯 {play}\n"
    msg += f"   ⚠️ {risk}\n"
    msg += f"   📈 Confidence: {conf}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# Send
telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
    print("Sent in 2 parts")
else:
    telegram.send_telegram_message(msg)
    print("Sent successfully")

print("Done")
