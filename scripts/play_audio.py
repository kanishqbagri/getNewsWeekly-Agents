#!/usr/bin/env python3
"""Play audio file or generate and play if not exists"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def find_audio_file():
    """Find the most recent audio file"""
    # Check approved directory
    approved_dir = Path('data/approved')
    if approved_dir.exists():
        audio_files = list(approved_dir.glob('week-*/podcast.mp3'))
        if audio_files:
            # Return most recent
            return sorted(audio_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    # Check website directory
    website_dir = Path('website/public/weeks')
    if website_dir.exists():
        audio_files = list(website_dir.glob('*/podcast.mp3'))
        if audio_files:
            return sorted(audio_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    return None

def play_audio(file_path):
    """Play audio file using system default player"""
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        print(f"❌ Audio file not found: {file_path}")
        return False
    
    print(f"🎵 Playing: {file_path.name}")
    print(f"   Location: {file_path}")
    print(f"   Size: {file_path.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    # Try different methods to play audio
    try:
        # macOS - use open command
        subprocess.run(['open', str(file_path)], check=True)
        print("✅ Audio opened in default player")
        return True
    except:
        try:
            # macOS - use afplay
            subprocess.run(['afplay', str(file_path)], check=True)
            print("✅ Audio playing with afplay")
            return True
        except:
            try:
                # Linux - use xdg-open
                subprocess.run(['xdg-open', str(file_path)], check=True)
                print("✅ Audio opened")
                return True
            except:
                print("❌ Could not play audio automatically")
                print(f"   Please open manually: {file_path}")
                return False

def main():
    """Main function"""
    print("🎙️  Audio Player for Gastown News Agents\n")
    
    # Check if specific file provided
    if len(sys.argv) > 1:
        audio_file = Path(sys.argv[1])
        if audio_file.exists():
            play_audio(audio_file)
            return
        else:
            print(f"❌ File not found: {audio_file}")
    
    # Find most recent audio file
    audio_file = find_audio_file()
    
    if audio_file:
        play_audio(audio_file)
    else:
        print("⚠️  No audio file found!")
        print("\n📋 To generate audio:")
        print("   1. python scripts/generate_demo_audio.py")
        print("   2. Or run full pipeline: python scripts/run_publishing_pipeline.py")
        print("\n💡 Make sure ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are set in .env")

if __name__ == "__main__":
    main()
