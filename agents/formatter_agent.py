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
        """Generate newsletter HTML using Claude with Ralph's Loop quality refinement"""
        # Convert to format Claude expects
        story_dicts = []
        for story in stories:
            if isinstance(story, dict):
                art = story.get('article', {})
                story_dicts.append({
                    'title': art.get('title', ''),
                    'category': art.get('category', ''),
                    'summary': art.get('summary', ''),
                    'url': art.get('url', '')
                })

        # Use Ralph's Loop for iterative quality improvement
        self.logger.info("Starting Ralph's Loop for newsletter content refinement")

        refined_content = await self.run_ralfs_loop(
            task=story_dicts,
            observe_func=self._observe_newsletter_state,
            reflect_func=self._reflect_on_newsletter_quality,
            act_func=self._improve_newsletter_content,
            max_iterations=3,
            confidence_threshold=0.85
        )

        content = refined_content.get('content', '')

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

    async def _observe_newsletter_state(self, task_or_result):
        """Observe: Generate or examine newsletter content"""
        if isinstance(task_or_result, list):
            # Initial generation
            self.logger.debug("Generating initial newsletter content")
            content = await self.claude.format_newsletter(task_or_result)
            return {
                'content': content,
                'stories': task_or_result,
                'iteration': 0
            }
        else:
            # Return the improved content from previous iteration
            return task_or_result

    async def _reflect_on_newsletter_quality(self, observation):
        """Reflect: Assess newsletter quality and provide improvement suggestions"""
        content = observation.get('content', '')
        stories = observation.get('stories', [])
        iteration = observation.get('iteration', 0)

        self.logger.debug(f"Reflecting on newsletter quality (iteration {iteration})")

        # Quality assessment prompt
        assessment_prompt = f"""Assess the quality of this Gen Z newsletter content and provide actionable feedback.

CONTENT TO REVIEW:
{content}

EVALUATION CRITERIA:
1. **Engagement** (0-10): Is it exciting and attention-grabbing?
2. **Clarity** (0-10): Are explanations clear and easy to understand?
3. **Tone** (0-10): Does it match "excited teenager with composure"?
4. **Relevance** (0-10): Does it explain why stories matter to Gen Z?
5. **Writing Quality** (0-10): Short sentences, active voice, good flow?

Provide your assessment in this exact JSON format:
{{
    "engagement_score": <0-10>,
    "clarity_score": <0-10>,
    "tone_score": <0-10>,
    "relevance_score": <0-10>,
    "writing_score": <0-10>,
    "overall_confidence": <0.0-1.0>,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "improvements": ["specific improvement 1", "specific improvement 2"]
}}

Return ONLY valid JSON, nothing else."""

        try:
            response = await self.claude.generate(assessment_prompt, max_tokens=1000, temperature=0.3)
            # Parse JSON response
            import json
            assessment = json.loads(response.strip())

            # Calculate average score and confidence
            avg_score = (
                assessment.get('engagement_score', 0) +
                assessment.get('clarity_score', 0) +
                assessment.get('tone_score', 0) +
                assessment.get('relevance_score', 0) +
                assessment.get('writing_score', 0)
            ) / 50.0  # Normalize to 0-1

            assessment['confidence'] = assessment.get('overall_confidence', avg_score)
            assessment['average_score'] = avg_score

            self.logger.info(
                f"Quality scores - Engagement: {assessment.get('engagement_score')}/10, "
                f"Clarity: {assessment.get('clarity_score')}/10, "
                f"Tone: {assessment.get('tone_score')}/10, "
                f"Overall confidence: {assessment['confidence']:.2f}"
            )

            return {
                **assessment,
                'content': content,
                'stories': stories,
                'iteration': iteration
            }
        except Exception as e:
            self.logger.warning(f"Failed to parse quality assessment: {e}, using default confidence")
            # Return high confidence to stop iteration on error
            return {
                'confidence': 0.9,
                'content': content,
                'stories': stories,
                'iteration': iteration,
                'improvements': []
            }

    async def _improve_newsletter_content(self, reflection):
        """Act: Generate improved newsletter based on reflection feedback"""
        content = reflection.get('content', '')
        stories = reflection.get('stories', [])
        improvements = reflection.get('improvements', [])
        weaknesses = reflection.get('weaknesses', [])
        iteration = reflection.get('iteration', 0)

        if not improvements:
            # No improvements needed, return as is
            return {
                'content': content,
                'stories': stories,
                'iteration': iteration + 1
            }

        self.logger.debug(f"Generating improved version (iteration {iteration + 1})")

        # Improvement prompt
        improvement_prompt = f"""Improve this Gen Z newsletter content based on specific feedback.

CURRENT CONTENT:
{content}

IDENTIFIED WEAKNESSES:
{chr(10).join(f"- {w}" for w in weaknesses)}

SPECIFIC IMPROVEMENTS TO MAKE:
{chr(10).join(f"- {imp}" for imp in improvements)}

REQUIREMENTS:
- Keep the same stories but improve the writing
- Make it MORE engaging and exciting for Gen Z
- Ensure tone is "excited teenager with composure"
- Use short sentences, active voice, occasional exclamation points
- Explain WHY each story matters to young people
- Maintain HTML-friendly formatting (use <div class="story"> for each story)

Generate the IMPROVED newsletter content following the feedback above."""

        improved_content = await self.claude.generate(
            improvement_prompt,
            max_tokens=3000,
            temperature=0.7
        )

        return {
            'content': improved_content,
            'stories': stories,
            'iteration': iteration + 1
        }
    
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
