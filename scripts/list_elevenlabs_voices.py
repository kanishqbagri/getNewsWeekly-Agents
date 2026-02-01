#!/usr/bin/env python3
"""List available ElevenLabs voices"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("❌ ELEVENLABS_API_KEY not set")
    exit(1)

try:
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)
    
    print("🎤 Available ElevenLabs Voices:\n")
    voices = client.voices.get_all()
    
    for voice in voices.voices[:10]:  # Show first 10
        print(f"✅ {voice.name}")
        print(f"   ID: {voice.voice_id}")
        print(f"   Category: {voice.category}")
        print()
    
    # Suggest a good voice for Gen Z podcast
    print("\n💡 Recommended voices for Gen Z podcast:")
    print("   - Rachel (conversational, friendly)")
    print("   - Antoni (male, energetic)")
    print("   - Sam (male, clear)")
    print("   - Elli (female, young)")
    
except Exception as e:
    print(f"❌ Error: {e}")
