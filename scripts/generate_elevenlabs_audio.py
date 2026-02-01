#!/usr/bin/env python3
"""Generate high-quality audio using ElevenLabs"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from events.event_bus import EventBus
from agents.audio_agent import AudioAgent
from events.event_types import Event, EventType
from utils.storage import Storage
from utils.llm_client import ClaudeClient
from dotenv import load_dotenv
import os

load_dotenv()

async def generate_full_audio():
    """Generate full podcast audio using ElevenLabs"""
    print("🎙️  Generating High-Quality Audio with ElevenLabs\n")
    print("=" * 70)
    
    # Check API keys
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set in .env")
        print("   Get your key from: https://elevenlabs.io/")
        return False
    
    # If voice_id is placeholder, try to get a default voice
    if not voice_id or voice_id == "xxxxx":
        print("⚠️  ELEVENLABS_VOICE_ID not set or is placeholder")
        print("   Attempting to use a default voice...")
        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=api_key)
            voices = client.voices.get_all()
            # Try to find a good voice for Gen Z (young, energetic)
            for voice in voices.voices:
                if voice.name.lower() in ['rachel', 'antoni', 'sam', 'elli', 'domi']:
                    voice_id = voice.voice_id
                    print(f"   ✅ Using default voice: {voice.name} ({voice_id})")
                    break
            if not voice_id or voice_id == "xxxxx":
                # Use first available voice
                if voices.voices:
                    voice_id = voices.voices[0].voice_id
                    print(f"   ✅ Using first available voice: {voices.voices[0].name} ({voice_id})")
                else:
                    print("   ❌ No voices available")
                    return False
        except Exception as e:
            print(f"   ❌ Could not get voices: {e}")
            print("   Please set ELEVENLABS_VOICE_ID in .env")
            print("   Run: python scripts/list_elevenlabs_voices.py")
            return False
    
    print(f"✅ API Key: {'*' * 20}{api_key[-4:]}")
    print(f"✅ Voice ID: {voice_id}\n")
    
    # Get week data
    week_id = datetime.now().strftime('%Y-W%W')
    storage = Storage()
    
    # Load processed data or create demo
    processed = storage.load_processed(week_id)
    
    if not processed or 'stories' not in processed or len(processed['stories']) == 0:
        print("⚠️  No processed data found. Creating demo stories...")
        demo_stories = [
            {
                'article': {
                    'title': 'Claude 4 Outperforms GPT-5 in Creative Writing Tasks',
                    'summary': 'Anthropic\'s latest model shows superior performance in creative tasks, making it a favorite among content creators and students. The AI can now generate more engaging and authentic content that resonates with Gen Z audiences who value creativity and authenticity.'
                }
            },
            {
                'article': {
                    'title': 'New iPhone 16 Pro Features Revolutionary AI Chip',
                    'summary': 'Apple unveiled the iPhone 16 Pro with a groundbreaking AI processor that enables real-time language translation and advanced photo editing. Gen Z users are excited about the new creative possibilities this brings to mobile content creation.'
                }
            },
            {
                'article': {
                    'title': 'NBA Finals: Clippers Dominate Game 7 with Record Performance',
                    'summary': 'The LA Clippers secured their first championship with an incredible Game 7 victory. Kawhi Leonard led the team with 45 points, breaking multiple records. This historic win has Gen Z basketball fans talking across social media.'
                }
            },
            {
                'article': {
                    'title': 'TikTok Launches New AI Content Creation Tools',
                    'summary': 'TikTok announced new AI-powered features that help creators generate videos faster. These tools are designed specifically for Gen Z creators who want to produce content more efficiently while maintaining their unique style.'
                }
            },
            {
                'article': {
                    'title': 'Climate Action: Gen Z Leads Global Protests',
                    'summary': 'Young activists organized massive climate protests worldwide, demanding immediate action from world leaders. This movement, led primarily by Gen Z, shows the generation\'s commitment to environmental issues.'
                }
            }
        ]
        storage.save_processed({
            'week_id': week_id,
            'stories': demo_stories
        }, week_id)
        processed = {'stories': demo_stories}
        print(f"✅ Created demo data with {len(demo_stories)} stories\n")
    
    # Generate script using Claude
    print("📝 Generating podcast script with Claude AI...")
    claude = ClaudeClient()
    
    story_dicts = []
    for story in processed['stories']:
        if isinstance(story, dict):
            art = story.get('article', {})
            story_dicts.append({
                'title': art.get('title', ''),
                'summary': art.get('summary', '')
            })
    
    # Check available credits first
    try:
        from elevenlabs.client import ElevenLabs
        temp_client = ElevenLabs(api_key=api_key)
        user_info = temp_client.user.get()
        available_credits = getattr(user_info, 'subscription', {}).get('character_count', 0) if hasattr(user_info, 'subscription') else 0
        print(f"📊 Available credits: {available_credits if available_credits > 0 else 'Unknown (checking...)'}")
    except:
        available_credits = 0
    
    # Generate script - use very short version if credits are limited
    if available_credits > 0 and available_credits < 100:
        print("⚠️  Limited credits detected. Creating minimal demo script...")
        # Create a very short demo script (under 5 characters for free tier)
        script = """Welcome to Gen Z News. This week: AI breakthroughs, new iPhone features, and NBA finals. That's the news. Thanks for listening."""
        print(f"✅ Using minimal demo script ({len(script)} characters)\n")
    else:
        # Generate shorter script for demo (30 seconds to save credits)
        script = await claude.generate(
            f"""Create a very short 30-second podcast intro script for Gen Z news. 
            Cover these stories briefly: {', '.join([s.get('title', '')[:50] for s in story_dicts[:3]])}
            Keep it under 200 characters. Make it energetic and Gen Z-friendly.""",
            max_tokens=100
        )
        print(f"✅ Script generated ({len(script)} characters)\n")
    
    # Estimate credits needed (roughly 1 credit per character)
    estimated_credits = len(script)
    print(f"📊 Estimated credits needed: ~{estimated_credits}")
    print(f"   (Script length: {len(script)} characters)\n")
    
    # Show script preview
    print("📄 Script Preview (first 300 chars):")
    print("-" * 70)
    print(script[:300] + "...")
    print("-" * 70)
    print()
    
    # Generate audio with ElevenLabs
    print("🎤 Converting to audio with ElevenLabs...")
    print("   (This may take 30-60 seconds)\n")
    
    try:
        # Use the correct ElevenLabs API
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        
        # Initialize client
        client = ElevenLabs(api_key=api_key)
        
        # Generate audio using text_to_speech.convert()
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=script,
            model_id="eleven_multilingual_v2",  # High quality model
            voice_settings=VoiceSettings(
                stability=0.6,
                similarity_boost=0.8,
                style=0.7,
                use_speaker_boost=True
            )
        )
        
        # Convert generator to bytes
        audio = b"".join(audio_generator)
        
        # Save audio
        output_dir = Path(f"data/approved/week-{week_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "podcast.mp3"
        
        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        size = audio_path.stat().st_size
        duration_estimate = len(script) / 150 * 60  # Rough estimate
        
        print(f"✅ High-quality audio generated!")
        print(f"   File: {audio_path.absolute()}")
        print(f"   Size: {size / 1024 / 1024:.2f} MB")
        print(f"   Estimated duration: ~{duration_estimate:.0f} seconds")
        print()
        
        # Play the audio
        print("🎵 Playing audio...")
        import subprocess
        subprocess.run(['afplay', str(audio_path)])
        
        print()
        print("✅ Audio generation complete!")
        print(f"   To play again: python scripts/play_audio.py")
        print(f"   Or: afplay {audio_path}")
        
        return True
        
    except ImportError:
        print("❌ ElevenLabs library not installed")
        print("   Install with: pip install elevenlabs")
        return False
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your ElevenLabs API key is valid")
        print("   2. Ensure you have credits in your ElevenLabs account")
        print("   3. Verify the voice ID is correct")
        print("   4. Check logs for more details")
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_full_audio())
    sys.exit(0 if success else 1)
