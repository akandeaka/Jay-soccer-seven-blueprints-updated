# convert_football_data.py
import os
import re
import pandas as pd

def convert_openfootball_to_csv(data_path="football_data", output_file="matches.csv"):
    """Convert openfootball .txt files to a single CSV"""
    
    all_matches = []
    
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract matches with format: "Home vs Away, 2-1"
                    pattern = r'([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+),\s+(\d+)-(\d+)'
                    matches = re.findall(pattern, content)
                    
                    for match in matches:
                        home = match[0].strip()
                        away = match[1].strip()
                        home_score = int(match[2])
                        away_score = int(match[3])
                        
                        # Extract league name from path
                        league = os.path.basename(root) if root != data_path else 'unknown'
                        
                        all_matches.append({
                            'home_team': home,
                            'away_team': away,
                            'home_score': home_score,
                            'away_score': away_score,
                            'league': league,
                            'result': 'H' if home_score > away_score else 'A' if away_score > home_score else 'D'
                        })
                except:
                    continue
    
    if all_matches:
        df = pd.DataFrame(all_matches)
        df.to_csv(output_file, index=False)
        print(f"✅ Converted {len(df)} matches to {output_file}")
    else:
        print("❌ No matches found")

if __name__ == "__main__":
    convert_openfootball_to_csv()
