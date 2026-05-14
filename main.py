"""
JAY SOCCER BLUEPRINTS - COMPLETE SYSTEM
8 Blueprints | Smart AI with Multiple Data Sources | GitHub Actions Ready
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from itertools import combinations
import pandas as pd
import glob

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
INPUT_FILE = "input_matches.txt"

# ============================================================
# MULTI-SOURCE DATABASE INTEGRATION
# ============================================================

class SmartAIDatabase:
    """
    Integrates multiple free data sources for deep analysis
    - football-data.co.uk (daily updated odds)
    - Club Football Match Data (475k matches)
    - FBref (xG, corners, shots via soccerdata)
    - OpenFootball Europe (standings, results)
    """
    
    def __init__(self):
        self.league_goals = {}
        self.team_form = {}
        self.team_xg = {}
        self.elo_ratings = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Load data from all available sources"""
        print("\n📊 Loading AI Data Sources...")
        
        # Source 1: football-data.co.uk (daily odds)
        self.load_football_data_co_uk()
        
        # Source 2: Club Football Match Data (475k matches)
        self.load_club_match_data()
        
        # Source 3: FBref via soccerdata (xG, corners)
        self.load_fbref_data()
        
        # Source 4: OpenFootball Europe
        self.load_openfootball_data()
        
        print("✅ AI Data Sources Loaded\n")
    
    def load_football_data_co_uk(self):
        """Load daily updated odds and results from football-data.co.uk"""
        try:
            # Check for data files in data directory
            if os.path.exists("data"):
                for file in glob.glob("data/*.csv"):
                    df = pd.read_csv(file)
                    # Extract league name from filename
                    league_name = os.path.basename(file).replace('.csv', '')
                    
                    # Calculate league goal average
                    if 'FTHG' in df.columns and 'FTAG' in df.columns:
                        total_goals = df['FTHG'] + df['FTAG']
                        avg_goals = total_goals.mean()
                        self.league_goals[league_name.lower()] = round(avg_goals, 1)
                        
                        # Extract team form from last matches
                        if 'HomeTeam' in df.columns:
                            for _, row in df.tail(100).iterrows():
                                home = row['HomeTeam']
                                away = row['AwayTeam']
                                home_goals = row['FTHG']
                                away_goals = row['FTAG']
                                
                                # Update team form
                                if home not in self.team_form:
                                    self.team_form[home] = {'goals_scored': [], 'goals_conceded': []}
                                if away not in self.team_form:
                                    self.team_form[away] = {'goals_scored': [], 'goals_conceded': []}
                                
                                self.team_form[home]['goals_scored'].append(home_goals)
                                self.team_form[home]['goals_conceded'].append(away_goals)
                                self.team_form[away]['goals_scored'].append(away_goals)
                                self.team_form[away]['goals_conceded'].append(home_goals)
            
            print(f"   ✅ football-data.co.uk: {len(self.league_goals)} leagues loaded")
        except Exception as e:
            print(f"   ⚠️ football-data.co.uk: {e}")
    
    def load_club_match_data(self):
        """Load 475k+ match dataset with Bet365 odds and form"""
        try:
            if os.path.exists("Club-Football-Match-Data-2000-2025/matches.csv"):
                df = pd.read_csv("Club-Football-Match-Data-2000-2025/matches.csv")
                
                # Extract league averages
                for league in df['League'].unique():
                    league_matches = df[df['League'] == league]
                    if 'FTGoals' in league_matches.columns:
                        avg = league_matches['FTGoals'].mean()
                        self.league_goals[league.lower()] = round(avg, 1)
                
                print(f"   ✅ Club Match Data: {len(df)} matches loaded")
            else:
                print("   ⚠️ Club Match Data not found - run: git clone https://github.com/xgabora/Club-Football-Match-Data-2000-2025.git")
        except Exception as e:
            print(f"   ⚠️ Club Match Data: {e}")
    
    def load_fbref_data(self):
        """Load advanced stats (xG, corners) from FBref via soccerdata"""
        try:
            from soccerdata import FBref
            
            # Get top 5 leagues data
            leagues = ["ENG-Premier League", "ESP-La Liga", "GER-Bundesliga", "ITA-Serie A", "FRA-Ligue 1"]
            
            for league in leagues:
                try:
                    fbref = FBref(leagues=league, seasons=2025)
                    stats = fbref.read_team_season_stats(stat_type='expected')
                    
                    for _, row in stats.iterrows():
                        team = row['team']
                        if team not in self.team_xg:
                            self.team_xg[team] = {}
                        self.team_xg[team]['xg_for'] = row.get('xg_for', 1.0)
                        self.team_xg[team]['xg_against'] = row.get('xg_against', 1.0)
                    
                    print(f"   ✅ FBref: {league} loaded")
                except:
                    pass
        except ImportError:
            print("   ⚠️ FBref not installed - run: pip install soccerdata")
        except Exception as e:
            print(f"   ⚠️ FBref: {e}")
    
    def load_openfootball_data(self):
        """Load OpenFootball Europe data for standings"""
        try:
            if os.path.exists("football_data"):
                print("   ✅ OpenFootball Europe data found")
            else:
                print("   ⚠️ OpenFootball not found - run: git clone https://github.com/openfootball/europe.git football_data")
        except Exception as e:
            print(f"   ⚠️ OpenFootball: {e}")
    
    def get_league_goals(self, league_name):
        """Get average goals for a league from loaded data"""
        league_lower = league_name.lower()
        for key, avg in self.league_goals.items():
            if key in league_lower or league_lower in key:
                return avg
        
        # Defaults based on league type (data-driven fallback)
        if any(x in league_lower for x in ['premier', 'epl']):
            return 2.8
        elif 'bundesliga' in league_lower:
            return 3.2
        elif 'serie a' in league_lower:
            return 2.6
        elif 'la liga' in league_lower:
            return 2.5
        elif 'ligue 1' in league_lower:
            return 2.7
        elif 'eredivisie' in league_lower:
            return 3.1
        else:
            return 2.5
    
    def get_team_attacking_score(self, team_name):
        """Calculate attacking score (0-1) from historical data"""
        if team_name in self.team_form:
            goals = self.team_form[team_name]['goals_scored']
            if goals:
                avg = sum(goals[-10:]) / min(len(goals), 10)
                return min(1.0, avg / 2.5)
        
        # Check xG data if available
        if team_name in self.team_xg:
            xg = self.team_xg[team_name].get('xg_for', 1.0)
            return min(1.0, xg / 2.5)
        
        # Default
        return 0.5
    
    def get_team_defensive_score(self, team_name):
        """Calculate defensive score (0-1) from historical data"""
        if team_name in self.team_form:
            conceded = self.team_form[team_name]['goals_conceded']
            if conceded:
                avg = sum(conceded[-10:]) / min(len(conceded), 10)
                return max(0, 1 - (avg / 2.0))
        
        # Check xG data if available
        if team_name in self.team_xg:
            xg_against = self.team_xg[team_name].get('xg_against', 1.0)
            return max(0, 1 - (xg_against / 2.0))
        
        return 0.5


