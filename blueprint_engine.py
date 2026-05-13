"""
Blueprint Engine - 8 Blueprints UPDATED
BP6: Draw or GG / Draw or Under 2.5
BP8: Over 2.5 Goals ONLY if 0-0 odds > 20
"""

HIGH_SCORING_LEAGUES = [
    'bundesliga', 'eredivisie', 'premier league', 'epl',
    'serie a', 'ligue 1', 'la liga', 'championship'
]

LOW_SCORING_LEAGUES = [
    'serie b', 'ligue 2', 'argentina', 'brazil', 'uruguay'
]


def check_bp1(home, away):
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return ('BP1', 'Straight Home Win', 95)
    return None


def check_bp2(home, away):
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return ('BP2', 'Home Win', 90)
    return None


def check_bp3(home, away):
    if 1.30 <= home <= 1.36 and 7.0 <= away <= 8.99:
        return ('BP3', '1X & Over 1.5 Goals', 85)
    return None


def check_bp4(home, league):
    if 1.72 <= home <= 1.80:
        is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
        conf = 75 if is_high else 68
        return ('BP4', 'Over 1.5 Goals', conf)
    return None


def check_bp5(home):
    if 1.90 <= home <= 2.02:
        return ('BP5', '1X & Under 3.5 FT', 70)
    return None


def check_bp6(draw, league):
    """BP6: Draw or GG / Draw or Under 2.5"""
    if not (2.75 <= draw <= 3.39):
        return None
    
    is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
    is_low = any(ll in league.lower() for ll in LOW_SCORING_LEAGUES)
    
    if is_high:
        return ('BP6', 'Draw or GG (Draw OR Both Teams to Score)', 68)
    elif is_low:
        return ('BP6', 'Draw or Under 2.5 Goals', 72)
    else:
        return ('BP6', 'Full Time Draw', 55)


def check_bp7(home, league):
    if 1.40 <= home <= 1.69:
        is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
        if is_high:
            return ('BP7', 'Both Teams to Score - YES', 75)
        else:
            return ('BP7', 'Both Teams to Score - NO', 65)
    return None


def check_bp8(draw, league, correct_scores=None):
    """BP8: Over 2.5 Goals - CRITERIA: 0-0 odds > 20"""
    is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
    
    if not (3.60 <= draw <= 3.75 and is_high):
        return None
    
    if correct_scores:
        odds_00 = correct_scores.get('0-0', 0)
        if odds_00 > 20:
            return ('BP8', 'Over 2.5 Goals', 75)
    
    return None


class BlueprintEngine:
    def __init__(self):
        self.stats = {f'BP{i}': 0 for i in range(1, 9)}
    
    def classify(self, match):
        home = match.get('home_odds', 0)
        draw = match.get('draw_odds', 0)
        away = match.get('away_odds', 0)
        league = match.get('league', '')
        correct_scores = match.get('correct_scores', {})
        
        # Check BP8 first (needs correct_scores)
        result = check_bp8(draw, league, correct_scores)
        
        if not result:
            result = (check_bp1(home, away) or check_bp2(home, away) or
                      check_bp3(home, away) or check_bp4(home, league) or
                      check_bp5(home) or check_bp6(draw, league) or
                      check_bp7(home, league))
        
        if result:
            bp, play, conf = result
            self.stats[bp] += 1
            return {
                'blueprint': bp,
                'play': play,
                'confidence': conf,
                'match': match.get('match'),
                'league': league,
                'home_odds': home,
                'draw_odds': draw,
                'away_odds': away
            }
        return None
