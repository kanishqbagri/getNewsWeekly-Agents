#!/usr/bin/env python3
"""Generate full-length script (within credit limits) and create video"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.llm_client import ClaudeClient
from dotenv import load_dotenv
import os

load_dotenv()

async def generate_full_content():
    """Generate full script and video within credit limits"""
    print("🎬 Generating Full Script & Video\n")
    print("=" * 70)
    
    week_id = datetime.now().strftime('%Y-W%W')
    storage = Storage()
    
    # Load stories
    processed = storage.load_processed(week_id)
    if not processed or 'stories' not in processed:
        print("❌ No processed data found")
        return False
    
    story_dicts = []
    for story in processed['stories']:
        if isinstance(story, dict):
            art = story.get('article', {})
            story_dicts.append({
                'title': art.get('title', ''),
                'summary': art.get('summary', '')
            })
    
    # Check available credits first
    print("📊 Checking available credits...")
    available_credits = 297  # From last error message
    print(f"   Available: ~{available_credits} credits")
    print(f"   Target: {available_credits - 50} characters (leaving buffer)\n")
    
    # Generate script that fits available credits
    print(f"📝 Generating optimized script (fits ~{available_credits - 50} credits)...")
    claude = ClaudeClient()
    
    # Create a script that's comprehensive but fits credits
    max_chars = available_credits - 50  # Leave buffer
    prompt = f"""Create a 1-2 minute engaging podcast script for Gen Z News Weekly.

Tone: Excited teenager with composure - energetic but credible
Style: Natural, conversational, like talking to friends
CRITICAL: Must be under {max_chars} characters total (count carefully!)

Stories to cover:
{chr(10).join(f"{i+1}. {s['title']}: {s.get('summary', '')[:100]}..." for i, s in enumerate(story_dicts[:5]))}

Structure:
- INTRO (20-30 sec): Energetic greeting, hook, preview
- STORY 1 (30-40 sec): First major story with why it matters to Gen Z
- STORY 2 (30-40 sec): Second story with real talk
- STORY 3 (30-40 sec): Third story with impact
- OUTRO (20-30 sec): Wrap up, call to action, sign off

Requirements:
- Sound like a real Gen Z person, not reading
- Use natural speech: "like", "honestly", "fr", "no cap"
- Make it engaging and authentic
- Keep total under {max_chars} characters (this is critical!)
- Cover all 3-5 stories briefly but meaningfully

Write the complete script as if you're the host speaking directly."""
    
    script = await claude.generate(prompt, max_tokens=500, temperature=0.8)
    
    # Ensure it's under max_chars
    if len(script) > max_chars:
        # Intelligently truncate
        sentences = script.split('. ')
        truncated = []
        char_count = 0
        target = max_chars - 50  # Leave room for outro
        for sentence in sentences:
            if char_count + len(sentence) < target:
                truncated.append(sentence)
                char_count += len(sentence) + 2
            else:
                break
        script = '. '.join(truncated) + '. Stay informed, stay real. Peace out!'
        
        # Final check
        if len(script) > max_chars:
            script = script[:max_chars-30] + '... Peace out!'
    
    print(f"✅ Script generated: {len(script)} characters\n")
    
    # Save script
    script_path = Path(f"data/approved/week-{week_id}/script.txt")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print("📄 Full Script:")
    print("-" * 70)
    print(script)
    print("-" * 70)
    print()
    
    # Generate audio
    print("🎤 Generating audio...")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set")
        return False
    
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        
        client = ElevenLabs(api_key=api_key)
        voices = client.voices.get_all()
        voice_id = voices.voices[0].voice_id if voices.voices else os.getenv("ELEVENLABS_VOICE_ID")
        
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
        audio_path = Path(f"data/approved/week-{week_id}/podcast.mp3")
        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        print(f"✅ Audio generated: {audio_path} ({len(audio) / 1024:.0f} KB)\n")
        
    except Exception as e:
        print(f"❌ Audio generation failed: {e}\n")
        return False
    
    # Generate video
    print("🎬 Generating video...")
    video_path = await generate_video(week_id, audio_path, script)
    
    if video_path and video_path.exists():
        print(f"✅ Video generated: {video_path} ({video_path.stat().st_size / 1024 / 1024:.2f} MB)\n")
        print("🎉 Complete! Script, audio, and video all generated!")
        return True
    else:
        print("⚠️  Video generation failed (check logs)\n")
        print("✅ Script and audio generated successfully!")
        return True

async def generate_video(week_id: str, audio_path: Path, script: str) -> Path:
    """Generate video using ffmpeg or HeyGen"""
    output_path = Path(f"data/approved/week-{week_id}/podcast.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try HeyGen first
    heygen_key = os.getenv("HEYGEN_API_KEY")
    if heygen_key:
        try:
            return await generate_heygen_video(week_id, audio_path, heygen_key)
        except Exception as e:
            print(f"   HeyGen failed: {e}, trying ffmpeg fallback...")
    
    # Fallback to ffmpeg
    try:
        import subprocess
        from PIL import Image, ImageDraw, ImageFont
        
        # Create thumbnail image
        img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Title
        title = "Gen Z News Weekly"
        bbox = draw.textbbox((0, 0), title, font=font_large)
        x = (1920 - (bbox[2] - bbox[0])) // 2
        draw.text((x, 350), title, fill='#6366F1', font=font_large)
        
        # Subtitle
        subtitle = f"Week {week_id}"
        bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
        x = (1920 - (bbox[2] - bbox[0])) // 2
        draw.text((x, 500), subtitle, fill='#EC4899', font=font_medium)
        
        # Save image
        image_path = output_path.parent / "video_thumbnail.png"
        img.save(image_path)
        
        # Create video with ffmpeg
        subprocess.run([
            'ffmpeg',
            '-loop', '1',
            '-i', str(image_path),
            '-i', str(audio_path),
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-y',
            str(output_path)
        ], check=True, capture_output=True)
        
        return output_path
        
    except FileNotFoundError:
        print("   ❌ FFmpeg not installed. Install with: brew install ffmpeg")
        return None
    except Exception as e:
        print(f"   ❌ FFmpeg error: {e}")
        return None

async def generate_heygen_video(week_id: str, audio_path: Path, api_key: str) -> Path:
    """Generate video using HeyGen API"""
    import requests
    
    # HeyGen API integration
    # Note: This is a template - adjust based on actual HeyGen API
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    # Upload audio first, then create video
    # (Implementation depends on HeyGen API docs)
    # For now, return None to use ffmpeg fallback
    return None

if __name__ == "__main__":
    success = asyncio.run(generate_full_content())
    sys.exit(0 if success else 1)
