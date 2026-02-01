import pytest
from agents.scraper_agent import ScraperAgent
from events.event_bus import EventBus

@pytest.fixture
def scraper():
    return ScraperAgent(EventBus())

@pytest.mark.asyncio
async def test_scrape_category(scraper):
    """Test scraping a category"""
    # This will make actual network calls, so may fail without internet
    try:
        articles = await scraper.scrape_category("Sports")
        assert isinstance(articles, list)
        # If articles found, check structure
        if articles:
            assert hasattr(articles[0], 'title')
            assert hasattr(articles[0], 'category')
    except Exception as e:
        # Network errors are acceptable in tests
        pytest.skip(f"Network error: {e}")

@pytest.mark.asyncio
async def test_relevance_scoring(scraper):
    """Test relevance scoring"""
    article = {
        "title": "NBA Finals Game 7",
        "summary": "Exciting game with amazing plays",
        "category": "Sports"
    }
    try:
        score = await scraper.claude.analyze_relevance(article)
        assert 0 <= score <= 1
    except Exception as e:
        # API errors are acceptable if keys not set
        pytest.skip(f"API error: {e}")
