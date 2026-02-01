#!/usr/bin/env python3
"""Generate email HTML preview"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from events.event_bus import EventBus
from agents.consolidation_agent import ConsolidationAgent
from events.event_types import Article, RankedArticle
from utils.storage import Storage
from dotenv import load_dotenv

load_dotenv()

async def generate_email():
    print('\n📧 GENERATING EMAIL HTML OUTPUT\n')
    print('=' * 70)
    
    bus = EventBus()
    consolidator = ConsolidationAgent(bus)
    storage = Storage()
    
    # Get week data
    today = datetime.now()
    start = today - timedelta(days=7)
    weekly_data = storage.load_weekly_raw(start, today)
    
    if not weekly_data or sum(len(articles) for articles in weekly_data.values()) == 0:
        print('⚠️  No weekly data found. Using today\'s data for demo...')
        # Use today's data
        today_str = today.strftime('%Y-%m-%d')
        raw_dir = storage.base_path / 'raw' / today_str
        weekly_data = {}
        if raw_dir.exists():
            for json_file in raw_dir.glob('*.json'):
                category = json_file.stem
                with open(json_file, 'r') as f:
                    articles = json.load(f)
                    if articles and len(articles) > 0:
                        weekly_data[category] = articles
    
    if weekly_data and sum(len(articles) for articles in weekly_data.values()) > 0:
        # Create ranked stories
        ranked_stories = []
        rank = 1
        
        for category, articles in weekly_data.items():
            for art_dict in articles[:2]:  # Top 2 per category
                if isinstance(art_dict, dict):
                    try:
                        from dateutil import parser
                        pub_date_str = art_dict.get('publish_date', '')
                        if isinstance(pub_date_str, str):
                            try:
                                pub_date = parser.parse(pub_date_str)
                            except:
                                pub_date = datetime.now()
                        else:
                            pub_date = datetime.now()
                        
                        article = Article(
                            title=art_dict.get('title', 'Untitled'),
                            summary=art_dict.get('summary', 'No summary available')[:500],
                            url=art_dict.get('url', '#'),
                            publish_date=pub_date,
                            source=art_dict.get('source', 'Unknown'),
                            category=category.replace('_', ' '),
                            image_url=art_dict.get('image_url'),
                            relevance_score=art_dict.get('relevance_score', 0.7)
                        )
                        ranked_stories.append(RankedArticle(
                            article=article,
                            rank=rank,
                            category_rank=1,
                            importance_score=article.relevance_score or 0.7,
                            selection_reason=f'Top story in {category.replace("_", " ")}'
                        ))
                        rank += 1
                        if rank > 10:  # Limit to 10 stories
                            break
                    except Exception as e:
                        print(f'Error processing article: {e}')
                        continue
        
        if ranked_stories:
            # Generate HTML
            html = await consolidator._generate_report(ranked_stories)
            print(html)
            
            # Save it
            week_id = today.strftime('%Y-W%W')
            output_file = Path(f'email_preview_{week_id}.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f'\n\n✅ Email HTML saved to: {output_file.absolute()}')
            print(f'   Open in browser: open {output_file}')
        else:
            print('❌ No articles to generate email from')
    else:
        print('❌ No data available to generate email')
        print('   Run: python scripts/run_daily_scrape.py first')

if __name__ == "__main__":
    asyncio.run(generate_email())
