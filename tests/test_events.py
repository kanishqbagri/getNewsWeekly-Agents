import pytest
import asyncio
from events.event_bus import EventBus
from events.event_types import Event, EventType
from datetime import datetime

@pytest.fixture
def event_bus():
    return EventBus()

@pytest.mark.asyncio
async def test_event_publish_subscribe(event_bus):
    """Test event publishing and subscribing"""
    received_events = []
    
    async def handler(event):
        received_events.append(event)
    
    await event_bus.subscribe(EventType.NEWS_SCRAPED, handler)
    
    test_event = Event(
        event_type=EventType.NEWS_SCRAPED,
        timestamp=datetime.now(),
        data={"test": "data"},
        agent_id="test",
        correlation_id="test-123"
    )
    
    await event_bus.publish(test_event)
    
    # Wait a moment for async processing
    await asyncio.sleep(0.1)
    
    assert len(received_events) == 1
    assert received_events[0].data["test"] == "data"
