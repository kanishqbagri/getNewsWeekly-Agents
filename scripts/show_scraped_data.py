#!/usr/bin/env python3
"""Display scraped data"""
import json
from pathlib import Path
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
raw_dir = Path('data/raw') / today

print('📰 SCRAPED DATA - Today\'s Articles\n')
print('=' * 70)

if raw_dir.exists():
    total = 0
    for json_file in sorted(raw_dir.glob('*.json')):
        category = json_file.stem.replace('_', ' ')
        with open(json_file, 'r') as f:
            articles = json.load(f)
            count = len(articles) if isinstance(articles, list) else 0
            total += count
            
            if count > 0:
                print(f'\n📂 {category.upper()} ({count} article(s)):')
                print('-' * 70)
                for i, article in enumerate(articles[:5], 1):  # Show first 5
                    print(f'\n  Article {i}:')
                    print(f'  Title: {article.get("title", "N/A")}')
                    print(f'  Source: {article.get("source", "N/A")}')
                    url = article.get("url", "N/A")
                    if len(url) > 80:
                        url = url[:80] + "..."
                    print(f'  URL: {url}')
                    summary = article.get("summary", "N/A")
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                    print(f'  Summary: {summary}')
                    if article.get('relevance_score'):
                        print(f'  ⭐ Relevance Score: {article.get("relevance_score"):.2f}')
    print(f'\n\n📊 TOTAL: {total} articles across all categories')
    
    if total == 0:
        print('\n⚠️  No articles found. The quality filter may have filtered them all out.')
        print('   Try running the scraper again or check the logs.')
else:
    print('❌ No data found for today')
    print('   Run: python scripts/run_daily_scrape.py')
