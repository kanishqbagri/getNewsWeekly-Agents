#!/usr/bin/env python3
"""Update website data file from processed stories"""
import json
from pathlib import Path
from datetime import datetime

def update_website_data():
    """Copy latest processed data to website public folder"""
    processed_dir = Path('data/processed')
    website_data_dir = Path('website/public/data')
    website_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Find latest week file
    week_files = sorted(processed_dir.glob('week-*.json'), reverse=True)
    
    if week_files:
        latest_file = week_files[0]
        week_id = latest_file.stem.replace('week-', '')
        
        # Load and transform data
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        # Create website-friendly format
        website_data = {
            'weekId': week_id,
            'stories': data.get('stories', []),
            'updated': datetime.now().isoformat()
        }
        
        # Save to website public folder
        output_file = website_data_dir / 'latest-stories.json'
        with open(output_file, 'w') as f:
            json.dump(website_data, f, indent=2, default=str)
        
        print(f'✅ Updated website data: {output_file}')
        print(f'   Week: {week_id}')
        print(f'   Stories: {len(website_data["stories"])}')
        return True
    else:
        print('⚠️  No processed data found')
        return False

if __name__ == "__main__":
    update_website_data()
