from datetime import datetime, timedelta
from typing import List, Dict
from agents.base_agent import BaseAgent
from events.event_types import EventType, Article, RankedArticle
from utils.email_client import EmailClient
import yaml
import json
import os

class ConsolidationAgent(BaseAgent):
    """Weekly consolidation with Ralf's Loop for story selection"""
    
    def __init__(self, event_bus):
        super().__init__("consolidation_agent", event_bus)
        self.email_client = EmailClient()
        self.categories = self._load_categories()
    
    def _load_categories(self) -> List:
        with open("config/categories.yaml", 'r') as f:
            return yaml.safe_load(f)['categories']
    
    def _setup_event_listeners(self):
        # Runs on schedule, doesn't listen to events
        pass
    
    async def process(self, event):
        pass
    
    async def run_weekly_consolidation(self):
        """Main consolidation workflow"""
        self.logger.info("Starting weekly consolidation")
        
        # Get week date range (Monday to Friday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=4)  # Friday
        
        # Aggregate data
        weekly_data = await self._aggregate_weekly_data(start_of_week, end_of_week)
        
        # Rank stories with Ralf's Loop
        ranked_stories = await self._rank_with_ralfs_loop(weekly_data)
        
        # Generate report
        report_html = await self._generate_report(ranked_stories)
        
        # Save for approval
        week_id = start_of_week.strftime("%Y-W%W")
        self.storage.save_processed({
            "week_id": week_id,
            "stories": [self._serialize_ranked(r) for r in ranked_stories]
        }, week_id)
        
        # Send approval email
        recipient = self.config.get('email', {}).get('approval_recipient') or os.getenv("EMAIL_RECIPIENT")
        if recipient:
            self.email_client.send_approval_request(report_html, recipient)
        
        # Emit event
        await self.emit_event(EventType.APPROVAL_REQUESTED, {
            "week_id": week_id,
            "story_count": len(ranked_stories)
        })
        
        self.logger.info(f"Consolidation complete for week {week_id}")
    
    async def _aggregate_weekly_data(self, start: datetime, end: datetime) -> Dict:
        """Load all scraped data from the week"""
        return self.storage.load_weekly_raw(start, end)
    
    async def _rank_with_ralfs_loop(self, weekly_data: Dict) -> List[RankedArticle]:
        """Use Ralf's Loop to select and rank best stories"""
        
        # Convert to Article objects
        all_articles = []
        for category, articles in weekly_data.items():
            for art_dict in articles:
                try:
                    # Handle both dict and Article object
                    if isinstance(art_dict, dict):
                        # Convert datetime strings back to datetime
                        if 'publish_date' in art_dict and isinstance(art_dict['publish_date'], str):
                            from dateutil import parser
                            art_dict['publish_date'] = parser.parse(art_dict['publish_date'])
                        all_articles.append(Article(**art_dict))
                    else:
                        all_articles.append(art_dict)
                except Exception as e:
                    self.logger.warning(f"Error converting article: {e}")
                    continue
        
        async def observe(articles):
            # Group by category, count diversity
            by_category = {}
            for a in articles:
                by_category.setdefault(a.category, []).append(a)
            return {"articles": articles, "by_category": by_category}
        
        async def reflect(observation):
            # Use Claude to assess selection quality
            articles = observation["articles"]
            
            # Check if we have good category balance
            category_counts = {cat: len(arts) for cat, arts in observation["by_category"].items()}
            
            # Get minimum required per category
            min_required = {c['name']: c['min_stories'] for c in self.categories}
            
            # Check coverage
            missing = [cat for cat, min_count in min_required.items() 
                      if category_counts.get(cat, 0) < min_count]
            
            confidence = 0.9 if not missing else 0.5
            
            return {
                "confidence": confidence,
                "missing_categories": missing,
                "feedback": "Good balance" if not missing else f"Need more: {missing}"
            }
        
        async def act(reflection):
            # Rank stories by category priority
            ranked = []
            rank = 1
            
            # Sort categories by priority
            sorted_categories = sorted(self.categories, key=lambda x: x['priority'])
            
            for cat_config in sorted_categories:
                cat_name = cat_config['name']
                cat_articles = [a for a in all_articles if a.category == cat_name]
                
                # Sort by relevance score
                cat_articles.sort(key=lambda x: x.relevance_score or 0, reverse=True)
                
                # Take top N for this category
                top_n = min(cat_config.get('min_stories', 2), len(cat_articles))
                
                for i, article in enumerate(cat_articles[:top_n]):
                    ranked.append(RankedArticle(
                        article=article,
                        rank=rank,
                        category_rank=i + 1,
                        importance_score=article.relevance_score or 0.7,
                        selection_reason=f"Top story in {cat_name}"
                    ))
                    rank += 1
            
            # Limit total
            max_stories = self.config.get('agents', {}).get('consolidation', {}).get('max_total_stories', 15)
            return ranked[:max_stories]
        
        result = await self.run_ralfs_loop(
            all_articles,
            observe,
            reflect,
            act,
            max_iterations=2
        )
        
        return result if isinstance(result, list) else []
    
    async def _generate_report(self, ranked_stories: List[RankedArticle]) -> str:
        """Generate comprehensive HTML approval email"""
        week_id = datetime.now().strftime('%Y-W%W')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly News Digest Approval - Week {week_id}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #6366F1;
                    border-bottom: 3px solid #6366F1;
                    padding-bottom: 10px;
                }}
                .summary {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .story {{
                    margin: 25px 0;
                    padding: 20px;
                    border-left: 4px solid #6366F1;
                    background: #fafafa;
                    border-radius: 4px;
                }}
                .story-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }}
                .category {{
                    display: inline-block;
                    background: #6366F1;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .rank {{
                    color: #666;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .story h3 {{
                    margin: 10px 0;
                    color: #1a1a1a;
                    font-size: 1.3em;
                }}
                .story p {{
                    color: #555;
                    margin: 10px 0;
                }}
                .story-meta {{
                    display: flex;
                    gap: 15px;
                    margin-top: 15px;
                    font-size: 0.9em;
                    color: #777;
                }}
                .relevance-score {{
                    display: inline-block;
                    background: #10b981;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-weight: bold;
                }}
                .source {{
                    color: #6366F1;
                }}
                a {{
                    color: #6366F1;
                    text-decoration: none;
                    font-weight: 500;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .actions {{
                    margin-top: 30px;
                    padding: 20px;
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    border-radius: 4px;
                }}
                .actions h3 {{
                    margin-top: 0;
                    color: #856404;
                }}
                .actions code {{
                    background: #f8f9fa;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📰 Weekly News Digest - Approval Request</h1>
                
                <div class="summary">
                    <strong>Week:</strong> {week_id}<br>
                    <strong>Total Stories:</strong> {len(ranked_stories)}<br>
                    <strong>Categories:</strong> {', '.join(set(s.article.category for s in ranked_stories))}
                </div>
                
                <h2>Top Stories for This Week</h2>
        """
        
        for ranked in ranked_stories:
            art = ranked.article
            summary = art.summary[:300] + "..." if len(art.summary) > 300 else art.summary
            
            html += f"""
                <div class="story">
                    <div class="story-header">
                        <span class="category">{art.category}</span>
                        <span class="rank">Rank #{ranked.rank}</span>
                    </div>
                    <h3>{art.title}</h3>
                    <p>{summary}</p>
                    <div class="story-meta">
                        <span class="source">Source: {art.source}</span>
                        <span class="relevance-score">⭐ {ranked.importance_score:.2f}</span>
                        <span>Published: {art.publish_date.strftime('%Y-%m-%d') if hasattr(art.publish_date, 'strftime') else str(art.publish_date)[:10]}</span>
                    </div>
                    <p><a href="{art.url}" target="_blank">🔗 Read Full Article →</a></p>
                </div>
            """
        
        html += f"""
                <div class="actions">
                    <h3>📋 Approval Actions</h3>
                    <p><strong>To approve this week's digest:</strong></p>
                    <p><code>mkdir -p data/approved/week-{week_id} && touch data/approved/week-{week_id}/APPROVED.txt</code></p>
                    
                    <p><strong>To reject:</strong></p>
                    <p><code>mkdir -p data/approved/week-{week_id} && touch data/approved/week-{week_id}/REJECTED.txt</code></p>
                    
                    <p><strong>After approval, run:</strong></p>
                    <p><code>python scripts/run_publishing_pipeline.py {week_id}</code></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _serialize_ranked(self, ranked: RankedArticle) -> Dict:
        """Convert RankedArticle to dict"""
        return {
            "article": ranked.article.__dict__,
            "rank": ranked.rank,
            "category_rank": ranked.category_rank,
            "importance_score": ranked.importance_score,
            "selection_reason": ranked.selection_reason
        }