# Initialize global AI database
ai_db = SmartAIDatabase()

# ============================================================
# BP6 DECISION MATRIX (DATA-DRIVEN)
# ============================================================

def determine_bp6_play(draw_odds, league, home_team, away_team):
    """
    BP6: Strong Draw - Uses AI database for decision
    Returns: (play, confidence)
    """
    
    if not (2.75 <= draw_odds <= 3.39):
        return None
    
    # Get data from AI database
    league_goals = ai_db.get_league_goals(league)
    home_attack = ai_db.get_team_attacking_score(home_team)
    away_attack = ai_db.get_team_attacking_score(away_team)
    avg_attack = (home_attack + away_attack) / 2
    
    # DECISION MATRIX
    if league_goals >= 3.0 or avg_attack >= 0.65:
        return ('Draw or GG (Draw OR Both Teams to Score)', 68)
    elif league_goals <= 2.3 or avg_attack <= 0.35:
        return ('Draw or Under 2.5 Goals', 72)
    else:
        return ('Full Time Draw', 55)


def determine_bp7_play(home_odds, league):
    """BP7: BTTS Value Spot - Uses league data"""
    if not (1.40 <= home_odds <= 1.69):
        return None
    
    league_goals = ai_db.get_league_goals(league)
    
    if league_goals >= 3.0:
        return ('Both Teams to Score - YES', 75)
    else:
        return ('Both Teams to Score - NO', 65)


