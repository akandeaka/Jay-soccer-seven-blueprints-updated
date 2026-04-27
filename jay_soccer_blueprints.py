import csv
from datetime import datetime
from jay_soccer_blueprints import JaySoccerBlueprints, Match

def read_odds_csv(filename: str):
    """
    Reads your CSV format:
    League,Home Team,Away Team,Home Odds,Draw Odds,Away Odds
    """
    matches = []
    today = datetime.now().strftime("%Y-%m-%d")
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map columns to Match object fields
            match = Match(
                league=row['League'].strip(),
                home_team=row['Home Team'].strip(),
                away_team=row['Away Team'].strip(),
                home_odds=float(row['Home Odds']),
                draw_odds=float(row['Draw Odds']),
                away_odds=float(row['Away Odds']),
                time="TBD",      # default because CSV doesn't have time
                date=today
            )
            matches.append(match)
    return matches

def main():
    # Read your odds data
    matches = read_odds_csv("matches_today.csv")   # change filename if needed
    print(f"Loaded {len(matches)} matches.\n")

    # Run blueprints
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(matches)

    if not results:
        print("No matches qualify for any blueprint.")
        return

    # Print summary
    print("QUALIFYING MATCHES (by blueprint):")
    for res in results:
        print(f"\nBlueprint {res.blueprint_number}: {res.blueprint_name}")
        print(f"  {res.match.home_team} vs {res.match.away_team} ({res.match.league})")
        print(f"  Odds: {res.match.home_odds} / {res.match.draw_odds} / {res.match.away_odds}")
        print(f"  Play: {res.target_market} (Risk: {res.risk_level})")

    # Save to CSV for your records
    with open("blueprint_output.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Blueprint", "League", "Home", "Away", "Home Odds", "Draw Odds", "Away Odds", "Play", "Risk"])
        for res in results:
            writer.writerow([
                res.blueprint_number,
                res.match.league,
                res.match.home_team,
                res.match.away_team,
                res.match.home_odds,
                res.match.draw_odds,
                res.match.away_odds,
                res.target_market,
                res.risk_level
            ])

if __name__ == "__main__":
    main()
