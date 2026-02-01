from agents.base_agent import BaseAgent
from events.event_types import EventType, Event
from pathlib import Path
import os

class AudioAgent(BaseAgent):
    """Podcast generation using ElevenLabs"""
    
    def __init__(self, event_bus):
        super().__init__("audio_agent", event_bus)
        self._init_elevenlabs()
    
    def _init_elevenlabs(self):
        """Initialize ElevenLabs client"""
        try:
            from elevenlabs import set_api_key
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if api_key:
                set_api_key(api_key)
        except ImportError:
            self.logger.warning("ElevenLabs not installed. Audio generation will fail.")
        except Exception as e:
            self.logger.warning(f"Error initializing ElevenLabs: {e}")
    
    def _setup_event_listeners(self):
        # Subscribe to content formatted events
        import asyncio
        asyncio.create_task(self.event_bus.subscribe(EventType.CONTENT_FORMATTED, self.process))
    
    async def process(self, event: Event):
        """Generate podcast"""
        week_id = event.data.get('week_id')
        if not week_id:
            self.logger.error("No week_id in content formatted event")
            return
        
        self.logger.info(f"Generating audio for week {week_id}")
        
        try:
            # Load stories
            processed = self.storage.load_processed(week_id)
            if not processed or 'stories' not in processed:
                self.logger.error(f"No processed data found for week {week_id}")
                return
            
            # Convert stories to format for script generation
            story_dicts = []
            for story in processed['stories']:
                if isinstance(story, dict):
                    art = story.get('article', {})
                    story_dicts.append({
                        'title': art.get('title', ''),
                        'summary': art.get('summary', '')
                    })
            
            # Generate script
            script = await self.claude.generate_script(story_dicts, duration_mins=5)
            
            # Text to speech
            audio = await self._text_to_speech(script)
            
            # Save
            audio_path = f"data/approved/week-{week_id}/podcast.mp3"
            Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
            with open(audio_path, 'wb') as f:
                f.write(audio)
            
            await self.emit_event(EventType.AUDIO_GENERATED, {"week_id": week_id})
            self.logger.info(f"Audio generated for week {week_id}")
        except Exception as e:
            self.logger.error(f"Error generating audio: {e}")
            await self.emit_event(EventType.ERROR_OCCURRED, {"error": str(e), "agent": "audio"})
    
    async def _text_to_speech(self, script: str) -> bytes:
        """Convert script to audio using ElevenLabs"""
        try:
            from elevenlabs import generate, Voice, VoiceSettings
            
            voice_id = os.getenv("ELEVENLABS_VOICE_ID")
            if not voice_id:
                raise ValueError("ELEVENLABS_VOICE_ID not set")
            
            audio = generate(
                text=script,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(
                        stability=0.6,
                        similarity_boost=0.8,
                        style=0.7
                    )
                )
            )
            
            return audio
        except ImportError:
            raise ImportError("ElevenLabs library not installed")
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
            raise
