#!/usr/bin/env python3
"""Check ElevenLabs account status and credits"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("❌ ELEVENLABS_API_KEY not set")
    exit(1)

print(f"🔑 API Key (last 4): ...{api_key[-4:]}\n")

try:
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)
    
    print("📊 Checking account status...\n")
    
    # Get user info
    try:
        user = client.user.get()
        print(f"✅ Connected to ElevenLabs account")
        print(f"   User type: {type(user).__name__}")
        
        # Try to get subscription/credit info
        if hasattr(user, 'subscription'):
            sub = user.subscription
            print(f"\n📋 Subscription Info:")
            print(f"   Type: {getattr(sub, 'tier', 'Unknown')}")
            if hasattr(sub, 'character_count'):
                print(f"   Character count: {sub.character_count}")
            if hasattr(sub, 'character_limit'):
                print(f"   Character limit: {sub.character_limit}")
            if hasattr(sub, 'remaining_characters'):
                print(f"   Remaining: {getattr(sub, 'remaining_characters', 'N/A')}")
        
        # List all attributes
        print(f"\n📝 Available user attributes:")
        attrs = [x for x in dir(user) if not x.startswith('_')]
        for attr in attrs[:15]:
            try:
                value = getattr(user, attr)
                if not callable(value):
                    print(f"   {attr}: {value}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # Try to get voices
    print(f"\n🎤 Checking available voices...")
    try:
        voices = client.voices.get_all()
        print(f"   ✅ Found {len(voices.voices)} voices")
        if voices.voices:
            print(f"   First voice: {voices.voices[0].name} ({voices.voices[0].voice_id})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Try a test generation with minimal text
    print(f"\n🧪 Testing audio generation with 5 characters...")
    try:
        test_text = "Test."
        audio_gen = client.text_to_speech.convert(
            voice_id=voices.voices[0].voice_id if voices.voices else "test",
            text=test_text,
            model_id="eleven_multilingual_v2"
        )
        audio = b"".join(audio_gen)
        print(f"   ✅ Test successful! Generated {len(audio)} bytes")
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        print(f"   Error details: {str(e)[:200]}")
        
except ImportError:
    print("❌ ElevenLabs library not installed")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
