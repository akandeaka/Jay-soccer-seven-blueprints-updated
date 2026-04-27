"""
Jay Soccer Blueprints - Manual Data Processor
Reads matches_today.csv with columns: League,Home Team,Away Team,Home Odds,Draw Odds,Away Odds
"""

import os
import csv
import json
from datetime import datetime
from typing import List
from jay_soccer_blueprints import JaySoccerBlueprints, Match, BlueprintResult


class GitHubDataProcessor:
    def __init__(self, input_file: str = "input/matches_today.csv", output_dir: str = "output"):
        self.input_file = input_file
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def read_matches_from_csv(self) -> List[Match]:
        """Read matches from CSV with columns: League,Home Team,Away Team,Home Odds,Draw Odds,Away Odds"""
        if not os.path.exists(self.input_file):
            print(f"\n❌ No input file found at: {self.input_file}")
            return []

        matches = []
        today = datetime.now().strftime("%Y-%m-%d")
        line_count = 0

        with open(self.input_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
            reader = csv.DictReader(f)
            # Print the actual column names for debugging
            print(f"CSV columns found: {reader.fieldnames}")

            for row in reader:
                line_count += 1
                try:
                    league = row.get('League', '').strip()
                    home_team = row.get('Home Team', '').strip()
                    away_team = row.get('Away Team', '').strip()
                    home_odds = float(row.get('Home Odds', 0))
                    draw_odds = float(row.get('Draw Odds', 0))
                    away_odds = float(row.get('Away Odds', 0))

                    # Skip rows with zero odds (invalid data)
                    if home_odds == 0 or draw_odds == 0 or away_odds == 0:
                        print(f"⚠️ Skipping row {line_count}: zero odds")
                        continue

                    match = Match(
                        league=league,
                        home_team=home_team,
                        away_team=away_team,
                        home_odds=home_odds,
                        draw_odds=draw_odds,
                        away_odds=away_odds,
                        time="TBD",
                        date=today
                    )
                    matches.append(match)
                except (ValueError, KeyError) as e:
                    print(f"⚠️ Error on line {line_count}: {e}")
                    continue

        print(f"\n📖 Read {len(matches)} valid matches from {self.input_file}")
        if matches:
            print("\n📋 First 3 matches:")
            for m in matches[:3]:
                print(f"   {m.home_team} vs {m.away_team} ({m.league}) - Odds: {m.home_odds}|{m.draw_odds}|{m.away_odds}")
        return matches

    def save_results(self, matches: List[Match], results: List[BlueprintResult]):
        today = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        blueprint_counts = {str(i): 0 for i in range(1, 8)}
        for res in results:
            blueprint_counts[str(res.blueprint_number)] += 1

        results_list = []
        for res in results:
            results_list.append({
                "blueprint_number": res.blueprint_number,
                "blueprint_name": res.blueprint_name,
                "target_market": res.target_market,
                "risk_level": res.risk_level,
                "match": {
                    "league": res.match.league,
                    "home_team": res.match.home_team,
                    "away_team": res.match.away_team,
                    "home_odds": res.match.home_odds,
                    "draw_odds": res.match.draw_odds,
                    "away_odds": res.match.away_odds,
                    "time": res.match.time,
                    "date": res.match.date
                },
                "reason": res.reason
            })

        full_data = {
            "timestamp": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {
                "total_matches": len(matches),
                "qualifying_matches": len(results),
                "blueprint_counts": blueprint_counts
            },
            "blueprints": results_list,
            "all_matches": [
                {
                    "league": m.league,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "home_odds": m.home_odds,
                    "draw_odds": m.draw_odds,
                    "away_odds": m.away_odds,
                    "time": m.time,
                    "date": m.date
                }
                for m in matches
            ]
        }

        json_path = os.path.join(self.output_dir, f"blueprint_results_{today}.json")
        with open(json_path, 'w') as f:
            json.dump(full_data, f, indent=2)
        print(f"✓ JSON saved: {json_path}")

        csv_path = os.path.join(self.output_dir, f"blueprint_results_{today}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Blueprint', 'League', 'Home', 'Away', 'Home Odds', 'Draw Odds', 'Away Odds', 'Play', 'Risk'])
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
        print(f"✓ CSV saved: {csv_path}")

    def print_summary(self, results: List[BlueprintResult]):
        if not results:
            print("\n" + "="*60)
            print("❌ NO MATCHES QUALIFY FOR ANY BLUEPRINT")
            print("="*60)
            return

        print("\n" + "="*70)
        print("⚽ JAY SOCCER BLUEPRINTS - RESULTS")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)

        bp_counts = {}
        for res in results:
            bp_counts[res.blueprint_number] = bp_counts.get(res.blueprint_number, 0) + 1

        print("\n📊 BLUEPRINT SUMMARY:")
        for bp in sorted(bp_counts.keys()):
            emoji = "🟢" if bp in [1,2] else "🟡" if bp in [3,4,5] else "🔴"
            print(f"   {emoji} Blueprint {bp}: {bp_counts[bp]} matches")

        print("\n" + "-"*70)
        print("🔍 QUALIFYING MATCHES:")
        for i, res in enumerate(results, 1):
            risk_emoji = "🟢" if "Low" in res.risk_level else "🟡" if "Moderate" in res.risk_level else "🔴"
            print(f"\n[{i}] {risk_emoji} BLUEPRINT {res.blueprint_number}: {res.blueprint_name}")
            print(f"    🏟️ {res.match.home_team} vs {res.match.away_team}")
            print(f"    🏆 {res.match.league}")
            print(f"    📊 Odds: {res.match.home_odds} | {res.match.draw_odds} | {res.match.away_odds}")
            print(f"    🎯 Play: {res.target_market}")
            print(f"    ⚠️ Risk: {res.risk_level}")
        print("="*70)


def run_github_processor():
    print("="*70)
    print("JAY SOCCER BLUEPRINTS - GITHUB MANUAL DATA PROCESSOR")
    print(f"Started: {datetime.now()}")
    print("="*70)

    processor = GitHubDataProcessor()
    matches = processor.read_matches_from_csv()

    if not matches:
        print("\n❌ No valid match data found in input/matches_today.csv")
        print("\n📋 Expected CSV format:")
        print("League,Home Team,Away Team,Home Odds,Draw Odds,Away Odds")
        return

    print(f"\n🔍 Running 7 Blueprints on {len(matches)} matches...")
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(matches)
    print(f"✓ Found {len(results)} qualifying matches")

    processor.save_results(matches, results)
    processor.print_summary(results)

    print(f"\n📁 Results saved in: {processor.output_dir}/")


if __name__ == "__main__":
    run_github_processor()
