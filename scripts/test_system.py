#!/usr/bin/env python3
"""
Quick system test to verify all components are working.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

async def test_system():
    """Test all system components"""
    print("🧪 Testing Gastown News Agents System...\n")
    
    results = []
    
    # Test 1: API Keys
    print("1️⃣  Testing API Key Manager...")
    try:
        from utils.api_keys import APIKeyManager
        status = APIKeyManager.check_keys()
        if status.get('ANTHROPIC_API_KEY'):
            print("   ✅ API keys detected")
            results.append(True)
        else:
            print("   ❌ API keys missing")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 2: Claude Client
    print("\n2️⃣  Testing Claude Client...")
    try:
        from utils.llm_client import ClaudeClient
        client = ClaudeClient()
        print("   ✅ ClaudeClient initialized")
        results.append(True)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 3: Event Bus
    print("\n3️⃣  Testing Event Bus...")
    try:
        from events.event_bus import EventBus
        from events.event_types import Event, EventType
        from datetime import datetime
        import uuid
        
        bus = EventBus()
        test_event = Event(
            event_type=EventType.NEWS_SCRAPED,
            timestamp=datetime.now(),
            data={"test": True},
            agent_id="test",
            correlation_id=str(uuid.uuid4())
        )
        await bus.publish(test_event)
        print("   ✅ Event bus working")
        results.append(True)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 4: Storage
    print("\n4️⃣  Testing Storage...")
    try:
        from utils.storage import Storage
        storage = Storage()
        print("   ✅ Storage initialized")
        results.append(True)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 5: Agents
    print("\n5️⃣  Testing Agents...")
    try:
        from events.event_bus import EventBus
        from agents.scraper_agent import ScraperAgent
        from agents.consolidation_agent import ConsolidationAgent
        
        bus = EventBus()
        scraper = ScraperAgent(bus)
        consolidator = ConsolidationAgent(bus)
        print("   ✅ Agents initialized")
        results.append(True)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All systems operational! Ready to run.")
        return 0
    else:
        print("⚠️  Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_system())
    sys.exit(exit_code)
