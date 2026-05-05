import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 60)
print("📊 PRODUCTION SYSTEM - 25 MATCHES INCLUDING DRAWS")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Load the CSV file
df = pd.read_csv('matches_today (5).csv')

print(f"Loaded {len(df)} rows")

# === FIX: Clean odds columns before conversion ===
odds_columns = ['Odds Home', 'Odds Draw', 'Odds Away']

for col in odds_columns:
    # Replace any non-numeric placeholders with NaN
    df[col] = df[col].replace(['-', '', 'Scheduled', 'Finished', 'FRO', 'Awaiting', 'Half Time', 'Cancelled', 'Live'], np.nan)
    # Convert to numeric, any invalid becomes NaN
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Option 1: Keep only rows that have ALL three odds (for draw analysis)
df_clean = df.dropna(subset=odds_columns)

# Option 2: If you prefer to keep rows with at least one odd, use this instead:
# df_clean = df.dropna(subset=['Odds Home', 'Odds Draw', 'Odds Away'], how='all')

print(f"Rows with valid odds: {len(df_clean)}")
print(f"Rows removed (invalid odds): {len(df) - len(df_clean)}")

# Continue with the clean dataframe
df = df_clean

# Now these conversions will work safely
df['Odds Home'] = df['Odds Home'].astype(float)
df['Odds Draw'] = df['Odds Draw'].astype(float)
df['Odds Away'] = df['Odds Away'].astype(float)

# === Your existing analysis logic below ===
# Example: Find matches with high draw probability
df['Draw_Implied_Prob'] = 1 / df['Odds Draw']
df['Draw_Edge'] = df['Draw_Implied_Prob'] - (1/3)  # Compare to 33.3% baseline

# Top 10 matches most likely to end in a draw
top_draws = df.nlargest(10, 'Draw_Implied_Prob')[['Home Team', 'Away Team', 'Competition', 'Odds Draw', 'Draw_Implied_Prob']]

print("\n" + "=" * 60)
print("🎯 TOP 10 MATCHES MOST LIKELY TO END IN A DRAW")
print("=" * 60)
for idx, row in top_draws.iterrows():
    print(f"{row['Home Team']} vs {row['Away Team']}")
    print(f"  League: {row['Competition']} | Draw Odds: {row['Odds Draw']:.2f} ({row['Draw_Implied_Prob']:.1%})")
    print()

# Additional analysis: Draw odds range distribution
print("=" * 60)
print("📈 DRAW ODDS DISTRIBUTION")
print("=" * 60)
bins = [0, 2.5, 3.0, 3.5, 4.0, 5.0, float('inf')]
labels = ['<2.50', '2.50-2.99', '3.00-3.49', '3.50-3.99', '4.00-4.99', '5.00+']
df['Odds Draw Range'] = pd.cut(df['Odds Draw'], bins=bins, labels=labels)
range_counts = df['Odds Draw Range'].value_counts().sort_index()
for rng, count in range_counts.items():
    pct = count / len(df) * 100
    print(f"  {rng}: {count} matches ({pct:.1f}%)")

# Group by competition for draw rate analysis
print("\n" + "=" * 60)
print("🏆 DRAW ODDS BY COMPETITION (Top 10 by avg draw probability)")
print("=" * 60)
comp_stats = df.groupby('Competition').agg({
    'Odds Draw': 'mean',
    'Draw_Implied_Prob': 'mean'
}).round(3)
comp_stats.columns = ['Avg Draw Odds', 'Avg Draw Prob']
comp_stats = comp_stats.sort_values('Avg Draw Prob', ascending=False).head(10)

for comp, row in comp_stats.iterrows():
    print(f"  {comp}: {row['Avg Draw Odds']:.2f} ({row['Avg Draw Prob']:.1%})")

print("\n" + "=" * 60)
print("✅ Production run completed successfully")
print("=" * 60)
