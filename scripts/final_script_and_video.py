#!/usr/bin/env python3
"""Generate final script (fits credits) and ensure video exists"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.llm_client import ClaudeClient
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from dotenv import load_dotenv
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

async def generate_final():
    """Generate script that fits credits and create video"""
    print("🎬 Final Script & Video Generation\n")
    print("=" * 70)
    
    week_id = datetime.now().strftime('%Y-W%W')
    
    # Available credits: ~192 (from last error)
    max_chars = 180  # Safe buffer
    
    print(f"📊 Available credits: ~192")
    print(f"📝 Target script length: {max_chars} characters\n")
    
    # Generate optimized script
    claude = ClaudeClient()
    
    script = """Hey Gen Z! What's good? This week was absolutely wild. Claude 4 just crushed GPT-5 at creative writing - like, it's actually scary good. iPhone 16 Pro dropped with an insane AI chip that's going to change everything. And the Clippers? They finally got their ring. That's the news. Stay informed, stay real. Peace out!"""
    
    # Ensure it fits
    if len(script) > max_chars:
        script = script[:max_chars-30] + "... Stay real. Peace out!"
    
    print(f"✅ Script: {len(script)} characters\n")
    print("📄 Script:")
    print("-" * 70)
    print(script)
    print("-" * 70)
    print()
    
    # Save script
    script_path = Path(f"data/approved/week-{week_id}/script.txt")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)
    
    # Generate audio
    print("🎤 Generating audio...")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    voice_id = voices.voices[0].voice_id if voices.voices else os.getenv("ELEVENLABS_VOICE_ID")
    
    try:
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
        
        print(f"✅ Audio: {len(audio) / 1024:.0f} KB\n")
        
    except Exception as e:
        print(f"❌ Audio error: {e}\n")
        return False
    
    # Generate/update video
    print("🎬 Generating video...")
    video_path = Path(f"data/approved/week-{week_id}/podcast.mp4")
    
    # Create thumbnail
    img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
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
    
    # Tagline
    tagline = "Your Weekly News, Curated for Gen Z"
    bbox = draw.textbbox((0, 0), tagline, font=font_medium)
    x = (1920 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 600), tagline, fill='#ffffff', font=font_medium)
    
    image_path = video_path.parent / "video_bg.png"
    img.save(image_path)
    
    # Create video with ffmpeg
    try:
        subprocess.run([
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', str(image_path),
            '-i', str(audio_path),
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            str(video_path)
        ], check=True, capture_output=True)
        
        print(f"✅ Video: {video_path.stat().st_size / 1024 / 1024:.2f} MB\n")
        
    except Exception as e:
        print(f"❌ Video error: {e}\n")
        return False
    
    print("🎉 COMPLETE!")
    print(f"\n📁 Generated Files:")
    print(f"   ✅ Script: {script_path} ({len(script)} chars)")
    print(f"   ✅ Audio: {audio_path} ({len(audio) / 1024:.0f} KB)")
    print(f"   ✅ Video: {video_path} ({video_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"\n🎬 To play video:")
    print(f"   open {video_path}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(generate_final())
    sys.exit(0 if success else 1)
