#!/usr/bin/env python3
"""Create demo audio using macOS say command (no API needed)"""
import subprocess
from pathlib import Path
from datetime import datetime

def create_demo_audio():
    """Create a demo podcast audio using macOS say command"""
    week_id = datetime.now().strftime('%Y-W%W')
    output_dir = Path(f'data/approved/week-{week_id}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'podcast.mp3'
    
    # Demo script
    script = """
    Welcome to Gen Z News Digest! This is your weekly podcast.
    
    This week's top stories include Claude 4 outperforming GPT-5 in creative writing,
    the new iPhone 16 Pro with revolutionary AI chip, and the NBA Finals where
    the Clippers dominated Game 7.
    
    Stay tuned for more updates next week!
    """
    
    print(f"🎙️  Creating demo audio for week {week_id}...")
    print(f"   Using macOS text-to-speech (say command)\n")
    
    # Use say command to create audio
    # Note: say creates .aiff by default, we'll convert or use it directly
    temp_file = output_dir / 'podcast.aiff'
    
    try:
        # Create audio with say command
        subprocess.run([
            'say',
            '-v', 'Samantha',  # Use a natural voice
            '-o', str(temp_file),
            script
        ], check=True)
        
        # Convert to MP3 if ffmpeg is available, otherwise keep as AIFF
        try:
            subprocess.run([
                'ffmpeg', '-i', str(temp_file),
                '-acodec', 'libmp3lame',
                '-ab', '128k',
                str(output_file),
                '-y'  # Overwrite if exists
            ], check=True, capture_output=True)
            temp_file.unlink()  # Remove temp file
            print(f"✅ Audio created: {output_file}")
            print(f"   Format: MP3")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Keep as AIFF if ffmpeg not available
            output_file = temp_file.with_suffix('.aiff')
            temp_file.rename(output_file)
            print(f"✅ Audio created: {output_file}")
            print(f"   Format: AIFF (install ffmpeg to convert to MP3)")
        
        size = output_file.stat().st_size
        print(f"   Size: {size / 1024:.2f} KB")
        print(f"\n🎵 Playing audio...")
        
        # Play the audio
        subprocess.run(['afplay', str(output_file)])
        
        return output_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating audio: {e}")
        return None
    except FileNotFoundError:
        print("❌ 'say' command not found. This script requires macOS.")
        return None

if __name__ == "__main__":
    audio_file = create_demo_audio()
    if audio_file:
        print(f"\n✅ Demo audio ready!")
        print(f"   File: {audio_file.absolute()}")
        print(f"\n💡 To play again: python scripts/play_audio.py")
