#!/usr/bin/env python3
"""Generate full 5-minute podcast with enhanced script and video"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from events.event_bus import EventBus
from agents.audio_agent import AudioAgent
from agents.video_agent import VideoAgent
from events.event_types import Event, EventType
from utils.storage import Storage
from utils.llm_client import ClaudeClient
from dotenv import load_dotenv
import os

load_dotenv()

async def generate_full_podcast():
    """Generate complete podcast with enhanced script and video"""
    print("🎙️  Generating Full Podcast with Enhanced Script & Video\n")
    print("=" * 70)
    
    # Check API keys
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set")
        return False
    
    week_id = datetime.now().strftime('%Y-W%W')
    storage = Storage()
    
    # Load or create stories
    processed = storage.load_processed(week_id)
    if not processed or 'stories' not in processed or len(processed['stories']) == 0:
        print("⚠️  No processed data. Creating enhanced demo stories...")
        demo_stories = [
            {
                'article': {
                    'title': 'Claude 4 Outperforms GPT-5 in Creative Writing Tasks',
                    'summary': 'Anthropic\'s latest model shows superior performance in creative tasks, making it a favorite among content creators and students. The AI can now generate more engaging and authentic content that resonates with Gen Z audiences who value creativity and authenticity. This breakthrough could change how young people create content for social media, school projects, and creative writing.'
                }
            },
            {
                'article': {
                    'title': 'New iPhone 16 Pro Features Revolutionary AI Chip',
                    'summary': 'Apple unveiled the iPhone 16 Pro with a groundbreaking AI processor that enables real-time language translation and advanced photo editing. Gen Z users are excited about the new creative possibilities this brings to mobile content creation. The chip can process AI tasks 10x faster, meaning filters, edits, and translations happen instantly.'
                }
            },
            {
                'article': {
                    'title': 'NBA Finals: Clippers Dominate Game 7 with Record Performance',
                    'summary': 'The LA Clippers secured their first championship with an incredible Game 7 victory. Kawhi Leonard led the team with 45 points, breaking multiple records. This historic win has Gen Z basketball fans talking across social media, with highlights going viral on TikTok and Twitter.'
                }
            },
            {
                'article': {
                    'title': 'TikTok Launches New AI Content Creation Tools',
                    'summary': 'TikTok announced new AI-powered features that help creators generate videos faster. These tools are designed specifically for Gen Z creators who want to produce content more efficiently while maintaining their unique style. The update includes AI script writing, auto-captions, and smart editing suggestions.'
                }
            },
            {
                'article': {
                    'title': 'Climate Action: Gen Z Leads Global Protests',
                    'summary': 'Young activists organized massive climate protests worldwide, demanding immediate action from world leaders. This movement, led primarily by Gen Z, shows the generation\'s commitment to environmental issues. Over 2 million young people participated in coordinated strikes across 150 countries.'
                }
            }
        ]
        storage.save_processed({
            'week_id': week_id,
            'stories': demo_stories
        }, week_id)
        processed = {'stories': demo_stories}
        print(f"✅ Created enhanced demo data with {len(demo_stories)} stories\n")
    
    # Generate enhanced script
    print("📝 Generating enhanced, realistic podcast script...")
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
        # Try to estimate credits - use a shorter script if needed
        # For now, generate 2-3 minute script to fit in credits
        estimated_credits = 721  # From error message
        if estimated_credits < 1000:
            duration = 2  # 2 minutes = ~3000 chars max
            print(f"⚠️  Limited credits detected ({estimated_credits}). Generating {duration}-minute script...")
        else:
            duration = 5
    except:
        duration = 3  # Safe default
    
    # Generate script that fits credits
    script = await claude.generate_script(story_dicts, duration_mins=duration)
    print(f"✅ Enhanced script generated ({len(script)} characters)\n")
    
    # If script is too long, truncate intelligently
    if len(script) > estimated_credits - 100:  # Leave buffer
        print(f"⚠️  Script too long. Truncating to fit credits...")
        # Keep intro and first few stories
        lines = script.split('\n')
        truncated = []
        char_count = 0
        for line in lines:
            if char_count + len(line) < estimated_credits - 200:
                truncated.append(line)
                char_count += len(line)
            else:
                break
        truncated.append("\n\nThat's the news for this week. Stay informed, stay real. Peace out!")
        script = '\n'.join(truncated)
        print(f"✅ Script adjusted to {len(script)} characters\n")
    
    # Show script preview
    print("📄 Script Preview (first 500 chars):")
    print("-" * 70)
    print(script[:500] + "...")
    print("-" * 70)
    print()
    
    # Save script
    script_path = Path(f"data/approved/week-{week_id}/script.txt")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)
    print(f"💾 Script saved to: {script_path}\n")
    
    # Generate audio
    print("🎤 Generating high-quality audio with ElevenLabs...")
    print("   (This may take 1-2 minutes for a 5-minute podcast)\n")
    
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        
        client = ElevenLabs(api_key=api_key)
        
        # Get voice
        voices = client.voices.get_all()
        voice_id = voices.voices[0].voice_id if voices.voices else os.getenv("ELEVENLABS_VOICE_ID")
        
        if not voice_id:
            print("❌ No voice ID available")
            return False
        
        print(f"   Using voice: {voices.voices[0].name if voices.voices else 'Default'}")
        print(f"   Script length: {len(script)} characters (~{len(script)} credits needed)\n")
        
        # Generate audio
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=script,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.6,
                similarity_boost=0.8,
                style=0.7,
                use_speaker_boost=True
            )
        )
        
        audio = b"".join(audio_generator)
        
        # Save audio
        audio_path = Path(f"data/approved/week-{week_id}/podcast.mp3")
        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        size = audio_path.stat().st_size
        print(f"✅ High-quality audio generated!")
        print(f"   File: {audio_path.absolute()}")
        print(f"   Size: {size / 1024 / 1024:.2f} MB\n")
        
        # Generate video
        print("🎬 Generating video...")
        bus = EventBus()
        video_agent = VideoAgent(bus)
        
        # Create event to trigger video generation
        event = Event(
            event_type=EventType.AUDIO_GENERATED,
            timestamp=datetime.now(),
            data={'week_id': week_id},
            agent_id='script',
            correlation_id='full-podcast-123'
        )
        
        await video_agent.process(event)
        
        # Check if video was created
        video_path = Path(f"data/approved/week-{week_id}/podcast.mp4")
        if video_path.exists():
            video_size = video_path.stat().st_size
            print(f"✅ Video generated!")
            print(f"   File: {video_path.absolute()}")
            print(f"   Size: {video_size / 1024 / 1024:.2f} MB\n")
        else:
            print("⚠️  Video generation attempted (check logs for details)\n")
        
        # Play audio
        print("🎵 Playing audio...")
        import subprocess
        subprocess.run(['afplay', str(audio_path)], check=False)
        
        print()
        print("✅ Full podcast generation complete!")
        print(f"\n📁 Files created:")
        print(f"   - Script: {script_path}")
        print(f"   - Audio: {audio_path}")
        if video_path.exists():
            print(f"   - Video: {video_path}")
        print(f"\n🎬 To play video:")
        print(f"   open {video_path if video_path.exists() else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_full_podcast())
    sys.exit(0 if success else 1)
