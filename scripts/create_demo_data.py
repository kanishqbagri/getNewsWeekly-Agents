#!/usr/bin/env python3
"""Create demo data for email preview"""
import json
from pathlib import Path
from datetime import datetime

# Create sample articles for demo
demo_articles = {
    'Sports': [
        {
            'title': 'NBA Finals: Clippers Dominate Game 7 with Record Performance',
            'summary': 'The LA Clippers secured their first championship with an incredible Game 7 victory. Kawhi Leonard led the team with 45 points, breaking multiple records. This win marks a historic moment for the franchise.',
            'url': 'https://example.com/nba-finals',
            'source': 'ESPN',
            'category': 'Sports',
            'relevance_score': 0.85,
            'publish_date': datetime.now().isoformat()
        }
    ],
    'Technology': [
        {
            'title': 'New iPhone 16 Pro Features Revolutionary AI Chip',
            'summary': 'Apple unveiled the iPhone 16 Pro with a groundbreaking AI processor that enables real-time language translation and advanced photo editing. Gen Z users are excited about the new creative possibilities.',
            'url': 'https://example.com/iphone-16',
            'source': 'TechCrunch',
            'category': 'Technology',
            'relevance_score': 0.90,
            'publish_date': datetime.now().isoformat()
        }
    ],
    'AI_News': [
        {
            'title': 'Claude 4 Outperforms GPT-5 in Creative Writing Tasks',
            'summary': 'Anthropic\'s latest model shows superior performance in creative tasks, making it a favorite among content creators and students. The AI can now generate more engaging and authentic content.',
            'url': 'https://example.com/claude-4',
            'source': 'VentureBeat AI',
            'category': 'AI News',
            'relevance_score': 0.88,
            'publish_date': datetime.now().isoformat()
        }
    ]
}

# Save demo data
today = datetime.now().strftime('%Y-%m-%d')
raw_dir = Path('data/raw') / today
raw_dir.mkdir(parents=True, exist_ok=True)

for category, articles in demo_articles.items():
    file_path = raw_dir / f'{category}.json'
    with open(file_path, 'w') as f:
        json.dump(articles, f, indent=2, default=str)

print(f'✅ Created demo data in {raw_dir}')
print(f'   Categories: {list(demo_articles.keys())}')
print(f'   Total articles: {sum(len(articles) for articles in demo_articles.values())}')
