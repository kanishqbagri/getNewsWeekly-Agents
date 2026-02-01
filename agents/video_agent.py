from agents.base_agent import BaseAgent
from events.event_types import EventType, Event
from pathlib import Path
import os
import asyncio
import requests
import json

class VideoAgent(BaseAgent):
    """Video generation using HeyGen or similar services"""
    
    def __init__(self, event_bus):
        super().__init__("video_agent", event_bus)
        self._init_heygen()
    
    def _init_heygen(self):
        """Initialize HeyGen client"""
        self.heygen_api_key = os.getenv("HEYGEN_API_KEY")
        self.heygen_api_url = "https://api.heygen.com/v1"
        
        if not self.heygen_api_key:
            self.logger.warning("HEYGEN_API_KEY not set. Video generation will fail.")
        else:
            self.logger.info("HeyGen API key configured")
    
    def _setup_event_listeners(self):
        # Subscribe to audio generated events
        asyncio.create_task(self.event_bus.subscribe(EventType.AUDIO_GENERATED, self.process))
    
    async def process(self, event: Event):
        """Generate video for podcast"""
        week_id = event.data.get('week_id')
        if not week_id:
            self.logger.error("No week_id in audio generated event")
            return
        
        self.logger.info(f"Generating video for week {week_id}")
        
        try:
            # Check if audio exists
            audio_path = Path(f"data/approved/week-{week_id}/podcast.mp3")
            if not audio_path.exists():
                self.logger.error(f"Audio file not found: {audio_path}")
                return
            
            # Load script/stories for video context
            processed = self.storage.load_processed(week_id)
            if not processed:
                self.logger.warning(f"No processed data for week {week_id}, using minimal context")
            
            # Generate video
            video_path = await self._generate_video(week_id, audio_path, processed)
            
            if video_path:
                await self.emit_event(EventType.VIDEO_GENERATED, {"week_id": week_id})
                self.logger.info(f"Video generated for week {week_id}")
            else:
                self.logger.error("Video generation failed")
                
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            await self.emit_event(EventType.ERROR_OCCURRED, {"error": str(e), "agent": "video"})
    
    async def _generate_video(self, week_id: str, audio_path: Path, processed_data: dict) -> Path:
        """Generate video using HeyGen API"""
        if not self.heygen_api_key:
            self.logger.error("HeyGen API key not configured")
            return None
        
        try:
            # Option 1: HeyGen API (if available)
            return await self._generate_with_heygen(week_id, audio_path, processed_data)
        except Exception as e:
            self.logger.warning(f"HeyGen generation failed: {e}")
            # Fallback: Create video using ffmpeg with static image
            return await self._generate_simple_video(week_id, audio_path)
    
    async def _generate_with_heygen(self, week_id: str, audio_path: Path, processed_data: dict) -> Path:
        """Generate video using HeyGen API"""
        # HeyGen API integration
        # This is a placeholder - actual implementation depends on HeyGen API docs
        
        headers = {
            "X-API-KEY": self.heygen_api_key,
            "Content-Type": "application/json"
        }
        
        # Create video task
        # Note: Actual HeyGen API endpoints may vary
        payload = {
            "video_input": {
                "audio_url": str(audio_path.absolute()),  # Or upload first
                "avatar_id": "default",  # Or use a specific avatar
            },
            "caption": True,
            "dimension": {
                "width": 1920,
                "height": 1080
            }
        }
        
        # Make API call (this is a template - adjust based on actual HeyGen API)
        response = requests.post(
            f"{self.heygen_api_url}/video/generate",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            video_url = result.get('video_url')
            
            # Download video
            video_response = requests.get(video_url, timeout=300)
            video_path = Path(f"data/approved/week-{week_id}/podcast.mp4")
            video_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(video_path, 'wb') as f:
                f.write(video_response.content)
            
            return video_path
        else:
            raise Exception(f"HeyGen API error: {response.status_code} - {response.text}")
    
    async def _generate_simple_video(self, week_id: str, audio_path: Path) -> Path:
        """Generate simple video with static image + audio (fallback)"""
        import subprocess
        
        output_path = Path(f"data/approved/week-{week_id}/podcast.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple image for the video
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Add title
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        title = "Gen Z News Weekly"
        subtitle = f"Week {week_id}"
        
        # Draw title
        bbox = draw.textbbox((0, 0), title, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1920 - text_width) // 2
        y = 400
        draw.text((x, y), title, fill='#6366F1', font=font_large)
        
        # Draw subtitle
        bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
        text_width = bbox[2] - bbox[0]
        x = (1920 - text_width) // 2
        y = 500
        draw.text((x, y), subtitle, fill='#EC4899', font=font_medium)
        
        # Save image
        image_path = output_path.parent / "thumbnail.png"
        img.save(image_path)
        
        # Use ffmpeg to create video
        try:
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
            
            self.logger.info(f"Simple video created: {output_path}")
            return output_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"FFmpeg error: {e}")
            self.logger.info("FFmpeg not available. Install with: brew install ffmpeg")
            return None
