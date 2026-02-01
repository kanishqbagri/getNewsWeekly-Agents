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
        """Use enhanced Ralf's Loop for intelligent story selection and ranking"""

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

        self.logger.info(f"Starting ranking for {len(all_articles)} articles")

        async def observe(articles):
            """Observe: Remove duplicates and group by category"""
            # Detect and remove duplicates
            unique_articles = await self._remove_duplicates(articles)
            removed = len(articles) - len(unique_articles)
            if removed > 0:
                self.logger.info(f"Removed {removed} duplicate articles")

            # Group by category
            by_category = {}
            for a in unique_articles:
                by_category.setdefault(a.category, []).append(a)

            return {
                "articles": unique_articles,
                "by_category": by_category,
                "duplicates_removed": removed
            }

        async def reflect(observation):
            """Reflect: Assess diversity, balance, and quality of selection"""
            articles_list = observation["articles"]
            by_category = observation["by_category"]

            # Check category balance
            category_counts = {cat: len(arts) for cat, arts in by_category.items()}

            # Get requirements
            min_required = {c['name']: c['min_stories'] for c in self.categories}

            # Check coverage
            missing = [cat for cat, min_count in min_required.items()
                      if category_counts.get(cat, 0) < min_count]

            # Assess diversity within categories
            diversity_scores = {}
            for cat, arts in by_category.items():
                # Check if articles cover different topics (title similarity)
                if len(arts) > 1:
                    unique_topics = self._count_unique_topics(arts)
                    diversity_scores[cat] = unique_topics / len(arts)
                else:
                    diversity_scores[cat] = 1.0

            avg_diversity = sum(diversity_scores.values()) / len(diversity_scores) if diversity_scores else 0

            # Calculate quality metrics
            avg_relevance = sum(a.relevance_score or 0.5 for a in articles_list) / len(articles_list) if articles_list else 0
            high_quality = sum(1 for a in articles_list if (a.relevance_score or 0) >= 0.7)

            # Assess recency (newer articles preferred)
            recent_count = self._count_recent_articles(articles_list, days=3)
            recency_ratio = recent_count / len(articles_list) if articles_list else 0

            # Overall confidence
            balance_score = 0.3 if not missing else 0.0
            diversity_score = avg_diversity * 0.25
            quality_score = (high_quality / len(articles_list)) * 0.25 if articles_list else 0
            recency_score = recency_ratio * 0.2

            confidence = balance_score + diversity_score + quality_score + recency_score

            self.logger.info(
                f"Quality assessment - Diversity: {avg_diversity:.2f}, "
                f"Avg relevance: {avg_relevance:.2f}, Recent: {recent_count}/{len(articles_list)}, "
                f"Confidence: {confidence:.2f}"
            )

            if missing:
                self.logger.warning(f"Missing categories: {missing}")

            return {
                "confidence": min(confidence, 0.95),  # Cap at 0.95 to allow iteration
                "missing_categories": missing,
                "diversity_scores": diversity_scores,
                "avg_diversity": avg_diversity,
                "avg_relevance": avg_relevance,
                "articles": articles_list,
                "by_category": by_category
            }

        async def act(reflection):
            """Act: Rank stories using multi-factor algorithm"""
            articles_list = reflection.get("articles", all_articles)
            by_category = reflection.get("by_category", {})

            ranked = []
            rank = 1

            # Sort categories by priority
            sorted_categories = sorted(self.categories, key=lambda x: x['priority'])

            for cat_config in sorted_categories:
                cat_name = cat_config['name']
                cat_articles = by_category.get(cat_name, [])

                if not cat_articles:
                    continue

                # Enhanced ranking algorithm
                for article in cat_articles:
                    article.composite_score = self._calculate_composite_score(article)

                # Sort by composite score
                cat_articles.sort(key=lambda x: x.composite_score, reverse=True)

                # Take top N for this category
                target_stories = cat_config.get('min_stories', 2)
                top_n = min(target_stories, len(cat_articles))

                for i, article in enumerate(cat_articles[:top_n]):
                    reason = self._generate_selection_reason(article, i + 1, cat_name)
                    ranked.append(RankedArticle(
                        article=article,
                        rank=rank,
                        category_rank=i + 1,
                        importance_score=article.composite_score,
                        selection_reason=reason
                    ))
                    rank += 1

            # Final ranking across categories by composite score
            ranked.sort(key=lambda x: x.importance_score, reverse=True)

            # Update global ranks
            for i, r in enumerate(ranked):
                r.rank = i + 1

            # Limit total
            max_stories = self.config.get('agents', {}).get('consolidation', {}).get('max_total_stories', 15)
            final_ranked = ranked[:max_stories]

            self.logger.info(f"Final selection: {len(final_ranked)} stories from {len(ranked)} candidates")

            return final_ranked

        result = await self.run_ralfs_loop(
            all_articles,
            observe,
            reflect,
            act,
            max_iterations=3,  # Increased for better refinement
            confidence_threshold=0.85
        )

        return result if isinstance(result, list) else []

    async def _remove_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate articles using URL and title similarity"""
        seen_urls = set()
        unique = []

        for article in articles:
            # Check URL duplicates
            if article.url in seen_urls:
                continue

            # Check title similarity with existing articles
            is_duplicate = False
            for existing in unique:
                similarity = self._title_similarity(article.title, existing.title)
                if similarity > 0.85:  # 85% similar = duplicate
                    # Keep the one with higher relevance score
                    if (article.relevance_score or 0) > (existing.relevance_score or 0):
                        unique.remove(existing)
                        unique.append(article)
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_urls.add(article.url)
                unique.append(article)

        return unique

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate title similarity using simple word overlap"""
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _count_unique_topics(self, articles: List[Article]) -> int:
        """Count unique topics in a category based on title similarity"""
        if not articles:
            return 0

        clusters = []
        for article in articles:
            # Check if similar to existing cluster
            matched = False
            for cluster in clusters:
                if self._title_similarity(article.title, cluster[0].title) > 0.7:
                    cluster.append(article)
                    matched = True
                    break
            if not matched:
                clusters.append([article])

        return len(clusters)

    def _count_recent_articles(self, articles: List[Article], days: int = 3) -> int:
        """Count articles published within last N days"""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=days)
        count = 0

        for article in articles:
            if isinstance(article.publish_date, datetime):
                if article.publish_date >= cutoff:
                    count += 1

        return count

    def _calculate_composite_score(self, article: Article) -> float:
        """Calculate composite score from multiple factors"""
        from datetime import datetime, timedelta

        # Base relevance score (50% weight)
        relevance = (article.relevance_score or 0.5) * 0.5

        # Recency bonus (30% weight) - newer = better
        recency_score = 0.0
        if isinstance(article.publish_date, datetime):
            age_days = (datetime.now() - article.publish_date).days
            if age_days <= 1:
                recency_score = 0.3  # Published today or yesterday
            elif age_days <= 3:
                recency_score = 0.2  # Last 3 days
            elif age_days <= 7:
                recency_score = 0.1  # Last week
            else:
                recency_score = 0.0  # Older

        # Source credibility (10% weight) - major sources get bonus
        credible_sources = ['Reuters', 'AP News', 'BBC', 'ESPN', 'TechCrunch', 'The Verge', 'Bloomberg']
        credibility = 0.1 if article.source in credible_sources else 0.05

        # Content quality (10% weight) - longer summaries = more content
        quality = 0.1 if len(article.summary) > 300 else 0.05

        composite = relevance + recency_score + credibility + quality

        return min(composite, 1.0)  # Cap at 1.0

    def _generate_selection_reason(self, article: Article, category_rank: int, category: str) -> str:
        """Generate human-readable selection reason"""
        from datetime import datetime, timedelta

        reasons = []

        # Rank in category
        if category_rank == 1:
            reasons.append(f"Top story in {category}")
        else:
            reasons.append(f"#{category_rank} in {category}")

        # Relevance
        score = article.relevance_score or 0.5
        if score >= 0.8:
            reasons.append("highly relevant")
        elif score >= 0.7:
            reasons.append("relevant")

        # Recency
        if isinstance(article.publish_date, datetime):
            age = (datetime.now() - article.publish_date).days
            if age == 0:
                reasons.append("breaking news")
            elif age <= 2:
                reasons.append("recent")

        # Source
        credible = ['Reuters', 'AP News', 'BBC', 'ESPN', 'TechCrunch', 'Bloomberg']
        if article.source in credible:
            reasons.append(f"from {article.source}")

        return ", ".join(reasons)
    
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
