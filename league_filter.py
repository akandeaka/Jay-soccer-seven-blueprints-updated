# league_filter.py - League Quality Filter Module (Expanded)

APPROVED_LEAGUES = {
    # Tier 1: Top 5 European Leagues
    'premier league': 1.0, 'epl': 1.0, 'england': 0.95,
    'bundesliga': 1.0, 'germany': 0.95,
    'la liga': 1.0, 'spain': 0.95, 'laliga': 1.0,
    'serie a': 1.0, 'italy': 0.95, 'seriea': 1.0,
    'ligue 1': 1.0, 'france': 0.95,
    
    # Tier 2: Strong European Leagues
    'eredivisie': 0.95, 'netherlands': 0.90,
    'primeira liga': 0.95, 'portugal': 0.90,
    'championship': 0.90, 'efl championship': 0.90,
    'belgian pro league': 0.90, 'belgium': 0.85,
    'scottish premiership': 0.90, 'scotland': 0.85,
    'swiss super league': 0.88, 'switzerland': 0.85,
    'austrian bundesliga': 0.88, 'austria': 0.85,
    'turkish super lig': 0.88, 'turkey': 0.85,
    'russian premier league': 0.88, 'russia': 0.85,
    'czech first league': 0.85, 'czech republic': 0.80,
    'polish ekstraklasa': 0.85, 'poland': 0.80,
    'croatian hnl': 0.85, 'croatia': 0.80,
    'greek superleague': 0.85, 'greece': 0.80,
    'danish superliga': 0.85, 'denmark': 0.80,
    'swedish allsvenskan': 0.85, 'sweden': 0.80,
    'norwegian eliteserien': 0.85, 'norway': 0.80,
    
    # Tier 3: Quality Non-European Leagues
    'mls': 0.80, 'usa': 0.80, 'united states': 0.80,
    'argentina': 0.75, 'argentine': 0.75,
    'brazil': 0.75, 'brasileirao': 0.75,
    'mexico': 0.75, 'liga mx': 0.75,
    'japan': 0.70, 'j league': 0.70,
    'korea': 0.70, 'k league': 0.70,
    'australia': 0.70, 'a-league': 0.70,
}

# Common words that indicate a match is NOT a top league
EXCLUDED_KEYWORDS = [
    'u20', 'u19', 'u21', 'u18', 'youth', 'academy', 'junior',
    'reserve', 'reserves', 'b team', 'ii', '2', '3', 'b', 'c',
    'women', 'womens', 'frauen', 'femminile', 'femenino', 'w',
    'cup', 'pokal', 'coppa', 'copa', 'fa cup', 'league cup',
    'amateur', 'regional', 'district', 'local',
    'friendly', 'club friendly', 'play offs', 'relegation',
    'africa', 'asia', 'oceania', 'south america', 'north america',
]


def is_approved_league(league_name):
    """Check if league should be scanned"""
    if not league_name or league_name == 'Unknown':
        return False
    
    league_lower = league_name.lower()
    
    # First check excluded keywords
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in league_lower:
            return False
    
    # Then check if in approved list
    for approved in APPROVED_LEAGUES.keys():
        if approved in league_lower:
            return True
    
    return False


def get_league_quality(league_name):
    """Get league quality multiplier"""
    if not league_name:
        return 0.5
    
    league_lower = league_name.lower()
    for league, quality in APPROVED_LEAGUES.items():
        if league in league_lower:
            return quality
    return 0.5
