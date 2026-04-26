"""
Jay Soccer Blueprints - GitHub Manual Data Processor
Reads matches_today.csv directly from the repository
No API needed - you paste data manually into GitHub
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict
from jay_soccer_blueprints import JaySoccerBlueprints, Match, BlueprintResult


class GitHubDataProcessor:
    """
    Processes match data from CSV file stored in the GitHub repository
    You update input/matches_today.csv directly on GitHub
    """
    
    def __init__(self, input_file: str = "input/matches_today.csv", output_dir: str = "output"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.create_output_folder()
    
    def create_output_folder(self):
        """Create output folder if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_matches_from_csv(self) -> List[Match]:
        """
        Read matches from CSV file in the repository
        File location: input/matches_today.csv
        
        Expected CSV format:
        league,home_team,away_team,home_odds,draw_odds,away_odds,time,date
        """
        if not os.path.exists(self.input_file):
            print(f"\n❌ No input file found at: {self.input_file}")
            print("\n📋 Please create this file in your repository with the following format:")
            print("-"*70)
            print("league,home_team,away_team,home_odds,draw_odds,away_odds,time,date")
            print("Premier League,Manchester City,Southampton,1.25,5.50,11.00,15:00,2026-04-26")
            print("-"*70)
            return []
        
        matches = []
        today = datetime.now().strftime("%Y-%m-%d")
        line_count = 0
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                line_count += 1
                try:
                    # Handle potential BOM characters in CSV
                    league = row.get('league', '').strip()
                    if league.startswith('\ufeff'):
                        league = league[1:]
                    
                    match = Match(
                        league=league,
                        home_team=row.get('home_team', 'Unknown').strip(),
                        away_team=row.get('away_team', 'Unknown').strip(),
                        home_odds=float(row.get('home_odds', 0)),
                        draw_odds=float(row.get('draw_odds', 0)),
                        away_odds=float(row.get('away_odds', 0)),
                        time=row.get('time', '').strip(),
                        date=row.get('date', today).strip()
                    )
                    matches.append(match)
                except (ValueError, KeyError) as e:
                    print(f"⚠️ Error on line {line_count}: {e}")
                    print(f"   Row data: {row}")
                    continue
        
        print(f"\n📖 Read {len(matches)} matches from {self.input_file}")
        
        # Show preview
        if matches:
            print("\n📋 First 3 matches:")
            for m in matches[:3]:
                print(f"   {m.home_team} vs {m.away_team} ({m.league}) - Odds: {m.home_odds}|{m.draw_odds}|{m.away_odds}")
        
        return matches
    
    def save_results(self, matches: List[Match], results: List[BlueprintResult]):
        """Save blueprint results to output folder"""
        
        today = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data
        blueprint_counts = {str(i): 0 for i in range(1, 8)}
        for res in results:
            blueprint_counts[str(res.blueprint_number)] += 1
        
        # Prepare results list
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
        
        # Group by blueprint
        blueprints_by_number = {}
        for bp_num in range(1, 8):
            bp_results = [r for r in results_list if r["blueprint_number"] == bp_num]
            if bp_results:
                blueprints_by_number[str(bp_num)] = bp_results
        
        full_data = {
            "timestamp": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {
                "total_matches": len(matches),
                "qualifying_matches": len(results),
                "blueprint_counts": blueprint_counts
            },
            "blueprints": results_list,
            "blueprints_by_number": blueprints_by_number,
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
        
        # Save JSON
        json_path = os.path.join(self.output_dir, f"blueprint_results_{today}.json")
        with open(json_path, 'w') as f:
            json.dump(full_data, f, indent=2)
        print(f"✓ JSON saved: {json_path}")
        
        # Save CSV
        csv_path = os.path.join(self.output_dir, f"blueprint_results_{today}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Blueprint', 'Name', 'League', 'Home', 'Away', 
                           'Home Odds', 'Draw Odds', 'Away Odds', 'Target Market', 'Risk', 'Time', 'Date'])
            for res in results:
                m = res.match
                writer.writerow([
                    res.blueprint_number,
                    res.blueprint_name,
                    m.league,
                    m.home_team,
                    m.away_team,
                    m.home_odds,
                    m.draw_odds,
                    m.away_odds,
                    res.target_market,
                    res.risk_level,
                    m.time,
                    m.date
                ])
        print(f"✓ CSV saved: {csv_path}")
        
        # Save summary
        summary_path = os.path.join(self.output_dir, f"summary_{today}.json")
        with open(summary_path, 'w') as f:
            json.dump(full_data["summary"], f, indent=2)
        print(f"✓ Summary saved: {summary_path}")
        
        return full_data
    
    def print_summary(self, results: List[BlueprintResult]):
        """Print a readable summary to console (for GitHub Actions log)"""
        
        if not results:
            print("\n" + "="*60)
            print("❌ NO MATCHES QUALIFY FOR ANY BLUEPRINT")
            print("="*60)
            return
        
        print("\n" + "="*70)
        print("⚽ JAY SOCCER BLUEPRINTS - RESULTS")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)
        
        # Summary by blueprint
        blueprint_counts = {}
        for res in results:
            bp = res.blueprint_number
            blueprint_counts[bp] = blueprint_counts.get(bp, 0) + 1
        
        print("\n📊 BLUEPRINT SUMMARY:")
        for bp in sorted(blueprint_counts.keys()):
            count = blueprint_counts[bp]
            if bp in [1,2]:
                emoji = "🟢"
            elif bp in [3,4,5]:
                emoji = "🟡"
            else:
                emoji = "🔴"
            print(f"   {emoji} Blueprint {bp}: {count} matches")
        
        print("\n" + "-"*70)
        print("🔍 QUALIFYING MATCHES:")
        print("-"*70)
        
        for i, res in enumerate(results, 1):
            risk_emoji = "🟢" if "Low" in res.risk_level else "🟡" if "Moderate" in res.risk_level else "🔴"
            print(f"\n[{i}] {risk_emoji} BLUEPRINT {res.blueprint_number}: {res.blueprint_name}")
            print(f"    🏟️  {res.match.home_team} vs {res.match.away_team}")
            print(f"    🏆 {res.match.league}")
            print(f"    📊 Odds: {res.match.home_odds} | {res.match.draw_odds} | {res.match.away_odds}")
            print(f"    🎯 Play: {res.target_market}")
            print(f"    ⚠️ Risk: {res.risk_level}")
        
        print("\n" + "="*70)


