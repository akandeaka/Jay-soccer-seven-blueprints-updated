"""
Data Parser - Parse matches from text OR CSV format
Supports: Manual copy/paste AND CSV files
"""

import re
import pandas as pd
from typing import List, Dict
import csv
import io


class Soccer24Parser:
    """Parse matches from text or CSV format"""
    
    def parse_match_text(self, raw_text: str) -> List[Dict]:
        """
        Parse raw copied text from Soccer24 into structured match data
        Format: 
            Manchester United vs Liverpool
            Premier League
            2.10 | 3.40 | 3.30
            Over 2.5: 1.75 | Under 2.5: 2.05
            BTTS Yes: 1.65 | BTTS No: 2.15
        """
        if not raw_text:
            return []
        
        # Check if input is CSV format
        if self._is_csv_format(raw_text):
            print("📊 Detected CSV format - parsing as CSV")
            return self._parse_csv_format(raw_text)
        
        # Otherwise parse as text format
        return self._parse_text_format(raw_text)
    
    def _is_csv_format(self, raw_text: str) -> bool:
        """Detect if input is CSV format"""
        first_line = raw_text.strip().split('\n')[0]
        # CSV has commas and typical header words
        if ',' in first_line and any(word in first_line.lower() for word in ['home', 'away', 'team', 'odds']):
            return True
        return False
    
    def _parse_csv_format(self, csv_content: str) -> List[Dict]:
        """Parse CSV format data"""
        matches = []
        
        # Use StringIO to read CSV from string
        csv_file = io.StringIO(csv_content)
        
        # Try to detect delimiter
        sample = csv_content[:500]
        if ';' in sample and ',' not in sample:
            delimiter = ';'
        else:
            delimiter = ','
        
        try:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            for row in reader:
                match_data = self._extract_from_csv_row(row)
                if match_data:
                    matches.append(match_data)
                    
        except Exception as e:
            print(f"⚠️ CSV parsing error: {e}")
            return []
        
        return matches
    
    def _extract_from_csv_row(self, row: Dict) -> Dict:
        """Extract match data from CSV row with flexible column names"""
        match_data = {}
        
        # Find team names (try different column name variations)
        home_col = self._find_column(row, ['Home Team', 'Home', 'HomeTeam', 'home_team', 'home'])
        away_col = self._find_column(row, ['Away Team', 'Away', 'AwayTeam', 'away_team', 'away'])
        
        if home_col and away_col:
            match_data['match'] = f"{row[home_col]} vs {row[away_col]}"
        else:
            return None
        
        # Find league
        league_col = self._find_column(row, ['League', 'Competition', 'league', 'competition', 'Comp'])
        match_data['league'] = row[league_col] if league_col else 'Unknown'
        
        # Find odds
        home_odds_col = self._find_column(row, ['Home Odds', 'HomeOdds', 'home_odds', 'OddH', 'Home Win'])
        draw_odds_col = self._find_column(row, ['Draw Odds', 'DrawOdds', 'draw_odds', 'OddD', 'Draw'])
        away_odds_col = self._find_column(row, ['Away Odds', 'AwayOdds', 'away_odds', 'OddA', 'Away Win'])
        
        match_data['home_odds'] = float(row[home_odds_col]) if home_odds_col and row[home_odds_col] else 0
        match_data['draw_odds'] = float(row[draw_odds_col]) if draw_odds_col and row[draw_odds_col] else 0
        match_data['away_odds'] = float(row[away_odds_col]) if away_odds_col and row[away_odds_col] else 0
        
        # Find Over/Under odds (optional)
        over_col = self._find_column(row, ['Over 2.5', 'Over2.5', 'over_25', 'O2.5'])
        under_col = self._find_column(row, ['Under 2.5', 'Under2.5', 'under_25', 'U2.5'])
        
        match_data['over_25_odds'] = float(row[over_col]) if over_col and row[over_col] else 0
        match_data['under_25_odds'] = float(row[under_col]) if under_col and row[under_col] else 0
        
        # Find BTTS odds (optional)
        btts_col = self._find_column(row, ['BTTS Yes', 'BTTS', 'btts_yes', 'GG'])
        match_data['btts_yes_odds'] = float(row[btts_col]) if btts_col and row[btts_col] else 0
        
        return match_data
    
    def _find_column(self, row: Dict, possible_names: List[str]) -> str:
        """Find which column name exists in the row"""
        for name in possible_names:
            if name in row:
                return name
        return None
    
    def _parse_text_format(self, raw_text: str) -> List[Dict]:
        """Parse the original text format"""
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
            
            # Odds line
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
        
        df = df.dropna(subset=['home_odds', 'draw_odds', 'away_odds'])
        
        return df
