import os
import anthropic
from typing import Dict, List, Any, Optional
import asyncio
from functools import wraps

def retry_on_error(max_retries=3, delay=1):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator

class ClaudeClient:
    """Wrapper for Anthropic Claude API"""
    
    def __init__(self):
        # Try to get API key from multiple sources
        # Import here to avoid circular dependency
        from utils.api_keys import APIKeyManager
        
        api_key = APIKeyManager.get_key("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please set it in .env file or environment variables. "
                "Cursor users: Check if Cursor has API keys configured in settings."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    @retry_on_error(max_retries=3)
    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using Claude"""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system:
            kwargs["system"] = system
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text
    
    async def analyze_relevance(self, article: Dict[str, Any]) -> float:
        """Assess article relevance for Gen Z (0-1 score)"""
        prompt = f"""Analyze this news article for relevance to Gen Z audiences (ages 16-26).
        
Title: {article['title']}
Summary: {article.get('summary', 'N/A')}
Category: {article['category']}

Rate relevance from 0.0 to 1.0 based on:
- Interest to young people
- Cultural relevance
- Impact on their lives
- Engagement potential

Return ONLY a number between 0.0 and 1.0, nothing else."""
        
        response = await self.generate(prompt, max_tokens=10)
        try:
            return float(response.strip())
        except:
            return 0.5
    
    async def rank_stories(self, stories: List[Dict]) -> List[Dict]:
        """Rank stories by importance using Claude"""
        prompt = f"""Rank these {len(stories)} news stories by importance for Gen Z readers.
        Consider: relevance, impact, engagement potential, timeliness.
        
Stories:
{chr(10).join(f"{i+1}. {s['title']} ({s['category']})" for i, s in enumerate(stories))}

Return a JSON array of story indices in ranked order (most important first).
Example: [3, 1, 5, 2, 4]"""
        
        response = await self.generate(prompt, max_tokens=200)
        # Parse JSON and reorder stories
        import json
        try:
            indices = json.loads(response.strip())
            return [stories[i-1] for i in indices if 0 < i <= len(stories)]
        except:
            return stories
    
    async def generate_script(self, stories: List[Dict], duration_mins: int = 5) -> str:
        """Generate realistic, engaging podcast script"""
        prompt = f"""Create a {duration_mins}-minute podcast script for "Gen Z News Weekly" - a real, engaging news podcast.

Tone: Excited teenager with composure - energetic but credible, like a real Gen Z host
Target: Gen Z listeners (ages 16-26)
Word count: ~{duration_mins * 150} words
Style: Natural, conversational, like talking to friends

Stories to cover:
{chr(10).join(f"{i+1}. {s['title']}: {s.get('summary', '')[:150]}..." for i, s in enumerate(stories[:7]))}

Script Structure:
- INTRO (30-45 sec): 
  * Energetic greeting: "Hey Gen Z! What's good?"
  * Hook: "This week was absolutely WILD"
  * Preview top 3 stories
  * Set the vibe

- STORY SEGMENTS ({duration_mins - 1.5} min total):
  For each story:
  * Natural transition: "Okay, so..."
  * Story headline with excitement
  * Why it matters to Gen Z specifically
  * Real talk/opinion: "And honestly? This is huge because..."
  * Smooth transition to next story

- OUTRO (30 sec):
  * Wrap up: "That's what's going on this week"
  * Call to action: "Follow us for more"
  * Sign off: "Stay informed, stay real. Peace out!"

Requirements:
- Sound like a real Gen Z person talking, not reading
- Use natural speech patterns: "like", "honestly", "no cap", "fr"
- Add personality and reactions
- Include brief pauses naturally
- Make it engaging and authentic
- Don't use [PAUSE] markers - just natural flow

Write the full script as if you're the host speaking directly to listeners."""
        
        return await self.generate(prompt, max_tokens=3000, temperature=0.8)
    
    async def format_newsletter(self, stories: List[Dict]) -> str:
        """Generate newsletter content"""
        prompt = f"""Write engaging newsletter content for these stories.

Tone: Excited teenager with composure
Audience: Gen Z
Format: HTML-friendly text (will be templated later)

Stories:
{chr(10).join(f"Title: {s['title']}{chr(10)}Category: {s['category']}{chr(10)}Summary: {s.get('summary', '')}{chr(10)}" for s in stories)}

For each story:
- Catchy headline
- 100-150 word summary in engaging style
- Why it matters to Gen Z

Use short sentences, active voice, occasional exclamation points (but not excessive)."""
        
        return await self.generate(prompt, max_tokens=3000)
