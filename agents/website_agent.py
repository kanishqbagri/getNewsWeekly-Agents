from agents.base_agent import BaseAgent
from events.event_types import EventType, Event
from pathlib import Path
import subprocess
import shutil
import json
import asyncio

class WebsiteAgent(BaseAgent):
    """Astro website publisher"""
    
    def __init__(self, event_bus):
        super().__init__("website_agent", event_bus)
        self.website_path = Path("website")
    
    def _setup_event_listeners(self):
        # Subscribe to ready to publish events
        asyncio.create_task(self.event_bus.subscribe(EventType.READY_TO_PUBLISH, self.process))
    
    async def process(self, event: Event):
        """Update and deploy website"""
        week_id = event.data.get('week_id')
        if not week_id:
            self.logger.error("No week_id in ready to publish event")
            return
        
        self.logger.info(f"Publishing website for week {week_id}")
        
        try:
            # Copy assets
            self._copy_assets(week_id)
            
            # Create page
            self._create_week_page(week_id)
            
            # Update index page
            self._update_index_page(week_id)
            
            # Build
            self.logger.info("Building Astro site...")
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=self.website_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.logger.error(f"Build failed: {result.stderr}")
                return
            
            # Deploy (if configured)
            deploy_cmd = self.config.get('website', {}).get('deploy_command')
            if deploy_cmd:
                self.logger.info("Deploying website...")
                subprocess.run(deploy_cmd.split(), cwd=self.website_path)
            
            await self.emit_event(EventType.WEBSITE_PUBLISHED, {"week_id": week_id})
            self.logger.info(f"Website published for week {week_id}")
        except Exception as e:
            self.logger.error(f"Error publishing website: {e}")
            await self.emit_event(EventType.ERROR_OCCURRED, {"error": str(e), "agent": "website"})
    
    def _copy_assets(self, week_id):
        """Copy audio and images to website"""
        src = Path(f"data/approved/week-{week_id}")
        dest = self.website_path / "public" / "weeks" / week_id
        dest.mkdir(parents=True, exist_ok=True)
        
        # Copy podcast
        podcast_src = src / "podcast.mp3"
        if podcast_src.exists():
            shutil.copy(podcast_src, dest / "podcast.mp3")
        
        # Copy thumbnails
        for thumb in src.glob("thumbnail_*.png"):
            shutil.copy(thumb, dest / thumb.name)
    
    def _create_week_page(self, week_id):
        """Create Astro page for this week"""
        # Load stories
        processed = self.storage.load_processed(week_id)
        stories = processed.get('stories', []) if processed else []
        
        # Generate page content
        stories_html = ""
        for story in stories:
            if isinstance(story, dict):
                art = story.get('article', {})
                stories_html += f"""
                <div class="story-card">
                    <h3>{art.get('title', 'Untitled')}</h3>
                    <p class="category">{art.get('category', 'News')}</p>
                    <p>{art.get('summary', '')[:200]}...</p>
                    <a href="{art.get('url', '#')}" target="_blank">Read more →</a>
                </div>
                """
        
        template = f"""---
const weekId = "{week_id}";
---
<BaseLayout title="Week {{weekId}}">
  <div class="week-header">
    <h1 class="text-4xl font-bold mb-4">Week {{weekId}}</h1>
    <audio controls class="w-full mb-8">
      <source src="/weeks/{{weekId}}/podcast.mp3" type="audio/mpeg">
      Your browser does not support the audio element.
    </audio>
  </div>
  
  <div class="stories-grid space-y-6">
    {stories_html}
  </div>
</BaseLayout>
"""
        
        page_path = self.website_path / "src" / "pages" / f"week-{week_id}.astro"
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(template)
    
    def _update_index_page(self, week_id):
        """Update main index page with latest week"""
        index_path = self.website_path / "src" / "pages" / "index.astro"
        if not index_path.exists():
            return
        
        content = index_path.read_text()
        # Simple update - add link to latest week
        if f"week-{week_id}" not in content:
            # This is a simplified update - in production, would use proper templating
            pass
