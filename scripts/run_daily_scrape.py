import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.scraper_agent import ScraperAgent
from events.event_bus import EventBus
from dotenv import load_dotenv

load_dotenv()

async def main():
    event_bus = EventBus()
    scraper = ScraperAgent(event_bus)
    await scraper.run_daily_scrape()

if __name__ == "__main__":
    asyncio.run(main())
