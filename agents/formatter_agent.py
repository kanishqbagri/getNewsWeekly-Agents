from agents.base_agent import BaseAgent
from events.event_types import EventType, Event
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
import asyncio

class FormatterAgent(BaseAgent):
    """Multi-format content formatter"""
    
    def __init__(self, event_bus):
        super().__init__("formatter_agent", event_bus)
    
    def _setup_event_listeners(self):
        # Subscribe to approval received events
        asyncio.create_task(self.event_bus.subscribe(EventType.APPROVAL_RECEIVED, self.process))
    
    async def process(self, event: Event):
        """Format approved content"""
        week_id = event.data.get('week_id')
        if not week_id:
            self.logger.error("No week_id in approval event")
            return
        
        self.logger.info(f"Formatting content for week {week_id}")
        
        try:
            # Load approved stories
            processed = self.storage.load_processed(week_id)
            if not processed or 'stories' not in processed:
                self.logger.error(f"No processed data found for week {week_id}")
                return
            
            # Generate formats
            newsletter = await self._format_newsletter(processed['stories'])
            twitter_thread = await self._format_twitter(processed['stories'])
            thumbnails = await self._generate_thumbnails(processed['stories'], week_id)
            
            # Save
            self.storage.save_approved(newsletter, week_id, "newsletter", "html")
            self.storage.save_approved(twitter_thread, week_id, "twitter", "json")
            
            await self.emit_event(EventType.CONTENT_FORMATTED, {"week_id": week_id})
            self.logger.info(f"Content formatted for week {week_id}")
        except Exception as e:
            self.logger.error(f"Error formatting content: {e}")
            await self.emit_event(EventType.ERROR_OCCURRED, {"error": str(e), "agent": "formatter"})
    
    async def _format_newsletter(self, stories):
        """Generate newsletter HTML using Claude"""
        # Convert to format Claude expects
        story_dicts = []
        for story in stories:
            if isinstance(story, dict):
                art = story.get('article', {})
                story_dicts.append({
                    'title': art.get('title', ''),
                    'category': art.get('category', ''),
                    'summary': art.get('summary', '')
                })
        
        content = await self.claude.format_newsletter(story_dicts)
        # Wrap in HTML template
        return f"""<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #6366F1; }}
        .story {{ margin: 20px 0; padding: 15px; background: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Gen Z News Digest</h1>
    {content}
</body>
</html>"""
    
    async def _format_twitter(self, stories):
        """Generate tweet thread"""
        top_stories = stories[:5]
        tweets = []
        
        # Hook tweet
        tweets.append({
            "text": f"This week was 🔥! Here's your Gen Z news rundown. Thread 👇",
            "position": 1
        })
        
        # Story tweets
        for i, story in enumerate(top_stories):
            if isinstance(story, dict):
                art = story.get('article', {})
                title = art.get('title', '')[:150]
                category = art.get('category', 'News')
                url = art.get('url', '')
                text = f"{category} Alert: {title}... {url}"
                tweets.append({"text": text[:250], "position": i + 2})
        
        return tweets
    
    async def _generate_thumbnails(self, stories, week_id):
        """Create thumbnail images"""
        thumbnails = []
        for i, story in enumerate(stories[:5]):
            if isinstance(story, dict):
                art = story.get('article', {})
                title = art.get('title', 'Untitled')[:60]
                
                # Create simple thumbnail
                img = Image.new('RGB', (1200, 630), color='#6366F1')
                draw = ImageDraw.Draw(img)
                
                # Try to use a font, fallback to default
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
                except:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
                
                # Draw title (wrapped)
                words = title.split()
                lines = []
                current_line = []
                for word in words:
                    if font:
                        test_line = ' '.join(current_line + [word])
                        bbox = draw.textbbox((0, 0), test_line, font=font)
                        if bbox[2] - bbox[0] < 1100:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word]
                    else:
                        if len(' '.join(current_line + [word])) < 50:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                
                y = 200
                for line in lines[:3]:  # Max 3 lines
                    if font:
                        draw.text((50, y), line, fill='white', font=font)
                    else:
                        draw.text((50, y), line, fill='white')
                    y += 60
                
                # Save thumbnail
                thumbnail_path = f"data/approved/week-{week_id}/thumbnail_{i}.png"
                Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)
                img.save(thumbnail_path)
                thumbnails.append(thumbnail_path)
        
        return thumbnails
