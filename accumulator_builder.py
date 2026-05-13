"""
Accumulator Builder - Smart Quality-Based Version
Function name: build_accumulators (compatible with existing main.py)
NO DUPLICATE MATCHES ACROSS ACCUMULATORS
"""

from itertools import combinations


# League quality multipliers
LEAGUE_QUALITY = {
    'premier league': 1.0,
    'bundesliga': 1.0,
    'la liga': 1.0,
    'serie a': 1.0,
    'ligue 1': 1.0,
    'championship': 0.85,
    'eredivisie': 0.85,
    'primeira liga': 0.85,
    'argentina': 0.65,
    'brazil': 0.65,
    'reserve': 0.25,
    'u20': 0.20,
    'u19': 0.20,
}

# Blueprint performance multipliers
BLUEPRINT_PERFORMANCE = {
    'BP1': 1.0,
    'BP2': 1.0,
    'BP3': 0.7,
    'BP4': 0.85,
    'BP5': 0.9,
    'BP6': 0.35,  # Heavily penalized - 32% accuracy
    'BP7': 0.55,
    'BP8': 0.7,
}

MIN_QUALITY_SCORE = 55


def calculate_quality_score(match):
    """Calculate quality score (0-100) for a match"""
    
    league = match.get('league', '').lower()
    league_score = 20
    
    for key, multiplier in LEAGUE_QUALITY.items():
        if key in league:
            league_score = 40 * multiplier
            break
    
    if 'reserve' in league or 'u20' in league or 'u19' in league:
        league_score = league_score * 0.5
    
    bp = match.get('blueprint', '')
    bp_score = 30 * BLUEPRINT_PERFORMANCE.get(bp, 0.5)
    
    confidence = match.get('confidence', 50)
    confidence_score = 30 * (confidence / 100)
    
    return round(league_score + bp_score + confidence_score, 1)


def build_accumulators(predictions):
    """
    Build accumulators using ONLY highest quality matches
    ENSURES NO DUPLICATE MATCHES ACROSS ACCUMULATORS
    Compatible with existing main.py
    """
    
    if len(predictions) < 2:
        return {}
    
    # Calculate quality score and set odds for each prediction
    for p in predictions:
        p['quality_score'] = calculate_quality_score(p)
        
        play = p.get('play', '')
        if 'Home Win' in play:
            p['odds'] = p.get('home_odds', 1.50)
        elif 'Draw' in play:
            p['odds'] = p.get('draw_odds', 1.50)
        else:
            p['odds'] = 1.50
    
    # Filter high quality picks
    quality_picks = [p for p in predictions if p.get('quality_score', 0) >= MIN_QUALITY_SCORE]
    
    print(f"\n🎯 Quality Filter:")
    print(f"   Total predictions: {len(predictions)}")
    print(f"   High quality (≥{MIN_QUALITY_SCORE}): {len(quality_picks)}")
    print(f"   Excluded (poor quality): {len(predictions) - len(quality_picks)}")
    
    if len(quality_picks) < 2:
        print("   ⚠️ Not enough high quality picks for accumulators")
        return {}
    
    # Sort by quality score (highest first)
    sorted_picks = sorted(quality_picks, key=lambda x: x['quality_score'], reverse=True)
    
    print(f"\n🏆 TOP QUALITY PICKS (from ALL matches, no bias):")
    for i, p in enumerate(sorted_picks[:10], 1):
        quality_emoji = "🔥" if p['quality_score'] >= 80 else "✅" if p['quality_score'] >= 70 else "🟡" if p['quality_score'] >= 60 else "⚠️"
        print(f"   {i}. {quality_emoji} {p['blueprint']}: {p['match'][:45]} (Quality: {p['quality_score']})")
    
    accumulators = {}
    used_matches = set()  # Tracks all matches already used
    
    def get_unused():
        """Return only matches NOT already used in previous accumulators"""
        return [p for p in sorted_picks if p['match'] not in used_matches]
    
    # 2 ODDS ACCUMULATOR (2-3 matches)
    available = get_unused()
    for n in [2, 3]:
        if len(available) >= n:
            for combo in combinations(available, n):
                total = 1
                for m in combo:
                    total *= m['odds']
                if 1.8 <= total <= 2.5:
                    accumulators['2_ODDS'] = {
                        'matches': list(combo),
                        'odds': round(total, 2),
                        'avg_quality': round(sum(m['quality_score'] for m in combo) / n, 1)
                    }
                    for m in combo:
                        used_matches.add(m['match'])
                    break
        if '2_ODDS' in accumulators:
            break
    
    # 4 ODDS ACCUMULATOR (4 matches) - uses ONLY unused matches
    available = get_unused()
    if len(available) >= 4:
        for combo in combinations(available[:12], 4):
            total = 1
            for m in combo:
                total *= m['odds']
            if 3.5 <= total <= 5.0:
                accumulators['4_ODDS'] = {
                    'matches': list(combo),
                    'odds': round(total, 2),
                    'avg_quality': round(sum(m['quality_score'] for m in combo) / 4, 1)
                }
                for m in combo:
                    used_matches.add(m['match'])
                break
    
    # 7 ODDS ACCUMULATOR (5 matches) - uses ONLY unused matches
    available = get_unused()
    if len(available) >= 5:
        for combo in combinations(available[:15], 5):
            total = 1
            for m in combo:
                total *= m['odds']
            if 6.0 <= total <= 8.5:
                accumulators['7_ODDS'] = {
                    'matches': list(combo),
                    'odds': round(total, 2),
                    'avg_quality': round(sum(m['quality_score'] for m in combo) / 5, 1)
                }
                for m in combo:
                    used_matches.add(m['match'])
                break
    
    # 10 ODDS ACCUMULATOR (5-6 matches) - uses ONLY unused matches
    available = get_unused()
    for n in [5, 6]:
        if len(available) >= n:
            for combo in combinations(available[:20], n):
                total = 1
                for m in combo:
                    total *= m['odds']
                if 9.0 <= total <= 12.0:
                    accumulators['10_ODDS'] = {
                        'matches': list(combo),
                        'odds': round(total, 2),
                        'avg_quality': round(sum(m['quality_score'] for m in combo) / n, 1)
                    }
                    for m in combo:
                        used_matches.add(m['match'])
                    break
        if '10_ODDS' in accumulators:
            break
    
    # Final verification - NO DUPLICATES
    all_matches = []
    for name, acc in accumulators.items():
        for match in acc['matches']:
            all_matches.append(match['match'])
    
    if len(all_matches) != len(set(all_matches)):
        print("\n❌ ERROR: Duplicate matches found across accumulators!")
    else:
        print(f"\n✅ Verified: {len(all_matches)} UNIQUE matches across all accumulators")
    
    return accumulators