def run_github_processor():
    """Main function to run the processor on GitHub"""
    
    print("="*70)
    print("JAY SOCCER BLUEPRINTS - GITHUB MANUAL DATA PROCESSOR")
    print(f"Started: {datetime.now()}")
    print("="*70)
    
    # Read matches from CSV in repository
    processor = GitHubDataProcessor()
    matches = processor.read_matches_from_csv()
    
    if not matches:
        print("\n❌ No match data found in input/matches_today.csv")
        print("\n📋 Please update the CSV file with today's matches:")
        print("   1. Go to your repository on GitHub")
        print("   2. Navigate to input/matches_today.csv")
        print("   3. Click Edit (pencil icon)")
        print("   4. Paste today's match data using the format below")
        print("   5. Commit changes")
        print("\n📝 CORRECT CSV FORMAT (copy this exactly):")
        print("-"*70)
        print("league,home_team,away_team,home_odds,draw_odds,away_odds,time,date")
        print("Premier League,Manchester City,Southampton,1.25,5.50,11.00,15:00,2026-04-26")
        print("LaLiga,Real Madrid,Getafe,1.33,5.00,9.50,17:30,2026-04-26")
        print("-"*70)
        return
    
    # Run blueprints
    print("\n🔍 Running 7 Blueprints on pasted data...")
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(matches)
    print(f"✓ Found {len(results)} qualifying matches")
    
    # Save results
    processor.save_results(matches, results)
    
    # Print summary
    processor.print_summary(results)
    
    print(f"\n📁 Results saved in: {processor.output_dir}/")
    print("   Download from GitHub Actions Artifacts")


if __name__ == "__main__":
    run_github_processor()
