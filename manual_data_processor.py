"""
Jay Soccer Blueprints - Manual Data Processor
Reads match data from CSV/Excel files that you paste into the input folder
You simply copy odds from Bet365/Soccer24 and paste into matches_today.csv
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict
from jay_soccer_blueprints import JaySoccerBlueprints, Match, BlueprintResult


class ManualDataProcessor:
    """
    Processes match data from manually pasted CSV files
    You provide the data, the system analyzes it
    """
    
    def __init__(self, input_dir: str = "./input", output_dir: str = "./output"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.create_folders()
    
    def create_folders(self):
        """Create input and output folders if they don't exist"""
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_matches_from_csv(self, filename: str = "matches_today.csv") -> List[Match]:
        """
        Read matches from CSV file you pasted into input folder
        
        Expected CSV format (with headers):
        league,home_team,away_team,home_odds,draw_odds,away_odds,time
        Premier League,Manchester City,Southampton,1.25,5.50,11.00,15:00
        La Liga,Real Madrid,Getafe,1.33,5.00,9.50,17:30
        """
        filepath = os.path.join(self.input_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"\n❌ No input file found at: {filepath}")
            print("\n📋 Please create the file with this format:")
            print("-"*60)
            print("league,home_team,away_team,home_odds,draw_odds,away_odds,time,date")
            print("Premier League,Manchester City,Southampton,1.25,5.50,11.00,15:00,2026-04-26")
            print("La Liga,Real Madrid,Getafe,1.33,5.00,9.50,17:30,2026-04-26")
            print("-"*60)
            return []
        
        matches = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    match = Match(
                        league=row.get('league', 'Unknown'),
                        home_team=row.get('home_team', 'Unknown'),
                        away_team=row.get('away_team', 'Unknown'),
                        home_odds=float(row.get('home_odds', 0)),
                        draw_odds=float(row.get('draw_odds', 0)),
                        away_odds=float(row.get('away_odds', 0)),
                        time=row.get('time', ''),
                        date=row.get('date', today)
                    )
                    matches.append(match)
                except (ValueError, KeyError) as e:
                    print(f"⚠️ Skipping row: {row} - Error: {e}")
        
        print(f"\n✓ Read {len(matches)} matches from {filename}")
        return matches
    
    def read_matches_from_text(self, filename: str = "matches_today.txt") -> List[Match]:
        """
        Read matches from simple text format (easier to copy/paste)
        
        Format (tab-separated or space-separated):
        League | Home Team | Away Team | Home Odds | Draw Odds | Away Odds | Time
        """
        filepath = os.path.join(self.input_dir, filename)
        
        if not os.path.exists(filepath):
            return []
        
        matches = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 7:
                        try:
                            match = Match(
                                league=parts[0].strip(),
                                home_team=parts[1].strip(),
                                away_team=parts[2].strip(),
                                home_odds=float(parts[3].strip()),
                                draw_odds=float(parts[4].strip()),
                                away_odds=float(parts[5].strip()),
                                time=parts[6].strip(),
                                date=today
                            )
                            matches.append(match)
                        except ValueError:
                            continue
        
        print(f"\n✓ Read {len(matches)} matches from {filename}")
        return matches
    
    def save_results(self, matches: List[Match], results: List[BlueprintResult]):
        """Save blueprint results to output folder"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        today = datetime.now().strftime("%Y%m%d")
        
        # Prepare data
        data = self.format_output_data(matches, results)
        
        # Save JSON
        json_path = os.path.join(self.output_dir, f"blueprint_results_{today}.json")
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ JSON saved: {json_path}")
        
        # Save CSV (for Excel)
        csv_path = os.path.join(self.output_dir, f"blueprint_results_{today}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Blueprint', 'Name', 'League', 'Home', 'Away', 
                           'Home Odds', 'Draw Odds', 'Away Odds', 'Target Market', 'Risk', 'Time'])
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
                    m.time
                ])
        print(f"✓ CSV saved: {csv_path}")
        
        # Save summary
        summary_path = os.path.join(self.output_dir, f"summary_{today}.json")
        with open(summary_path, 'w') as f:
            json.dump(data['summary'], f, indent=2)
        print(f"✓ Summary saved: {summary_path}")
        
        return data
    
    def format_output_data(self, matches: List[Match], results: List[BlueprintResult]) -> Dict:
        """Format data for JSON output"""
        
        # Count blueprints
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
        
        return {
            "timestamp": datetime.now().isoformat(),
            "date": today,
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
                    "time": m.time
                }
                for m in matches
            ]
        }
    
    def print_summary(self, results: List[BlueprintResult]):
        """Print a readable summary to console"""
        
        if not results:
            print("\n" + "="*60)
            print("❌ NO MATCHES QUALIFY FOR ANY BLUEPRINT")
            print("="*60)
            return
        
        print("\n" + "="*80)
        print("⚽ JAY SOCCER BLUEPRINTS - RESULTS")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80)
        
        # Summary by blueprint
        blueprint_counts = {}
        for res in results:
            bp = res.blueprint_number
            blueprint_counts[bp] = blueprint_counts.get(bp, 0) + 1
        
        print("\n📊 BLUEPRINT SUMMARY:")
        for bp in sorted(blueprint_counts.keys()):
            count = blueprint_counts[bp]
            emoji = "🟢" if bp in [1,2] else "🟡" if bp in [3,4,5] else "🔴"
            print(f"   {emoji} Blueprint {bp}: {count} matches")
        
        print("\n" + "-"*80)
        print("🔍 DETAILED MATCHES:")
        print("-"*80)
        
        for i, res in enumerate(results, 1):
            risk_emoji = "🟢" if "Low" in res.risk_level else "🟡" if "Moderate" in res.risk_level else "🔴"
            print(f"\n[{i}] {risk_emoji} BLUEPRINT {res.blueprint_number}: {res.blueprint_name}")
            print(f"    🏟️  {res.match.home_team} vs {res.match.away_team}")
            print(f"    🏆 {res.match.league}")
            print(f"    📊 Odds: {res.match.home_odds} | {res.match.draw_odds} | {res.match.away_odds}")
            print(f"    🎯 Play: {res.target_market}")
            print(f"    ⚠️ Risk: {res.risk_level}")
            print(f"    📝 Reason: {res.reason}")
        
        print("\n" + "="*80)


def run_manual_processor():
    """Main function to run the manual data processor"""
    
    print("="*60)
    print("JAY SOCCER BLUEPRINTS - MANUAL DATA PROCESSOR")
    print("="*60)
    
    processor = ManualDataProcessor()
    
    # Try to read matches from CSV first, then TXT
    matches = processor.read_matches_from_csv("matches_today.csv")
    
    if not matches:
        matches = processor.read_matches_from_text("matches_today.txt")
    
    if not matches:
        print("\n❌ No match data found!")
        print("\n📋 Please create a file in the 'input' folder:")
        print("   - input/matches_today.csv (CSV format)")
        print("   - OR input/matches_today.txt (text format)")
        print("\n📝 CSV Example:")
        print("   league,home_team,away_team,home_odds,draw_odds,away_odds,time")
        print("   Premier League,Manchester City,Southampton,1.25,5.50,11.00,15:00")
        return
    
    # Run blueprints
    print("\n🔍 Running 7 Blueprints on pasted data...")
    scanner = JaySoccerBlueprints()
    results = scanner.scan_matches(matches)
    
    # Save results
    processor.save_results(matches, results)
    
    # Print summary
    processor.print_summary(results)
    
    print(f"\n📁 Results saved in: {processor.output_dir}/")
    print("   - blueprint_results_YYYYMMDD.json")
    print("   - blueprint_results_YYYYMMDD.csv")
    print("   - summary_YYYYMMDD.json")


if __name__ == "__main__":
    run_manual_processor()
