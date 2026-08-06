# results_validator.py
import re
import os
import json
import pandas as pd

class ResultsValidator:
    """Core validator to evaluate predictions, blueprints, and accumulators."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalizes team/match strings for accurate cross-matching."""
        if not name:
            return ""
        name = name.lower()
        name = re.sub(r'\b(fc|ac|utd|united|sv|vfb|sc|afc|cd|ud)\b', '', name)
        return re.sub(r'[^a-z0-9]', '', name).strip()

    def evaluate_play(self, play: str, home_score: int, away_score: int) -> bool:
        """Evaluates prediction conditions against final scores."""
        total = home_score + away_score
        play_lower = play.lower()

        if 'home win' in play_lower or '1' == play_lower:
            return home_score > away_score
        elif 'away win' in play_lower or '2' == play_lower:
            return away_score > home_score
        elif 'draw' in play_lower and 'or' not in play_lower:
            return home_score == away_score
        elif 'both teams to score' in play_lower or 'gg' in play_lower:
            return home_score > 0 and away_score > 0
        elif 'over 1.5' in play_lower:
            return total > 1
        elif 'over 2.5' in play_lower:
            return total > 2
        elif 'under 3.5' in play_lower:
            return total < 4
        elif 'under 2.5' in play_lower:
            return total < 3
        elif 'draw or under 2.5' in play_lower:
            return (home_score == away_score) or total < 3
        elif 'draw or gg' in play_lower:
            return (home_score == away_score) or (home_score > 0 and away_score > 0)
        return False

    def validate_predictions(self, predictions: list, actual_results_map: dict) -> list:
        """
        Validates all 85 predictions against actual match results.
        """
        validated_list = []

        for pred in predictions:
            match_name = pred.get('match', f"{pred.get('home_team', '')} vs {pred.get('away_team', '')}")
            blueprint_id = pred.get('blueprint_id', pred.get('blueprint', 'Unknown'))
            predicted_play = pred.get('play', pred.get('predicted_outcome', ''))
            
            norm_match = self.normalize_name(match_name)
            
            # Find matching result using key comparison
            actual = None
            for result_key, score_data in actual_results_map.items():
                norm_key = self.normalize_name(result_key)
                if norm_key in norm_match or norm_match in norm_key:
                    actual = score_data
                    break

            if actual and 'home_score' in actual and 'away_score' in actual:
                is_correct = self.evaluate_play(predicted_play, actual['home_score'], actual['away_score'])
                status = 'WIN' if is_correct else 'LOSS'
                score_str = f"{actual['home_score']}-{actual['away_score']}"
            else:
                is_correct = False
                status = 'PENDING'
                score_str = 'N/A'

            validated_list.append({
                'match': match_name,
                'blueprint': blueprint_id,
                'play': predicted_play,
                'actual_score': score_str,
                'status': status,
                'is_correct': is_correct
            })

        return validated_list

    def generate_blueprint_and_full_report(self, validated_records: list):
        """Generates comprehensive report with Blueprint performance breakdown."""
        total = len(validated_records)
        completed = [r for r in validated_records if r['status'] in ['WIN', 'LOSS']]
        total_completed = len(completed)
        wins = sum(1 for r in completed if r['is_correct'])
        overall_acc = (wins / total_completed * 100) if total_completed > 0 else 0.0

        # Blueprint performance accumulator
        bp_stats = {}
        for r in completed:
            bp = r['blueprint']
            if bp not in bp_stats:
                bp_stats[bp] = {'total': 0, 'wins': 0}
            bp_stats[bp]['total'] += 1
            if r['is_correct']:
                bp_stats[bp]['wins'] += 1

        # Build Full Report (For Email)
        report = f"====================================================\n"
        report += f" ⚽ FULL SYSTEM PERFORMANCE & BLUEPRINT VALIDATION\n"
        report += f"====================================================\n"
        report += f"Total Predictions Evaluated: {total}\n"
        report += f"Matches Finished: {total_completed}\n"
        report += f"Overall Win Rate: {overall_acc:.2f}% ({wins}/{total_completed})\n\n"

        report += "----------------------------------------------------\n"
        report += "📊 PERFORMANCE BY BLUEPRINT\n"
        report += "----------------------------------------------------\n"
        for bp, stats in sorted(bp_stats.items()):
            acc = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            report += f"• Blueprint {bp}: {acc:.1f}% Win Rate ({stats['wins']}/{stats['total']})\n"

        report += "\n----------------------------------------------------\n"
        report += "📋 DETAILED PREDICTION BREAKDOWN (ALL 85 MATCHES)\n"
        report += "----------------------------------------------------\n"
        for i, r in enumerate(validated_records, 1):
            report += f"{i:02d}. [{r['status']}] {r['match']} | BP: {r['blueprint']} | Play: {r['play']} | Score: {r['actual_score']}\n"

        return report, overall_acc, wins, total_completed
