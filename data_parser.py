"""
Data Parser - Parse matches from Soccer24 copy/paste
"""

import re
import pandas as pd
from typing import List, Dict


class Soccer24Parser:
    """Parse matches from copied text"""
    
    def parse_match_text(self, raw_text: str) -> List[Dict]:
        """Parse raw copied text into structured match data"""
        if not raw_text:
            return []
        
        matches = []
        lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            match_data = {}
            
            # Match name line (must contain 'vs')
            if ' vs ' not in lines[i]:
                i += 1
                continue
            
            match_data['match'] = lines[i]
            i += 1
            
            # League line
            if i < len(lines) and '|' not in lines[i] and ':' not in lines[i]:
                match_data['league'] = lines[i]
                i += 1
            else:
                match_data['league'] = 'Unknown'
            
            # Odds line (Home | Draw | Away)
            if i < len(lines) and '|' in lines[i]:
                odds = re.findall(r'(\d+\.\d+)', lines[i])
                if len(odds) >= 3:
                    match_data['home_odds'] = float(odds[0])
                    match_data['draw_odds'] = float(odds[1])
                    match_data['away_odds'] = float(odds[2])
                i += 1
            
            # Over/Under line (optional)
            if i < len(lines) and ('Over' in lines[i] or 'Under' in lines[i]):
                over_match = re.search(r'Over\s+\d+\.\d+:\s*(\d+\.\d+)', lines[i])
                under_match = re.search(r'Under\s+\d+\.\d+:\s*(\d+\.\d+)', lines[i])
                if over_match:
                    match_data['over_25_odds'] = float(over_match.group(1))
                if under_match:
                    match_data['under_25_odds'] = float(under_match.group(1))
                i += 1
            
            # BTTS line (optional)
            if i < len(lines) and 'BTTS' in lines[i]:
                btts_match = re.search(r'BTTS Yes:\s*(\d+\.\d+)', lines[i])
                if btts_match:
                    match_data['btts_yes_odds'] = float(btts_match.group(1))
                i += 1
            
            # Set defaults
            match_data.setdefault('over_25_odds', 0)
            match_data.setdefault('under_25_odds', 0)
            match_data.setdefault('btts_yes_odds', 0)
            
            matches.append(match_data)
        
        return matches
    
    def create_dataframe(self, matches: List[Dict]) -> pd.DataFrame:
        """Convert matches to DataFrame"""
        if not matches:
            return pd.DataFrame()
        
        df = pd.DataFrame(matches)
        numeric_cols = ['home_odds', 'draw_odds', 'away_odds', 'over_25_odds', 'under_25_odds', 'btts_yes_odds']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with missing essential odds
        df = df.dropna(subset=['home_odds', 'draw_odds', 'away_odds'])
        
        return df
