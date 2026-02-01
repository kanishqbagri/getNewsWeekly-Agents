import asyncio
from pathlib import Path
import sys
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.formatter_agent import FormatterAgent
from agents.audio_agent import AudioAgent
from agents.twitter_agent import TwitterAgent
from agents.website_agent import WebsiteAgent
from events.event_bus import EventBus
from events.event_types import Event, EventType
from dotenv import load_dotenv

load_dotenv()

async def main():
    event_bus = EventBus()
    
    # Initialize all agents
    formatter = FormatterAgent(event_bus)
    audio = AudioAgent(event_bus)
    twitter = TwitterAgent(event_bus)
    website = WebsiteAgent(event_bus)
    
    # Wait a moment for agents to subscribe
    await asyncio.sleep(1)
    
    # Get week_id from command line or use current week
    if len(sys.argv) > 1:
        week_id = sys.argv[1]
    else:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        week_id = start_of_week.strftime("%Y-W%W")
    
    print(f"Running publishing pipeline for week {week_id}")
    
    # Simulate approval received event
    await event_bus.publish(Event(
        event_type=EventType.APPROVAL_RECEIVED,
        timestamp=datetime.now(),
        data={"week_id": week_id},
        agent_id="manual",
        correlation_id=str(uuid.uuid4())
    ))
    
    # Wait for formatting and audio generation
    await asyncio.sleep(10)
    
    # Trigger publishing
    await event_bus.publish(Event(
        event_type=EventType.READY_TO_PUBLISH,
        timestamp=datetime.now(),
        data={"week_id": week_id},
        agent_id="manual",
        correlation_id=str(uuid.uuid4())
    ))
    
    # Wait for publishing to complete
    await asyncio.sleep(30)
    
    print("Publishing pipeline complete")

if __name__ == "__main__":
    from datetime import timedelta
    asyncio.run(main())
