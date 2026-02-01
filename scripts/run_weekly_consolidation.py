import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.consolidation_agent import ConsolidationAgent
from events.event_bus import EventBus
from dotenv import load_dotenv

load_dotenv()

async def main():
    event_bus = EventBus()
    consolidator = ConsolidationAgent(event_bus)
    await consolidator.run_weekly_consolidation()

if __name__ == "__main__":
    asyncio.run(main())
