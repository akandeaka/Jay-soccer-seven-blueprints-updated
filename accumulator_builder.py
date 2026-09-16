"""
Accumulator Builder - Data-Driven Inclusion
Includes ALL leagues with sufficient statistical data
Excludes ONLY leagues with poor/inconsistent data
"""

import os
import json
from itertools import combinations

# ============================================================
# LEAGUES WITH GOOD STATISTICAL DATA (INCLUDED)
# ============================================================

# TIER 1: Elite Men's Leagues (Extensive data)
TIER_1_MENS = {
    'premier league': 1.0,
    'bundesliga': 1.0,
    'la liga': 1.0,
    'serie a': 1.0,
    'ligue 1': 1.0,
    'eredivisie': 0.98,
    'primeira liga': 0.98,
    'championship': 0.95,
}

# TIER 2: Strong Men's Leagues (Good data)
TIER_2_MENS = {
    'belgian pro league': 0.92,
    'scottish premiership': 0.90,
    'swiss super league': 0.90,
    'austrian bundesliga': 0.90,
    'turkish super lig': 0.88,
    'russian premier league': 0.88,
    'czech first league': 0.85,
    'polish ekstraklasa': 0.85,
    'croatian hnl': 0.85,
    'greek superleague': 0.85,
    'denmark superliga': 0.85,
    'sweden allsvenskan': 0.85,
    'norway eliteserien': 0.85,
}

# TIER 3: Competitive Men's Leagues (Moderate data)
TIER_3_MENS = {
    'mls': 0.80,
    'argentina': 0.78,
    'brazil': 0.78,
    'mexico': 0.78,
    'japan': 0.75,
    'korea': 0.75,
    'australia': 0.75,
    'china': 0.70,
    'india': 0.65,
}

# TIER 1: Women's Leagues (Good data - DO NOT EXCLUDE)
TIER_1_WOMENS = {
    'women\'s super league': 0.95,  # England
    'frauen bundesliga': 0.95,       # Germany
    'serie a femminile': 0.92,       # Italy
    'ligue 1 feminine': 0.92,        # France
    'liga f': 0.90,                  # Spain
    'nwsl': 0.92,                    # USA
}

# TIER 2: Other Women's Leagues (Developing but usable)
TIER_2_WOMENS = {
    'damallsvenskan': 0.85,          # Sweden
    'toppserien': 0.85,              # Norway
    'naisten liiga': 0.80,           # Finland
    'ekoligia': 0.80,                # Czech
}

# Lower divisions with good goal statistics (INCLUDED)
LOWER_DIVISIONS = {
    'league one': 0.85,              # England 3rd tier
    'league two': 0.82,              # England 4th tier
    '2. bundesliga': 0.85,           # Germany 2nd tier
    '3. liga': 0.80,                 # Germany 3rd tier
    'serie b': 0.82,                 # Italy 2nd tier
    'serie c': 0.75,                 # Italy 3rd tier
    'liga 2': 0.82,                  # Spain 2nd tier
    'scottish championship': 0.82,   # Scotland 2nd tier
}

# ============================================================
# EXCLUDED ONLY (Poor/inconsistent data)
# ============================================================

