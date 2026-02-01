import pytest
from agents.consolidation_agent import ConsolidationAgent
from events.event_bus import EventBus

@pytest.fixture
def consolidator():
    return ConsolidationAgent(EventBus())

def test_load_categories(consolidator):
    """Test category loading"""
    assert len(consolidator.categories) > 0
    assert consolidator.categories[0]['name'] == "Sports"
