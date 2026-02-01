#!/usr/bin/env python3
"""Generate demo audio for testing"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from events.event_bus import EventBus
from agents.audio_agent import AudioAgent
from events.event_types import Event, EventType
from dotenv import load_dotenv

load_dotenv()

async def generate_demo_audio():
    """Generate a demo podcast audio file"""
    print("🎙️ Generating Demo Audio...\n")
    
    bus = EventBus()
    audio_agent = AudioAgent(bus)
    
    # Create demo stories data
    week_id = datetime.now().strftime('%Y-W%W')
    
    # Create processed data structure
    demo_stories = [
        {
            'article': {
                'title': 'Claude 4 Outperforms GPT-5 in Creative Writing Tasks',
                'summary': 'Anthropic\'s latest model shows superior performance in creative tasks, making it a favorite among content creators and students. The AI can now generate more engaging and authentic content.'
            }
        },
        {
            'article': {
                'title': 'New iPhone 16 Pro Features Revolutionary AI Chip',
                'summary': 'Apple unveiled the iPhone 16 Pro with a groundbreaking AI processor that enables real-time language translation and advanced photo editing. Gen Z users are excited about the new creative possibilities.'
            }
        },
        {
            'article': {
                'title': 'NBA Finals: Clippers Dominate Game 7',
                'summary': 'The LA Clippers secured their first championship with an incredible Game 7 victory. Kawhi Leonard led the team with 45 points, breaking multiple records.'
            }
        }
    ]
    
    # Save demo processed data
    from utils.storage import Storage
    storage = Storage()
    storage.save_processed({
        'week_id': week_id,
        'stories': demo_stories
    }, week_id)
    
    print(f"✅ Created demo data for week {week_id}")
    
    # Create event to trigger audio generation
    event = Event(
        event_type=EventType.CONTENT_FORMATTED,
        timestamp=datetime.now(),
        data={'week_id': week_id},
        agent_id='demo',
        correlation_id='demo-123'
    )
    
    print("🎤 Generating podcast audio...")
    print("   (This will use ElevenLabs API - make sure ELEVENLABS_API_KEY is set)\n")
    
    try:
        await audio_agent.process(event)
        
        # Check if file was created
        audio_path = Path(f"data/approved/week-{week_id}/podcast.mp3")
        if audio_path.exists():
            size = audio_path.stat().st_size
            print(f"\n✅ Audio generated successfully!")
            print(f"   Location: {audio_path.absolute()}")
            print(f"   Size: {size / 1024 / 1024:.2f} MB")
            print(f"\n📁 Full path: {audio_path.resolve()}")
        else:
            print(f"\n⚠️  Audio file not found at expected location: {audio_path}")
            print("   Check logs for errors")
            
    except Exception as e:
        print(f"\n❌ Error generating audio: {e}")
        print("\n💡 Make sure:")
        print("   1. ELEVENLABS_API_KEY is set in .env")
        print("   2. ELEVENLABS_VOICE_ID is set in .env")
        print("   3. You have ElevenLabs credits available")

if __name__ == "__main__":
    from events.event_types import Event
    import uuid
    asyncio.run(generate_demo_audio())
