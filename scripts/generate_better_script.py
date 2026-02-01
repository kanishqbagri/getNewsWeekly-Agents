#!/usr/bin/env python3
"""Generate a better script that fits within available credits"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.llm_client import ClaudeClient
from dotenv import load_dotenv

load_dotenv()

async def generate_better_script():
    """Generate a comprehensive script within credit limits"""
    print("📝 Generating Better Script (Within Credit Limits)\n")
    print("=" * 70)
    
    week_id = datetime.now().strftime('%Y-W%W')
    storage = Storage()
    
    # Load stories
    processed = storage.load_processed(week_id)
    if not processed or 'stories' not in processed:
        print("❌ No processed data")
        return False
    
    story_dicts = []
    for story in processed['stories']:
        if isinstance(story, dict):
            art = story.get('article', {})
            story_dicts.append({
                'title': art.get('title', ''),
                'summary': art.get('summary', '')
            })
    
    # Available credits: ~297
    # Target: ~240 characters (safe buffer)
    max_chars = 240
    
    print(f"📊 Credit Limit: {max_chars} characters\n")
    
    claude = ClaudeClient()
    
    # Create a concise but complete script
    stories_text = '\n'.join([f"- {s['title']}" for s in story_dicts[:3]])
    
    prompt = f"""Write a concise 1-minute Gen Z news podcast script. 

CRITICAL: The script must be EXACTLY under {max_chars} characters total. Count every character including spaces.

Stories:
{stories_text}

Structure:
- Greeting: "Hey Gen Z! What's good?"
- Quick intro: "This week was wild"
- Story 1: One sentence about first story
- Story 2: One sentence about second story  
- Story 3: One sentence about third story
- Outro: "That's the news. Stay real. Peace out!"

Style: Energetic Gen Z host, natural speech
Keep it tight and punchy. Every word counts.

Return ONLY the script text, no markdown, no labels. Just the spoken words."""
    
    script = await claude.generate(prompt, max_tokens=200, temperature=0.8)
    
    # Clean up script
    script = script.strip()
    # Remove any markdown formatting
    script = script.replace('**', '').replace('*', '').replace('#', '')
    script = script.split('\n\n')[0] if '\n\n' in script else script
    
    # Ensure it fits
    if len(script) > max_chars:
        # Truncate intelligently
        words = script.split()
        truncated = []
        char_count = 0
        for word in words:
            if char_count + len(word) + 1 < max_chars - 20:
                truncated.append(word)
                char_count += len(word) + 1
            else:
                break
        script = ' '.join(truncated) + '. Stay real. Peace out!'
    
    print(f"✅ Script generated: {len(script)} characters\n")
    print("📄 Script Content:")
    print("-" * 70)
    print(script)
    print("-" * 70)
    print()
    
    # Save
    script_path = Path(f"data/approved/week-{week_id}/script.txt")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"💾 Saved to: {script_path}\n")
    
    # Generate audio
    print("🎤 Generating audio with this script...")
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    import os
    
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
        
        print(f"✅ Audio generated: {len(audio) / 1024:.0f} KB\n")
        
        # Generate video
        print("🎬 Generating video...")
        await generate_video_simple(week_id, audio_path)
        
        print("\n✅ Complete! Script, audio, and video generated!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def generate_video_simple(week_id: str, audio_path: Path):
    """Generate simple video with ffmpeg"""
    import subprocess
    from PIL import Image, ImageDraw
    
    output_path = Path(f"data/approved/week-{week_id}/podcast.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create thumbnail
    img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
    except:
        font = ImageFont.load_default()
    
    title = "Gen Z News Weekly"
    bbox = draw.textbbox((0, 0), title, font=font)
    x = (1920 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 400), title, fill='#6366F1', font=font)
    
    image_path = output_path.parent / "video_bg.png"
    img.save(image_path)
    
    # Create video
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
        str(output_path)
    ], check=True, capture_output=True)
    
    print(f"✅ Video: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    asyncio.run(generate_better_script())
