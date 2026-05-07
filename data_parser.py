"""
Data Parser - Parse matches from Soccer24 copy/paste ONLY
NO DEMO DATA - Returns empty if no valid input
"""

import re
import pandas as pd
from typing import List, Dict


class Soccer24Parser:
    """Parse matches from Soccer24 copy/paste - NO DEMOS"""
    
    def parse_match_text(self, raw_text: str) -> List[Dict]:
        """
        Parse raw copied text from Soccer24
        Returns EMPTY list if format is invalid
        """
        if not raw_text or len(raw_text.strip()) < 50:
            print("❌ Input text is empty or too short")
            return []
        
        matches = []
        lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            match_data = {}
            
            # Must have 'vs' in the match name
            if ' vs ' not in lines[i]:
                i += 1
                continue
            
            match_data['match'] = lines[i]
            i += 1
            
            # Get league (must be next line and not contain odds)
            if i < len(lines) and '|' not in lines[i] and ':' not in lines[i]:
                match_data['league'] = lines[i]
                i += 1
            else:
                match_data['league'] = 'Unknown'
            
            # Get odds (must contain | symbol)
            if i < len(lines) and '|' in lines[i]:
                odds = re.findall(r'(\d+\.\d+)', lines[i])
                if len(odds) >= 3:
                    match_data['home_odds'] = float(odds[0])
                    match_data['draw_odds'] = float(odds[1])
                    match_data['away_odds'] = float(odds[2])
                else:
                    # Invalid odds format - skip this match
                    i += 1
                    continue
                i += 1
            else:
                # No odds found - skip this match
                continue
            
            # Get Over/Under odds
            if i < len(lines) and ('Over' in lines[i] or 'Under' in lines[i]):
                over_match = re.search(r'Over\s+\d+\.\d+:\s*(\d+\.\d+)', lines[i])
                under_match = re.search(r'Under\s+\d+\.\d+:\s*(\d+\.\d+)', lines[i])
                if over_match:
                    match_data['over_25_odds'] = float(over_match.group(1))
                if under_match:
                    match_data['under_25_odds'] = float(under_match.group(1))
                i += 1
            else:
                match_data['over_25_odds'] = 0
                match_data['under_25_odds'] = 0
            
            # Get BTTS odds
            if i < len(lines) and 'BTTS' in lines[i]:
                btts_match = re.search(r'BTTS Yes:\s*(\d+\.\d+)', lines[i])
                if btts_match:
                    match_data['btts_yes_odds'] = float(btts_match.group(1))
                i += 1
            else:
                match_data['btts_yes_odds'] = 0
            
            # Set defaults for missing values
            match_data.setdefault('over_25_odds', 0)
            match_data.setdefault('under_25_odds', 0)
            match_data.setdefault('btts_yes_odds', 0)
            
            matches.append(match_data)
        
        # Validate we got real matches
        if not matches:
            print("❌ No valid matches found in input file")
            print("   Expected format:")
            print("   Manchester United vs Liverpool")
            print("   Premier League")
            print("   2.10 | 3.40 | 3.30")
            print("   Over 2.5: 1.75 | Under 2.5: 2.05")
            print("   BTTS Yes: 1.65 | BTTS No: 2.15")
        
        return matches
    
    def create_dataframe(self, matches: List[Dict]) -> pd.DataFrame:
        """Convert matches list to DataFrame"""
        if not matches:
            return pd.DataFrame()
        
        df = pd.DataFrame(matches)
        
        # Ensure numeric columns
        numeric_cols = ['home_odds', 'draw_odds', 'away_odds', 'over_25_odds', 'under_25_odds', 'btts_yes_odds']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with missing odds
        df = df.dropna(subset=['home_odds', 'draw_odds', 'away_odds'])
        
        return df