def determine_bp8_play(draw_odds, league):
    """BP8: High-Scoring Signals - Uses league data"""
    if not (3.60 <= draw_odds <= 3.75):
        return None
    
    league_goals = ai_db.get_league_goals(league)
    
    if league_goals >= 2.7:
        return ('Over 2.5 Goals', 60)
    return None

# ============================================================
# PARSE INPUT FILE
# ============================================================

def parse_matches():
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ {INPUT_FILE} not found!")
        return []
    
    with open(INPUT_FILE, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return []
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    matches = []
    i = 0
    
    while i < len(lines):
        if ' vs ' not in lines[i]:
            i += 1
            continue
        
        match = {'match': lines[i]}
        teams = lines[i].split(' vs ')
        match['home_team'] = teams[0].strip()
        match['away_team'] = teams[1].strip() if len(teams) > 1 else ''
        i += 1
        
        if i < len(lines) and '|' not in lines[i]:
            match['league'] = lines[i]
            i += 1
        else:
            match['league'] = 'Unknown'
        
        if i < len(lines) and '|' in lines[i]:
            odds = re.findall(r'(\d+\.\d+)', lines[i])
            if len(odds) >= 3:
                match['home_odds'] = float(odds[0])
                match['draw_odds'] = float(odds[1])
                match['away_odds'] = float(odds[2])
            i += 1
        else:
            i += 1
            continue
        
        matches.append(match)
    
    return matches

# ============================================================
# 8 BLUEPRINTS WITH AI INTEGRATION
# ============================================================

def analyze_match(match):
    home = match.get('home_odds', 0)
    draw = match.get('draw_odds', 0)
    away = match.get('away_odds', 0)
    league = match.get('league', 'Unknown')
    home_team = match.get('home_team', '')
    away_team = match.get('away_team', '')
    
    # BP1: Elite Home Banker
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return {
            'blueprint': 'BP1', 'play': 'Straight Home Win',
            'confidence': 95, 'risk': 'Ultra-Low',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP2: Primary Favorite
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return {
            'blueprint': 'BP2', 'play': 'Home Win',
            'confidence': 90, 'risk': 'Low',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP3: Moderate Favorite Safety
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return {
            'blueprint': 'BP3', 'play': '1X & Over 1.5 Goals',
            'confidence': 85, 'risk': 'Low-Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP4: Goal Engine
    if 1.72 <= home <= 1.80:
        return {
            'blueprint': 'BP4', 'play': 'Over 1.5 Goals',
            'confidence': 75, 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP5: Defensive Trap
    if 1.90 <= home <= 2.02:
        return {
            'blueprint': 'BP5', 'play': '1X & Under 3.5 FT',
            'confidence': 70, 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP6: Strong Draw (AI-Enhanced)
    bp6_result = determine_bp6_play(draw, league, home_team, away_team)
    if bp6_result:
        play, confidence = bp6_result
        return {
            'blueprint': 'BP6', 'play': play,
            'confidence': confidence, 'risk': 'Medium',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP7: BTTS Value Spot (AI-Enhanced)
    bp7_result = determine_bp7_play(home, league)
    if bp7_result:
        play, confidence = bp7_result
        return {
            'blueprint': 'BP7', 'play': play,
            'confidence': confidence, 'risk': 'Low-Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    # BP8: High-Scoring Signals (AI-Enhanced)
    bp8_result = determine_bp8_play(draw, league)
    if bp8_result:
        play, confidence = bp8_result
        return {
            'blueprint': 'BP8', 'play': play,
            'confidence': confidence, 'risk': 'Moderate',
            'match': match['match'], 'league': league,
            'home_odds': home, 'draw_odds': draw, 'away_odds': away
        }
    
    return None

# ============================================================
# ACCUMULATOR BUILDER
# ============================================================

def build_accumulators(predictions):
    if len(predictions) < 2:
        return {}
    
    for p in predictions:
        if 'Home Win' in p['play']:
            p['odds'] = p['home_odds']
        elif 'Draw' in p['play']:
            p['odds'] = p['draw_odds']
        else:
            p['odds'] = 1.50
    
    sorted_picks = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    accumulators = {}
    used = set()
    
    def get_unused(pool):
        return [p for p in pool if p['match'] not in used]
    
    # 2_ODDS
    available = get_unused(sorted_picks)
    for n in [2, 3]:
        for combo in combinations(available[:6], n):
            total = 1
            for m in combo:
                total *= m['odds']
            if 1.8 <= total <= 2.5:
                accumulators['2_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                for m in combo:
                    used.add(m['match'])
                break
        if '2_ODDS' in accumulators:
            break
    
    # 4_ODDS
    available = get_unused(sorted_picks)
    for combo in combinations(available[:10], 4):
        total = 1
        for m in combo:
            total *= m['odds']
        if 3.5 <= total <= 5.0:
            accumulators['4_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 7_ODDS
    available = get_unused(sorted_picks)
    for combo in combinations(available[:12], 5):
        total = 1
        for m in combo:
            total *= m['odds']
        if 6.0 <= total <= 8.5:
            accumulators['7_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
            for m in combo:
                used.add(m['match'])
            break
    
    # 10_ODDS
    available = get_unused(sorted_picks)
    for n in [5, 6]:
        for combo in combinations(available[:15], n):
            total = 1
            for m in combo:
                total *= m['odds']
            if 9.0 <= total <= 12.0:
                accumulators['10_ODDS'] = {'matches': list(combo), 'odds': round(total, 2)}
                break
        if '10_ODDS' in accumulators:
            break
    
    return accumulators

# ============================================================
# TELEGRAM SENDER
# ============================================================

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return False
    
    if len(message) > 4096:
        message = message[:4000] + "\n\n... (truncated)"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=30)
        return r.json().get('ok', False)
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("⚽ JAY SOCCER BLUEPRINTS SYSTEM")
    print("8 BLUEPRINTS | AI-ENHANCED | MULTI-DATABASE")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Delete cache
    if os.path.exists("predictions.json"):
        os.remove("predictions.json")
        print("🗑️ Deleted old cache")
    
    # Parse matches
    matches = parse_matches()
    if not matches:
        print("\n❌ No matches found in input_matches.txt")
        return 1
    
    print(f"\n📊 Loaded {len(matches)} matches")
    
    # Analyze each match with AI-enhanced blueprints
    predictions = []
    for match in matches:
        result = analyze_match(match)
        if result:
            predictions.append(result)
    
    if not predictions:
        print("❌ No matches passed blueprints")
        return 1
    
    print(f"\n✅ {len(predictions)} matches passed blueprints")
    
    # Display predictions
    for i, p in enumerate(predictions[:20], 1):
        print(f"   {i}. {p['blueprint']}: {p['match'][:50]}")
        print(f"      🎯 {p['play']} | Conf: {p['confidence']}%")
    
    # Build accumulators
    accumulators = build_accumulators(predictions)
    
    # Build Telegram message
    message = f"""⚽ JAY SOCCER BLUEPRINTS - AI PREDICTIONS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
🤖 AI Data Sources: football-data.co.uk | Club Match Data | FBref
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BLUEPRINT PICKS ({len(predictions)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for p in predictions[:15]:
        emoji = "✅" if p['confidence'] >= 75 else "🟡"
        message += f"\n{emoji} {p['blueprint']}: {p['match'][:45]}\n   🎯 {p['play']} | Conf: {p['confidence']}%"
    
    if accumulators:
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎰 SMART ACCUMULATORS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for name, acc in accumulators.items():
            message += f"\n{name} | Total Odds: {acc['odds']}\n"
            for m in acc['matches']:
                message += f"   • {m['match'][:45]}\n"
                message += f"     🎯 {m['play']}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Bet responsibly!\n📊 AI predictions for informational purposes only."
    
    # Send to Telegram
    send_telegram(message)
    
    # Save predictions
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ SYSTEM COMPLETE")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Matches analyzed: {len(matches)}")
    print(f"   Predictions made: {len(predictions)}")
    print(f"   Accumulators built: {len(accumulators)}")
    print(f"   AI Data Sources: football-data.co.uk, Club Match Data, FBref")
    print(f"   Telegram: {'Sent' if TELEGRAM_TOKEN else 'Not configured'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
