"""
Result Fetcher - Automatically fetches match results from football APIs
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class ResultFetcher:
    """Automatically fetch match results from multiple sources"""
    
    def __init__(self):
        self.results = []
        
    def fetch_from_sportmonks(self, match_date: str = None) -> pd.DataFrame:
        """
        Fetch results from Sportmonks API
        Requires API key in environment variables
        """
        api_key = os.getenv('SPORTMONKS_API_KEY', '')
        
        if not api_key:
            print("⚠️ Sportmonks API key not found")
            return pd.DataFrame()
        
        if not match_date:
            match_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Sportmonks API endpoint for fixtures by date
        url = f"https://soccer.sportmonks.com/api/v2.0/fixtures/date/{match_date}"
        
        params = {
            'api_token': api_key,
            'include': 'localTeam,visitorTeam,league',
            'per_page': 100
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            matches = []
            for fixture in data.get('data', []):
                match = {
                    'match': f"{fixture['localTeam']['data']['name']} vs {fixture['visitorTeam']['data']['name']}",
                    'home_score': fixture.get('scores', {}).get('localteam_score', 0),
                    'away_score': fixture.get('scores', {}).get('visitorteam_score', 0),
                    'result': self._determine_result(
                        fixture.get('scores', {}).get('localteam_score', 0),
                        fixture.get('scores', {}).get('visitorteam_score', 0)
                    ),
                    'league': fixture.get('league', {}).get('data', {}).get('name', 'Unknown'),
                    'status': fixture.get('status', '')
                }
                
                if match['home_score'] > 0 or match['away_score'] > 0:
                    matches.append(match)
            
            print(f"✅ Fetched {len(matches)} results from Sportmonks")
            return pd.DataFrame(matches)
            
        except Exception as e:
            print(f"❌ Error fetching from Sportmonks: {e}")
            return pd.DataFrame()
    
    def fetch_from_football_data_org(self) -> pd.DataFrame:
        """
        Fetch results from Football-Data.org API
        """
        api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
        
        if not api_key:
            print("⚠️ Football-Data.org API key not found")
            return pd.DataFrame()
        
        # API endpoints for top leagues
        leagues = ['PL', 'BL1', 'SA', 'PD', 'FL1']  # Premier League, Bundesliga, Serie A, La Liga, Ligue 1
        all_matches = []
        
        for league in leagues:
            url = f"https://api.football-data.org/v4/competitions/{league}/matches"
            headers = {'X-Auth-Token': api_key}
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                data = response.json()
                
                for match in data.get('matches', []):
                    if match.get('status') == 'FINISHED':
                        match_data = {
                            'match': f"{match['homeTeam']['name']} vs {match['awayTeam']['name']}",
                            'home_score': match['score']['fullTime']['home'],
                            'away_score': match['score']['fullTime']['away'],
                            'result': self._determine_result(
                                match['score']['fullTime']['home'],
                                match['score']['fullTime']['away']
                            ),
                            'league': match['competition']['name'],
                            'status': 'FINISHED'
                        }
                        all_matches.append(match_data)
                
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                print(f"❌ Error fetching {league}: {e}")
        
        print(f"✅ Fetched {len(all_matches)} results from Football-Data.org")
        return pd.DataFrame(all_matches)
    
    def fetch_from_web_scraping(self, predicted_matches: List[Dict]) -> pd.DataFrame:
        """
        Fetch results via web scraping (fallback method)
        """
        from bs4 import BeautifulSoup
        
        results = []
        
        for match in predicted_matches:
            match_name = match.get('match', '')
            # Construct search query
            search_query = match_name.replace(' vs ', ' ')[:50]
            
            # This would require scraping specific sites
            # Simplified for now
            pass
        
        return pd.DataFrame(results)
    
    def _determine_result(self, home_score: int, away_score: int) -> str:
        """Determine match result from scores"""
        if home_score > away_score:
            return 'Home Win'
        elif home_score < away_score:
            return 'Away Win'
        else:
            return 'Draw'
    
    def validate_predictions(self, predictions_file: str = "predictions.json") -> pd.DataFrame:
        """Fetch results and validate against predictions"""
        
        # Load predictions
        try:
            with open(predictions_file, 'r') as f:
                predictions = json.load(f)
            print(f"✅ Loaded {len(predictions)} predictions from {predictions_file}")
        except Exception as e:
            print(f"❌ Could not load predictions: {e}")
            return pd.DataFrame()
        
        # Fetch actual results
        actual_results = self.fetch_from_football_data_org()
        
        if actual_results.empty:
            actual_results = self.fetch_from_sportmonks()
        
        if actual_results.empty:
            print("❌ No results fetched from any source")
            return pd.DataFrame()
        
        # Validate each prediction
        validated_results = []
        
        for pred in predictions:
            match_name = pred.get('match', '')
            
            # Find matching actual result
            actual = None
            for _, row in actual_results.iterrows():
                if match_name.lower() in row['match'].lower() or row['match'].lower() in match_name.lower():
                    actual = row
                    break
            
            if actual is not None:
                is_correct = self._check_prediction_correct(pred, actual)
                
                validated_results.append({
                    'match': match_name,
                    'blueprint': pred.get('blueprint', ''),
                    'predicted_play': pred.get('play', ''),
                    'ai_confidence': pred.get('ai_confidence', 0),
                    'home_score': actual['home_score'],
                    'away_score': actual['away_score'],
                    'actual_result': actual['result'],
                    'is_correct': is_correct
                })
        
        # Save validated results
        df = pd.DataFrame(validated_results)
        df.to_csv("actual_results.csv", index=False)
        print(f"✅ Saved {len(df)} validated results to actual_results.csv")
        
        return df
    
    def _check_prediction_correct(self, prediction: Dict, actual: pd.Series) -> bool:
        """Check if prediction was correct"""
        predicted_play = prediction.get('play', '')
        home_score = actual['home_score']
        away_score = actual['away_score']
        
        if 'Home Win' in predicted_play:
            return home_score > away_score
        elif 'Away Win' in predicted_play:
            return away_score > home_score
        elif 'Draw' in predicted_play:
            return home_score == away_score
        elif 'BTTS' in predicted_play or 'Both Teams to Score' in predicted_play:
            return home_score > 0 and away_score > 0
        elif 'Over 1.5' in predicted_play:
            return (home_score + away_score) > 1
        elif 'Over 2.5' in predicted_play:
            return (home_score + away_score) > 2
        elif 'Under 3.5' in predicted_play:
            return (home_score + away_score) < 4
        
        return False
