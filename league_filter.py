# league_filter.py - Comprehensive League Filter

APPROVED_LEAGUES = {
    # Tier 1: Top European Leagues
    'premier league': 1.0, 'epl': 1.0, 'england': 1.0,
    'bundesliga': 1.0, 'germany': 1.0,
    'la liga': 1.0, 'spain': 1.0, 'laliga': 1.0,
    'serie a': 1.0, 'italy': 1.0, 'seriea': 1.0,
    'ligue 1': 1.0, 'france': 1.0,
    
    # Tier 2: European Leagues
    'eredivisie': 0.95, 'netherlands': 0.95, 'holland': 0.95,
    'primeira liga': 0.95, 'portugal': 0.95,
    'championship': 0.90, 'efl championship': 0.90,
    'belgian pro league': 0.90, 'belgium': 0.90,
    'scottish premiership': 0.90, 'scotland': 0.90,
    'swiss super league': 0.88, 'switzerland': 0.88,
    'austrian bundesliga': 0.88, 'austria': 0.88,
    'turkish super lig': 0.88, 'turkey': 0.88,
    'russian premier league': 0.88, 'russia': 0.88,
    'czech republic': 0.85, 'czech first league': 0.85,
    'poland': 0.85, 'polish ekstraklasa': 0.85,
    'croatia': 0.85, 'croatian hnl': 0.85,
    'greece': 0.85, 'greek superleague': 0.85,
    'denmark': 0.85, 'danish superliga': 0.85,
    'sweden': 0.85, 'swedish allsvenskan': 0.85,
    'norway': 0.85, 'norwegian eliteserien': 0.85,
    'bulgaria': 0.80, 'romania': 0.80, 'serbia': 0.80,
    'slovenia': 0.80, 'luxembourg': 0.75,
    'latvia': 0.75, 'estonia': 0.75, 'azerbaijan': 0.75,
    'moldova': 0.75, 'rwanda': 0.65,
    
    # Tier 3: World Leagues
    'mls': 0.85, 'usa': 0.85, 'canada': 0.80,
    'argentina': 0.80, 'argentine': 0.80,
    'brazil': 0.80, 'brasileirao': 0.80,
    'mexico': 0.80, 'liga mx': 0.80,
    'japan': 0.75, 'j league': 0.75,
    'korea': 0.75, 'k league': 0.75,
    'australia': 0.75, 'a-league': 0.75,
    'colombia': 0.70, 'chile': 0.70,
    'ecuador': 0.70, 'bolivia': 0.65,
    'uruguay': 0.70, 'paraguay': 0.65,
    'peru': 0.65, 'venezuela': 0.60,
    
    # African Leagues
    'egypt': 0.70, 'tunisia': 0.70, 'morocco': 0.70,
    'algeria': 0.65, 'south africa': 0.70,
    'uganda': 0.55, 'tanzania': 0.55, 'kenya': 0.55,
    'zambia': 0.55, 'zimbabwe': 0.55, 'mozambique': 0.55,
    'ghana': 0.55, 'senegal': 0.55,
    
    # Asian Leagues
    'saudi arabia': 0.70, 'uae': 0.65, 'qatar': 0.65,
    'oman': 0.55, 'kazakhstan': 0.60,
    'china': 0.70, 'india': 0.60,
}

# Excluded keywords - matches with these are automatically rejected
EXCLUDED_KEYWORDS = [
    'u20', 'u19', 'u21', 'u18', 'youth', 'academy', 'junior',
    'reserve', 'reserves', 'b team', 'ii', '2', '3', 'b', 'c',
    'women', 'womens', 'frauen', 'femminile', 'femenino', 'w',
    'cup', 'pokal', 'coppa', 'copa', 'fa cup', 'league cup',
    'amateur', 'regional', 'district', 'local', 'friendly',
    'play offs', 'relegation', 'promotion',
]


def is_approved_league(league_name):
    """Check if league should be scanned - case insensitive"""
    if not league_name or league_name == 'Unknown':
        return False
    
    league_lower = league_name.lower().strip()
    
    # First check excluded keywords
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in league_lower:
            return False
    
    # Then check if in approved list
    for approved in APPROVED_LEAGUES.keys():
        if approved in league_lower:
            return True
    
    # Also check direct country name matches (for uppercase like "ENGLAND")
    country_matches = {
        'england': True, 'germany': True, 'spain': True, 'italy': True, 'france': True,
        'netherlands': True, 'portugal': True, 'belgium': True, 'scotland': True,
        'austria': True, 'turkey': True, 'russia': True, 'czech': True, 'poland': True,
        'croatia': True, 'greece': True, 'denmark': True, 'sweden': True, 'norway': True,
        'bulgaria': True, 'romania': True, 'serbia': True, 'argentina': True,
        'brazil': True, 'mexico': True, 'japan': True, 'korea': True, 'australia': True,
        'egypt': True, 'tunisia': True, 'saudi': True, 'ukraine': True,
    }
    
    for country, _ in country_matches.items():
        if country in league_lower:
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
    
    # Default quality for unknown leagues
    return 0.6
