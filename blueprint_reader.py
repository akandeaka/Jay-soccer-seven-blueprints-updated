"""
Blueprint Data Reader - Reads data from your blueprint system
"""

import os
import json
import re
from datetime import datetime
from typing import Tuple, Optional, Dict, List


class BlueprintReader:
    """Reads blueprint data from various sources"""
    
    def __init__(self, config):
        self.config = config
    
    def read_from_file(self, filepath: str) -> Optional[str]:
        """Read blueprint output from a text file"""
        try:
            if not os.path.exists(filepath):
                print(f"⚠️ File not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✅ Read {len(content)} characters from {filepath}")
            return content
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None
    
    def read_from_csv(self, filepath: str) -> Optional[str]:
        """Convert CSV match data to blueprint format"""
        try:
            import pandas as pd
            
            if not os.path.exists(filepath):
                print(f"⚠️ CSV file not found: {filepath}")
                return None
            
            df = pd.read_csv(filepath)
            
            # Convert CSV to blueprint text format
            blueprint_text = self._convert_csv_to_blueprint(df)
            
            print(f"✅ Converted {len(df)} matches from CSV to blueprint format")
            return blueprint_text
            
        except ImportError:
            print("❌ pandas not installed. Install with: pip install pandas")
            return None
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return None
    
    def _convert_csv_to_blueprint(self, df) -> str:
        """Convert DataFrame to blueprint text format"""
        lines = []
        
        # Add header
        lines.append("📊 Summary:")
        lines.append(f"   Total qualifying matches: {len(df)}")
        lines.append("")
        
        # Convert each row
        for idx, row in df.iterrows():
            # Determine blueprint type based on odds or custom logic
            blueprint = self._determine_blueprint(row)
            
            # Get teams
            home_team = row.get('Home Team', row.get('home_team', 'Unknown'))
            away_team = row.get('Away Team', row.get('away_team', 'Unknown'))
            
            # Get odds
            home_odds = row.get('Home Odds', row.get('home_odds', '0'))
            draw_odds = row.get('Draw Odds', row.get('draw_odds', '0'))
            away_odds = row.get('Away Odds', row.get('away_odds', '0'))
            
            # Get league and play
            league = row.get('League', row.get('league', 'Unknown'))
            play = row.get('Play', row.get('play', 'Match'))
            risk = row.get('Risk', row.get('risk', 'Moderate'))
            
            # Build blueprint line
            lines.append(f"{blueprint} {idx+1}. {self._get_blueprint_name(blueprint)}")
            lines.append(f"   🏟️ {home_team} vs {away_team}")
            lines.append(f"   🏆 {league}")
            lines.append(f"   📊 Odds: {home_odds} | {draw_odds} | {away_odds}")
            lines.append(f"   🎯 Play: {play}")
            lines.append(f"   ⚠️ Risk: {risk}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _determine_blueprint(self, row) -> str:
        """Determine blueprint type from match data"""
        # You can customize this logic based on your blueprint system
        home_odds = float(row.get('Home Odds', row.get('home_odds', 2.0)))
        draw_odds = float(row.get('Draw Odds', row.get('draw_odds', 3.0)))
        away_odds = float(row.get('Away Odds', row.get('away_odds', 3.0)))
        
        if home_odds < 1.40:
            return "🟢 BP1"  # Elite Home Banker
        elif home_odds < 1.70:
            return "🟢 BP2"  # Primary Favorite
        elif home_odds < 2.00:
            return "🟡 BP3"  # Moderate Favorite
        elif draw_odds < 3.20:
            return "🔴 BP6"  # Strong Draw
        else:
            return "🟡 BP7"  # High Scoring Signals
    
    def _get_blueprint_name(self, blueprint_code: str) -> str:
        """Get full blueprint name"""
        names = {
            "🟢 BP1": "THE ELITE HOME BANKER",
            "🟢 BP2": "THE PRIMARY FAVORITE",
            "🟡 BP3": "THE MODERATE FAVORITE SAFETY",
            "🟡 BP4": "THE GOAL ENGINE",
            "🟡 BP5": "THE DEFENSIVE TRAP",
            "🔴 BP6": "THE STRONG DRAW",
            "🟡 BP7": "THE HIGH-SCORING SIGNALS"
        }
        return names.get(blueprint_code, "MATCH")
    
    def get_blueprint_data(self) -> Tuple[Optional[str], int]:
        """Get blueprint data from configured source"""
        
        # Try CSV file first
        if self.config.BLUEPRINT_CSV_FILE:
            content = self.read_from_csv(self.config.BLUEPRINT_CSV_FILE)
            if content:
                # Extract total matches count
                total = content.count("🏟️")
                return content, total
        
        # Try text file
        if self.config.BLUEPRINT_OUTPUT_FILE:
            content = self.read_from_file(self.config.BLUEPRINT_OUTPUT_FILE)
            if content:
                # Extract total from summary
                match = re.search(r'Total qualifying matches:\s*(\d+)', content)
                total = int(match.group(1)) if match else content.count("🏟️")
                return content, total
        
        # Try API
        if self.config.BLUEPRINT_API_URL:
            content = self._read_from_api()
            if content:
                total = content.count("🏟️")
                return content, total
        
        print("❌ No blueprint data source configured!")
        return None, 0
    
    def _read_from_api(self) -> Optional[str]:
        """Read from API endpoint"""
        try:
            import requests
            
            headers = {}
            if self.config.BLUEPRINT_API_KEY:
                headers['Authorization'] = f"Bearer {self.config.BLUEPRINT_API_KEY}"
            
            response = requests.get(
                self.config.BLUEPRINT_API_URL,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('blueprint_text', str(data))
            else:
                print(f"⚠️ API returned status {response.status_code}")
                return None
                
        except ImportError:
            print("❌ requests not installed")
            return None
        except Exception as e:
            print(f"❌ API error: {e}")
            return None
