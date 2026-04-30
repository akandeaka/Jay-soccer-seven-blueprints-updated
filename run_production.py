import pandas as pd
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

df = pd.read_csv("matches_today.csv")

# Your exact column names
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = df['Odds Home'].astype(float)
df['Odds Draw'] = df['Odds Draw'].astype(float)
df['Odds Away'] = df['Odds Away'].astype(float)

matches = []
for _, r in df.iterrows():
    h, d, a = r['Odds Home'], r['Odds Draw'], r['Odds Away']
    if 1.20 <= h <= 1.29 and a >= 10:
        matches.append(('BP1', 'Straight Home Win', 'Ultra-Low', 95, r))
    elif 1.30 <= h <= 1.36 and a >= 9:
        matches.append(('BP2', 'Home Win', 'Low', 90, r))
    elif 1.72 <= h <= 1.80:
        matches.append(('BP4', 'Over 1.5 Goals', 'Moderate', 75, r))
    elif 2.75 <= d <= 3.39:
        matches.append(('BP6', 'Full Time Draw', 'High', 50, r))

if not matches:
    print("No matches")
    sys.exit(1)

matches.sort(key=lambda x: x[3], reverse=True)
top5 = matches[:5]

msg = f"RESULTS {datetime.now()}\n"
for i, m in enumerate(top5, 1):
    bp, play, risk, conf, r = m
    msg += f"\n{i}. {bp}: {r['Home Team']} vs {r['Away Team']}\n"
    msg += f"   {r['Competition']}\n"
    msg += f"   Odds: {r['Odds Home']}|{r['Odds Draw']}|{r['Odds Away']}\n"
    msg += f"   Play: {play}\n"

telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)
telegram.send_telegram_message(msg)
