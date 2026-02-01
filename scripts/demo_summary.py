#!/usr/bin/env python3
"""
Quick demo summary showing what the system has collected.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

def main():
    print("🎯 Gastown News Agents - Demo Summary\n")
    print("=" * 60)
    
    # Check raw data
    today = datetime.now().strftime('%Y-%m-%d')
    raw_dir = Path('data/raw') / today
    
    if raw_dir.exists():
        print(f"\n📰 Today's Scrape ({today}):")
        total = 0
        for json_file in sorted(raw_dir.glob('*.json')):
            category = json_file.stem.replace('_', ' ')
            with open(json_file, 'r') as f:
                articles = json.load(f)
                count = len(articles) if isinstance(articles, list) else 0
                total += count
                if count > 0:
                    print(f"   ✅ {category}: {count} article(s)")
                    if articles and isinstance(articles, list):
                        first = articles[0]
                        title = first.get('title', 'N/A')[:70]
                        score = first.get('relevance_score', 'N/A')
                        print(f"      📄 {title}...")
                        if score != 'N/A':
                            print(f"      ⭐ Relevance: {score:.2f}")
        print(f"\n   📊 Total: {total} articles")
    else:
        print(f"\n⚠️  No data found for today ({today})")
        print("   Run: python scripts/run_daily_scrape.py")
    
    # Check processed data
    processed_dir = Path('data/processed')
    if processed_dir.exists():
        week_files = list(processed_dir.glob('week-*.json'))
        if week_files:
            print(f"\n📦 Processed Weeks: {len(week_files)}")
            for week_file in sorted(week_files, reverse=True)[:3]:
                week_id = week_file.stem.replace('week-', '')
                with open(week_file, 'r') as f:
                    data = json.load(f)
                    story_count = len(data.get('stories', []))
                    print(f"   ✅ Week {week_id}: {story_count} stories")
    
    # Check approved data
    approved_dir = Path('data/approved')
    if approved_dir.exists():
        week_dirs = list(approved_dir.glob('week-*'))
        if week_dirs:
            print(f"\n✅ Approved Content: {len(week_dirs)} week(s)")
            for week_dir in sorted(week_dirs, reverse=True)[:3]:
                week_id = week_dir.name.replace('week-', '')
                files = list(week_dir.glob('*'))
                print(f"   📁 Week {week_id}: {len(files)} file(s)")
    
    print("\n" + "=" * 60)
    print("\n🚀 Next Steps:")
    print("   1. Continue daily scraping: python scripts/run_daily_scrape.py")
    print("   2. Run weekly consolidation: python scripts/run_weekly_consolidation.py")
    print("   3. Check logs: tail -f logs/*.log")
    print("   4. View website: cd website && npm run dev")

if __name__ == "__main__":
    main()