EXCLUDED_KEYWORDS = [
    # Reserve teams (inconsistent lineups, poor data)
    'reserve', 'reserves', 'b team', 'ii',
    # Youth leagues (highly unpredictable, limited data)
    'u20', 'u19', 'u21', 'u18', 'youth', 'academy', 'junior', 'primavera',
    # Cup competitions (one-off matches, unpredictable)
    'cup', 'pokal', 'coppa', 'copa', 'fa cup', 'league cup', 'dfb pokal',
    'carabao cup', 'efl trophy',
    # Obscure leagues with no data
    'oman', 'uae', 'qatar', 'bahrain', 'kuwait', 'jordan',
    'vietnam', 'thailand', 'indonesia', 'malaysia', 'philippines',
    'mongolia', 'cambodia', 'myanmar', 'laos', 'brunei',
    # Amateur/Semi-pro (no reliable data)
    'amateur', 'semi-pro', 'regional', 'district',
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_league_data_quality(league_name):
    """Get data quality score for ANY league (0-1)"""
    league_lower = league_name.lower()
    
    # Check excluded first
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in league_lower:
            return 0  # No data, exclude
    
    # Check Tier 1 Men's
    for key, score in TIER_1_MENS.items():
        if key in league_lower:
            return score
    
    # Check Tier 2 Men's
    for key, score in TIER_2_MENS.items():
        if key in league_lower:
            return score
    
    # Check Tier 3 Men's
    for key, score in TIER_3_MENS.items():
        if key in league_lower:
            return score
    
    # Check Women's Leagues (INCLUDED)
    for key, score in TIER_1_WOMENS.items():
        if key in league_lower:
            return score
    
    for key, score in TIER_2_WOMENS.items():
        if key in league_lower:
            return score
    
    # Check Lower Divisions (INCLUDED)
    for key, score in LOWER_DIVISIONS.items():
        if key in league_lower:
            return score
    
    # Unknown league - give minimal score but don't exclude
    if any(x in league_lower for x in ['league', 'liga', 'bundesliga', 'serie']):
        return 0.50  # Probably a lower division
    
    return 0  # Exclude if truly unknown


def is_valid_for_accumulator(league_name):
    """Check if league has sufficient data for accumulator"""
    score = get_league_data_quality(league_name)
    return score > 0  # Any positive score


def get_league_multiplier(league_name):
    """Get multiplier for quality scoring"""
    return get_league_data_quality(league_name)


def get_league_insight(league_name):
    """Provide insight about league data quality"""
    league_lower = league_name.lower()
    score = get_league_data_quality(league_name)
    
    if score >= 0.95:
        return "🔥 ELITE DATA - Extensive historical records"
    elif score >= 0.85:
        return "✅ EXCELLENT DATA - Strong statistical records"
    elif score >= 0.75:
        return "🟡 GOOD DATA - Reliable for predictions"
    elif score >= 0.65:
        return "📊 MODERATE DATA - Use with caution"
    elif score > 0:
        return "⚠️ LIMITED DATA - Lower confidence"
    else:
        return "🚫 EXCLUDED - Insufficient data"


def calculate_quality_score(match):
    """Calculate quality score based on data availability"""
    
    league = match.get('league', '')
    
    # Get data quality score
    data_quality = get_league_data_quality(league)
    
    if data_quality == 0:
        return 0  # Excluded
    
    bp = match.get('blueprint', '')
    confidence = match.get('confidence', 50)
    
    # League score (0-40)
    league_score = 40 * data_quality
    
    # Blueprint weights (based on historical performance)
    bp_weights = {
        'BP1': 0.85, 'BP2': 0.82, 'BP3': 0.70,
        'BP4': 0.75, 'BP5': 0.68, 'BP6': 0.35,
        'BP7': 0.60, 'BP8': 0.65
    }
    bp_score = 30 * bp_weights.get(bp, 0.50)
    
    # Confidence score (0-30)
    confidence_score = 30 * (confidence / 100)
    
    return round(league_score + bp_score + confidence_score, 1)

# ============================================================
# MAIN ACCUMULATOR BUILDER
# ============================================================

def build_accumulators(predictions):
    """
    # Only accumulate validated blueprints
    from blueprint_engine import ENABLED_BLUEPRINTS
    predictions = [p for p in predictions if p.get('blueprint') in ENABLED_BLUEPRINTS]
    if len(predictions) < 2:
        return {}
    Build accumulators using data-driven league inclusion
    INCLUDES: Women's leagues, lower divisions with good data
    EXCLUDES: Reserve teams, youth leagues, cup competitions, obscure leagues
    """
    
    if len(predictions) < 2:
        return {}
    
    # Filter for valid leagues
    valid_picks = []
    excluded_count = 0
    
    for p in predictions:
        league = p.get('league', '')
        
        if is_valid_for_accumulator(league):
            p['quality_score'] = calculate_quality_score(p)
            p['league_insight'] = get_league_insight(league)
            p['data_quality'] = get_league_data_quality(league)
            
            # Set odds
            play = p.get('play', '')
            if 'Home Win' in play:
                p['odds'] = p.get('home_odds', 1.50)
            elif 'Draw' in play:
                p['odds'] = p.get('draw_odds', 1.50)
            else:
                p['odds'] = 1.50
            
            valid_picks.append(p)
        else:
            excluded_count += 1
    
    print(f"\n🎯 DATA-DRIVEN FILTER:")
    print(f"   Total predictions: {len(predictions)}")
    print(f"   Excluded (poor/inconsistent data): {excluded_count}")
    print(f"   Eligible (good data): {len(valid_picks)}")
    
    if len(valid_picks) < 2:
        print("   ⚠️ Not enough eligible picks for accumulators")
        return {}
    
    # Sort by quality
    sorted_picks = sorted(valid_picks, key=lambda x: x['quality_score'], reverse=True)
    
    print(f"\n🏆 ELIGIBLE PICKS (By Data Quality):")
    for i, p in enumerate(sorted_picks[:15], 1):
        quality = p['quality_score']
        quality_emoji = "🔥" if quality >= 80 else "✅" if quality >= 70 else "🟡" if quality >= 60 else "⚠️"
        league_type = "👩 Women's" if any(w in p.get('league', '').lower() for w in ['women', 'womens', 'frauen', 'femminile']) else "⚽ Men's"
        print(f"   {i}. {quality_emoji} {p['blueprint']}: {p['match'][:45]}")
        print(f"      {league_type} | {p.get('league', 'Unknown')} | Data Quality: {p['data_quality']:.0%}")
        print(f"      🎯 {p['play']} | Odds: {p['odds']}")
        print(f"      📊 {p['league_insight']}")
    
    accumulators = {}
    used_matches = set()
    
    def get_unused(pool):
        return [p for p in pool if p['match'] not in used_matches]
    
    # Build 2_ODDS from highest quality
    high_quality = [p for p in sorted_picks if p['quality_score'] >= 75]
    pool = get_unused(high_quality)
    if len(pool) >= 2:
        combo = pool[:2]
        total = combo[0]['odds'] * combo[1]['odds']
        accumulators['2_ODDS'] = {
            'matches': list(combo),
            'odds': round(total, 2),
            'avg_quality': round((combo[0]['quality_score'] + combo[1]['quality_score']) / 2, 1),
            'avg_data_quality': round((combo[0]['data_quality'] + combo[1]['data_quality']) / 2, 2)
        }
        for m in combo:
            used_matches.add(m['match'])
        print(f"\n✅ 2_ODDS built (Avg Data Quality: {accumulators['2_ODDS']['avg_data_quality']:.0%})")
    
    # Build 4_ODDS from good quality
    good_quality = [p for p in sorted_picks if p['quality_score'] >= 65]
    pool = get_unused(good_quality)
    if len(pool) >= 4:
        combo = pool[:4]
        total = 1
        for m in combo:
            total *= m['odds']
        accumulators['4_ODDS'] = {
            'matches': list(combo),
            'odds': round(total, 2),
            'avg_quality': round(sum(m['quality_score'] for m in combo) / 4, 1),
            'avg_data_quality': round(sum(m['data_quality'] for m in combo) / 4, 2)
        }
        for m in combo:
            used_matches.add(m['match'])
        print(f"✅ 4_ODDS built (Avg Data Quality: {accumulators['4_ODDS']['avg_data_quality']:.0%})")
    
    # Build 7_ODDS from acceptable quality
    acceptable = [p for p in sorted_picks if p['quality_score'] >= 55]
    pool = get_unused(acceptable)
    if len(pool) >= 5:
        combo = pool[:5]
        total = 1
        for m in combo:
            total *= m['odds']
        accumulators['7_ODDS'] = {
            'matches': list(combo),
            'odds': round(total, 2),
            'avg_quality': round(sum(m['quality_score'] for m in combo) / 5, 1),
            'avg_data_quality': round(sum(m['data_quality'] for m in combo) / 5, 2)
        }
        print(f"✅ 7_ODDS built (Avg Data Quality: {accumulators['7_ODDS']['avg_data_quality']:.0%})")
    
    return accumulators
