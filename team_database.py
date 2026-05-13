# team_database.py - Query local GitHub data (UPDATED)
import pandas as pd
import os

class TeamDatabase:
    """Query team form, league strength, head-to-head from local data"""
    
    def __init__(self, data_path="football_data", csv_file="matches.csv"):
        self.data_path = data_path
        self.csv_file = csv_file
        self.matches_df = None
        self.load_data()
    
    def load_data(self):
        """Load match data from CSV file"""
        # First try the converted CSV
        if os.path.exists(self.csv_file):
            self.matches_df = pd.read_csv(self.csv_file)
            print(f"✅ Loaded {len(self.matches_df)} historical matches from {self.csv_file}")
            return
        
        # If CSV doesn't exist, try to read from openfootball format
        if os.path.exists(self.data_path):
            print(f"⚠️ CSV not found. Run convert_football_data.py first")
            print(f"   Or use: git clone https://github.com/openfootball/europe.git")
        else:
            print(f"⚠️ No data found. Run:")
            print(f"   git clone https://github.com/openfootball/europe.git {self.data_path}")
    
    def get_team_form(self, team_name, last_n=5):
        """Get team's last N results"""
        if self.matches_df is None or self.matches_df.empty:
            return None
        
        # Find matches involving the team
        team_matches = self.matches_df[
            (self.matches_df['home_team'].str.contains(team_name, case=False, na=False)) |
            (self.matches_df['away_team'].str.contains(team_name, case=False, na=False))
        ].tail(last_n)
        
        if len(team_matches) == 0:
            return None
        
        # Calculate form (win/draw/loss)
        form = []
        for _, match in team_matches.iterrows():
            if match['home_team'].lower() == team_name.lower():
                if match['home_score'] > match['away_score']:
                    form.append('W')
                elif match['home_score'] == match['away_score']:
                    form.append('D')
                else:
                    form.append('L')
            else:
                if match['away_score'] > match['home_score']:
                    form.append('W')
                elif match['away_score'] == match['home_score']:
                    form.append('D')
                else:
                    form.append('L')
        
        return form
    
    def get_form_score(self, team_name, last_n=5):
        """Get numeric form score (0-1)"""
        form = self.get_team_form(team_name, last_n)
        if not form:
            return 0.5  # Neutral if no data
        
        # Convert W=1, D=0.5, L=0
        score = sum(1.0 if r == 'W' else 0.5 if r == 'D' else 0.0 for r in form) / len(form)
        return round(score, 2)
    
    def get_head_to_head(self, home_team, away_team):
        """Get head-to-head record between two teams"""
        if self.matches_df is None or self.matches_df.empty:
            return None
        
        h2h = self.matches_df[
            ((self.matches_df['home_team'].str.contains(home_team, case=False, na=False)) &
             (self.matches_df['away_team'].str.contains(away_team, case=False, na=False))) |
            ((self.matches_df['home_team'].str.contains(away_team, case=False, na=False)) &
             (self.matches_df['away_team'].str.contains(home_team, case=False, na=False)))
        ]
        
        if len(h2h) == 0:
            return None
        
        home_wins = 0
        away_wins = 0
        draws = 0
        
        for _, match in h2h.iterrows():
            if match['home_team'].lower() == home_team.lower():
                if match['home_score'] > match['away_score']:
                    home_wins += 1
                elif match['home_score'] < match['away_score']:
                    away_wins += 1
                else:
                    draws += 1
            else:
                if match['away_score'] > match['home_score']:
                    home_wins += 1
                elif match['away_score'] < match['home_score']:
                    away_wins += 1
                else:
                    draws += 1
        
        return {
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'total': len(h2h)
        }
    
    def get_league_quality(self, league_name):
        """Get league strength score"""
        league_quality = {
            'premier league': 1.0,
            'bundesliga': 1.0,
            'la liga': 1.0,
            'serie a': 1.0,
            'ligue 1': 1.0,
            'championship': 0.8,
            'eredivisie': 0.8,
            'primeira liga': 0.8,
            'argentina': 0.6,
            'brasil': 0.6,
            'brazil': 0.6,
            'ligue 2': 0.5,
            'serie b': 0.4,
            '2. bundesliga': 0.4,
        }
        
        for key, score in league_quality.items():
            if key in league_name.lower():
                return score
        return 0.4  # Default for unknown leagues


# Test the database
if __name__ == "__main__":
    db = TeamDatabase()
    
    if db.matches_df is not None:
        print("\n📊 Testing TeamDatabase:")
        
        # Test team form
        form = db.get_team_form("Arsenal", 5)
        print(f"   Arsenal last 5 form: {form}")
        
        # Test form score
        score = db.get_form_score("Arsenal", 5)
        print(f"   Arsenal form score: {score}")
        
        # Test H2H
        h2h = db.get_head_to_head("Arsenal", "Chelsea")
        if h2h:
            print(f"   Arsenal vs Chelsea H2H: {h2h}")
        
        # Test league quality
        quality = db.get_league_quality("Premier League")
        print(f"   Premier League quality: {quality}")
