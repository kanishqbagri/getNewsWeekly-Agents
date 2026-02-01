#!/usr/bin/env python3
"""Generate minimal audio with ElevenLabs (for accounts with limited credits)"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from dotenv import load_dotenv
import os

load_dotenv()

async def generate_minimal_audio():
    """Generate audio with minimal text to fit free tier"""
    print("🎙️  Generating Minimal Audio (Free Tier Compatible)\n")
    print("=" * 70)
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set")
        return False
    
    # Get available voice
    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    if not voices.voices:
        print("❌ No voices available")
        return False
    
    voice_id = voices.voices[0].voice_id
    voice_name = voices.voices[0].name
    print(f"✅ Using voice: {voice_name} ({voice_id})\n")
    
    # Create minimal script (under 5 characters for free tier)
    # Free tier typically has 5 credits, so we need a very short script
    script = "Welcome to Gen Z News. Top stories: AI advances, iPhone updates, and sports highlights. Thanks for listening."
    
    print(f"📝 Script ({len(script)} characters):")
    print(f"   {script}\n")
    
    print(f"⚠️  Note: Your account has 5 credits remaining.")
    print(f"   This script needs {len(script)} credits.")
    print(f"   You need to add more credits to your ElevenLabs account.\n")
    
    if len(script) > 5:
        print("❌ Script too long for available credits")
        print("\n💡 Solutions:")
        print("   1. Add credits to your ElevenLabs account")
        print("   2. Upgrade to a paid plan")
        print("   3. Use a shorter script (under 5 characters)")
        print("\n📋 To add credits:")
        print("   Visit: https://elevenlabs.io/app/settings/billing")
        return False
    
    try:
        print("🎤 Generating audio...")
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=script,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.6,
                similarity_boost=0.8,
                style=0.7
            )
        )
        
        audio = b"".join(audio_generator)
        
        # Save
        week_id = datetime.now().strftime('%Y-W%W')
        output_dir = Path(f"data/approved/week-{week_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "podcast.mp3"
        
        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        size = audio_path.stat().st_size
        print(f"\n✅ Audio generated!")
        print(f"   File: {audio_path.absolute()}")
        print(f"   Size: {size / 1024:.2f} KB")
        
        # Play
        import subprocess
        print("\n🎵 Playing audio...")
        subprocess.run(['afplay', str(audio_path)])
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if "quota" in str(e).lower():
            print("\n💡 Your ElevenLabs account needs more credits.")
            print("   Current limit: 5 credits")
            print("   Needed: More credits for full podcast")
            print("\n   Options:")
            print("   1. Add credits: https://elevenlabs.io/app/settings/billing")
            print("   2. Upgrade plan for more monthly credits")
            print("   3. Wait for monthly credit reset")
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_minimal_audio())
    sys.exit(0 if success else 1)
