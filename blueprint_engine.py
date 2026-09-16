"""
Blueprint Engine - Data-Validated Version (Final)

Only four rules survived an 11-season backtest of 55,699 matches
(2014/15 through 2024/25):

  BP3  - Draw in close matches                    +3.77% ROI, 9/11 positive
  BP4  - Home Win @ 1.72-1.80, high-scoring       +2.10% ROI, 7/11 positive
  BP12 - Home Win + Over 2.5 FT @ 1.20-1.30       +9.54% ROI, 9/11 positive
  BP13 - Home Win @ 1.70-1.75, select leagues     +2.10% ROI, 7/11 positive

All other blueprints (BP1, BP2, BP5, BP6, BP7, BP8) failed the backtest.
They are preserved in code but disabled by default.

To re-enable any disabled blueprint, add its ID to ENABLED_BLUEPRINTS.
"""

# ============================================================
# ENABLED BLUEPRINTS
# ============================================================

ENABLED_BLUEPRINTS = ["BP3", "BP4", "BP12", "BP13"]


# ============================================================
# LEAGUE QUALITY FILTER
# ============================================================

APPROVED_LEAGUES = [
    'premier league', 'bundesliga', 'la liga', 'serie a', 'ligue 1',
    'championship', 'eredivisie', 'primeira liga', 'belgian pro league',
    'scottish premiership', 'turkish super lig', 'russian premier league',
    'mls', 'argentina', 'brazil', 'mexico', 'colombia', 'chile',
    'czech republic', 'poland', 'greece', 'denmark', 'sweden', 'norway',
    'austria', 'switzerland', 'croatia', 'serbia', 'bulgaria', 'romania',
    'ukraine', 'israel', 'korea', 'japan', 'china'
]

LOW_QUALITY_KEYWORDS = [
    'u20', 'u19', 'u21', 'reserve', '2', 'ii', 'b', 'youth', 'academy',
    'amateur', 'regional', 'cup', 'pokal', 'coppa', 'copa', 'fa cup'
]


def get_league_quality(league_name):
    league_lower = league_name.lower()
    for kw in LOW_QUALITY_KEYWORDS:
        if kw in league_lower:
            return 0.3
    for approved in APPROVED_LEAGUES:
        if approved in league_lower:
            return 1.0
    return 0.6


# ============================================================
# LEAGUE CLASSIFICATIONS
# ============================================================

HIGH_SCORING_LEAGUES = [
    'bundesliga', 'eredivisie', 'premier league', 'epl',
    'serie a', 'ligue 1', 'la liga', 'championship'
]

BP12_LEAGUES = ['bundesliga', 'eredivisie', 'premier league', 'epl']
BP13_LEAGUES = ['eredivisie', 'bundesliga', 'championship', 'premier league', 'epl']


# ============================================================
# LEGACY BLUEPRINTS (disabled by default)
# ============================================================

def check_bp1(home, away):
    if 1.20 <= home <= 1.29 and away >= 10.0:
        return ('BP1', 'Straight Home Win', 95)
    return None


def check_bp2(home, away):
    if 1.30 <= home <= 1.36 and away >= 9.0:
        return ('BP2', 'Home Win', 90)
    return None


def check_bp5(home):
    if 1.90 <= home <= 2.02:
        return ('BP5', '1X & Under 3.5 FT', 70)
    return None


def check_bp6(draw, league, home_goals_avg=1.2, away_goals_avg=1.2):
    if not (2.75 <= draw <= 3.39):
        return None
    avg_goals = (home_goals_avg + away_goals_avg) / 2
    league_lower = league.lower()
    high_scoring = ['bundesliga', 'eredivisie', 'premier league', 'epl',
                    'serie a', 'ligue 1', 'la liga']
    low_scoring = ['serie b', 'ligue 2', 'japan', 'j1', 'j2',
                   'korea', 'k-league', 'china']
    is_high = (avg_goals >= 1.3 or any(hl in league_lower for hl in high_scoring))
    is_low = (avg_goals <= 1.0 or any(ll in league_lower for ll in low_scoring))
    if is_high:
        return ('BP6', 'Draw or GG', 68)
    elif is_low:
        return ('BP6', 'Draw or Under 2.5 Goals', 72)
    return ('BP6', 'Draw or Under 2.5 Goals', 60)


def check_bp7(home, league):
    if 1.40 <= home <= 1.69:
        is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
        if is_high:
            return ('BP7', 'Both Teams to Score - YES', 75)
        return ('BP7', 'Both Teams to Score - NO', 65)
    return None


def check_bp8(draw, league, correct_scores=None):
    is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
    if not (3.60 <= draw <= 3.75 and is_high):
        return None
    if correct_scores:
        odds_00 = correct_scores.get('0-0', 0)
        if odds_00 > 20:
            return ('BP8', 'Over 2.5 Goals', 75)
    return None


# ============================================================
# VALIDATED BLUEPRINTS
# ============================================================

def check_bp3(home, draw, away):
    """BP3 — Draw in close matches. +3.77% ROI, 9/11 positive."""
    if not (2.80 <= draw <= 3.40):
        return None
    if abs(home - draw) > 0.50:
        return None
    if abs(away - draw) > 0.50:
        return None
    return ('BP3', 'Full Time Draw', 50)


def check_bp4(home, league):
    """BP4 — Straight home win @ 1.72-1.80. +2.10% ROI, 7/11 positive."""
    if 1.72 <= home <= 1.80:
        is_high = any(hl in league.lower() for hl in HIGH_SCORING_LEAGUES)
        conf = 58 if is_high else 55
        return ('BP4', 'Straight Home Win', conf)
    return None


def check_bp12(home, league):
    """BP12 — Home Win + Over 2.5 FT @ 1.20-1.30. +9.54% ROI, 9/11 positive."""
    if not (1.20 <= home <= 1.30):
        return None
    if not any(hl in league.lower() for hl in BP12_LEAGUES):
        return None
    return ('BP12', 'Home Win + Over 2.5 Goals', 58)


def check_bp13(home, league):
    """BP13 — Straight home win @ 1.70-1.75. +2.10% ROI, 7/11 positive."""
    if not (1.70 <= home <= 1.75):
        return None
    if not any(hl in league.lower() for hl in BP13_LEAGUES):
        return None
    return ('BP13', 'Straight Home Win', 57)


# ============================================================
# ENGINE
# ============================================================

class BlueprintEngine:
    def __init__(self, enabled=None):
        self.enabled = set(enabled) if enabled else set(ENABLED_BLUEPRINTS)
        self.stats = {f'BP{i}': 0 for i in range(1, 14)}

    def classify(self, match):
        home = match.get('home_odds', 0)
        draw = match.get('draw_odds', 0)
        away = match.get('away_odds', 0)
        league = match.get('league', '')
        correct_scores = match.get('correct_scores', {})

        candidates = [
            check_bp12(home, league),                    # +9.54%
            check_bp13(home, league),                    # +2.10% (tighter)
            check_bp4(home, league),                     # +2.10% (wider)
            check_bp3(home, draw, away),                 # +3.77%
            check_bp8(draw, league, correct_scores),
            check_bp1(home, away),
            check_bp2(home, away),
            check_bp5(home),
            check_bp6(draw, league),
            check_bp7(home, league),
        ]

        for result in candidates:
            if not result:
                continue
            bp, play, conf = result
            if bp not in self.enabled:
                continue
            self.stats[bp] += 1
            return {
                'blueprint': bp,
                'play': play,
                'confidence': conf,
                'match': match.get('match'),
                'league': league,
                'home_odds': home,
                'draw_odds': draw,
                'away_odds': away,
            }
        return None
