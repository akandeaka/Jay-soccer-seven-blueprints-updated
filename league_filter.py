# league_filter.py - Add this new file instead of modifying main.py
"""
League Quality Filter - Separate module
Can be imported without affecting existing code
"""

APPROVED_LEAGUES = {
    'premier league': 1.0, 'bundesliga': 1.0, 'la liga': 1.0,
    'serie a': 1.0, 'ligue 1': 1.0, 'eredivisie': 0.95,
    'primeira liga': 0.95, 'championship': 0.90,
    'belgian pro league': 0.90, 'scottish premiership': 0.90,
    'mls': 0.80, 'argentina': 0.75, 'brazil': 0.75,
}

EXCLUDED_KEYWORDS = [
    'u20', 'u19', 'u21', 'youth', 'academy', 'junior',
    'reserve', 'b team', 'women', 'cup', 'friendly'
]

def is_approved_league(league_name):
    league_lower = league_name.lower()
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in league_lower:
            return False
    for approved in APPROVED_LEAGUES.keys():
        if approved in league_lower:
            return True
    return False
