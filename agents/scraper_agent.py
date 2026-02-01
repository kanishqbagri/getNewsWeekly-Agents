import asyncio
import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article as NewsArticle
from datetime import datetime
from typing import List, Dict
from agents.base_agent import BaseAgent
from events.event_types import EventType, Article
import yaml
from dateutil import parser as date_parser

class ScraperAgent(BaseAgent):
    """Daily news scraper with Ralf's Loop quality filtering"""
    
    def __init__(self, event_bus):
        super().__init__("scraper_agent", event_bus)
        self.sources = self._load_sources()
        self.categories = self._load_categories()
    
    def _load_sources(self) -> Dict:
        with open("config/sources.yaml", 'r') as f:
            return yaml.safe_load(f)['sources']
    
    def _load_categories(self) -> List:
        with open("config/categories.yaml", 'r') as f:
            return yaml.safe_load(f)['categories']
    
    def _setup_event_listeners(self):
        # Scraper runs on schedule, doesn't listen to events
        pass
    
    async def process(self, event):
        # Not used - scraper runs independently
        pass
    
    async def run_daily_scrape(self):
        """Main scraping workflow"""
        self.logger.info("Starting daily news scrape")
        all_articles = []
        
        for category_config in self.categories:
            category = category_config['name']
            self.logger.info(f"Scraping category: {category}")
            
            try:
                articles = await self.scrape_category(category)

                # Apply Ralf's Loop for quality filtering
                filtered = await self._apply_quality_filter(articles)
                self.logger.debug(f"Quality filter returned type: {type(filtered)}")

                # Ensure filtered is a list
                if not isinstance(filtered, list):
                    self.logger.warning(f"Filtered result is not a list: {type(filtered)}, converting...")
                    if isinstance(filtered, dict) and 'articles' in filtered:
                        filtered = filtered['articles']
                    else:
                        filtered = []

                self.logger.debug(f"After type check, filtered has {len(filtered)} articles")

                # Convert Article objects to dicts for storage
                articles_dicts = []
                for i, article in enumerate(filtered):
                    try:
                        if isinstance(article, Article):
                            # Convert dataclass to dict
                            article_dict = {
                                'title': article.title,
                                'summary': article.summary,
                                'url': article.url,
                                'publish_date': article.publish_date.isoformat() if hasattr(article.publish_date, 'isoformat') else str(article.publish_date),
                                'source': article.source,
                                'category': article.category,
                                'image_url': article.image_url,
                                'raw_content': article.raw_content,
                                'relevance_score': article.relevance_score
                            }
                            articles_dicts.append(article_dict)
                    except Exception as article_error:
                        self.logger.error(f"Error converting article {i}: {article_error}")
                        continue

                self.logger.debug(f"Converted {len(articles_dicts)} articles to dicts")

                # Save to storage
                self.storage.save_raw(
                    articles_dicts,
                    category.replace(" ", "_")
                )

                self.logger.debug("Saved to storage successfully")

                all_articles.extend(filtered)
                self.logger.info(f"Scraped {len(filtered)} articles from {category}")

            except Exception as e:
                import traceback
                self.logger.error(f"Error scraping {category}: {e}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Emit event
        await self.emit_event(EventType.NEWS_SCRAPED, {
            "total_articles": len(all_articles),
            "categories": len(self.categories),
            "date": datetime.now().isoformat()
        })
        
        self.logger.info(f"Daily scrape complete: {len(all_articles)} total articles")
    
    async def scrape_category(self, category: str) -> List[Article]:
        """Scrape all sources for a category"""
        articles = []
        sources = self.sources.get(category.replace(" ", "_"), [])
        
        for source in sources:
            try:
                if source.get('rss'):
                    source_articles = await self._scrape_rss(source['rss'], source['name'], category)
                else:
                    source_articles = await self._scrape_web(source['url'], source['name'], category)
                
                articles.extend(source_articles)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error scraping {source['name']}: {e}")
        
        return articles
    
    async def _scrape_rss(self, feed_url: str, source: str, category: str) -> List[Article]:
        """Parse RSS feed with enhanced content extraction"""
        articles = []

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Fetching RSS feed from {source} (attempt {attempt + 1})")
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    self.logger.warning(f"No entries found in RSS feed for {source}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return articles

                for entry in feed.entries[:15]:  # Increased to 15 per source
                    try:
                        # Extract full content if available
                        full_content = self._extract_full_content(entry)
                        summary = entry.get('summary', entry.get('description', ''))

                        # Try to fetch full article content using newspaper3k
                        article_url = entry.get('link', '')
                        if article_url and not full_content:
                            full_content = await self._extract_article_content(article_url)

                        # Use full content for summary if available
                        if full_content and len(full_content) > len(summary):
                            summary = full_content[:800]  # Increased from 500
                        else:
                            summary = summary[:800]

                        # Validate essential fields
                        title = entry.get('title', '').strip()
                        if not title or not article_url:
                            self.logger.debug(f"Skipping entry with missing title or URL from {source}")
                            continue

                        # Enhanced image extraction
                        image_url = self._extract_image(entry) or await self._find_article_image(article_url)

                        article = Article(
                            title=title,
                            summary=summary,
                            url=article_url,
                            publish_date=self._parse_date(entry.get('published')),
                            source=source,
                            category=category,
                            image_url=image_url,
                            raw_content=full_content or summary
                        )

                        # Validate article before adding
                        if self._validate_article(article):
                            articles.append(article)
                        else:
                            self.logger.debug(f"Article validation failed: {title[:50]}")

                    except Exception as e:
                        self.logger.warning(f"Error processing RSS entry from {source}: {e}")
                        continue

                self.logger.info(f"Successfully scraped {len(articles)} articles from {source}")
                break  # Success, exit retry loop

            except Exception as e:
                self.logger.error(f"RSS parse error for {source} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    # Try web scraping as fallback
                    self.logger.info(f"Falling back to web scraping for {source}")

        return articles

    def _extract_full_content(self, entry) -> str:
        """Extract full content from RSS entry"""
        # Try content:encoded first (full article)
        if 'content' in entry and entry.content:
            for content in entry.content:
                if content.get('type') == 'text/html' or content.get('type') == 'text/plain':
                    # Strip HTML tags
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content.value, 'lxml')
                    return soup.get_text(separator=' ', strip=True)
        return ""

    async def _extract_article_content(self, url: str) -> str:
        """Extract full article content using newspaper3k"""
        try:
            article = NewsArticle(url)
            article.download()
            article.parse()
            return article.text if article.text else ""
        except Exception as e:
            self.logger.debug(f"Could not extract full content from {url}: {e}")
            return ""

    async def _find_article_image(self, url: str) -> str:
        """Try to find article image from webpage"""
        try:
            article = NewsArticle(url)
            article.download()
            article.parse()
            return article.top_image if article.top_image else None
        except:
            return None

    def _validate_article(self, article: Article) -> bool:
        """Validate article has required fields and quality"""
        # Check required fields
        if not article.title or len(article.title) < 10:
            return False
        if not article.url or not article.url.startswith('http'):
            return False
        if not article.summary or len(article.summary) < 50:
            return False

        # Check publish date is recent (within 14 days)
        if article.publish_date:
            from datetime import datetime, timedelta, timezone
            if isinstance(article.publish_date, datetime):
                # Make datetime.now() timezone-aware if article date is aware
                now = datetime.now(timezone.utc) if article.publish_date.tzinfo else datetime.now()
                try:
                    age = now - article.publish_date
                    if age > timedelta(days=14):
                        self.logger.debug(f"Article too old: {article.title[:50]}")
                        return False
                except TypeError:
                    # If still can't compare, skip date check
                    pass

        return True
    
    async def _scrape_web(self, url: str, source: str, category: str) -> List[Article]:
        """Fallback web scraping using newspaper3k"""
        articles = []
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find article links (generic approach)
            links = soup.find_all('a', href=True)[:20]
            
            for link in links:
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = url + article_url
                
                try:
                    news_article = NewsArticle(article_url)
                    news_article.download()
                    news_article.parse()
                    
                    article = Article(
                        title=news_article.title or link.text[:100],
                        summary=news_article.summary[:500] if news_article.summary else news_article.text[:500],
                        url=article_url,
                        publish_date=news_article.publish_date or datetime.now(),
                        source=source,
                        category=category,
                        image_url=news_article.top_image
                    )
                    articles.append(article)
                    
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Web scrape error for {source}: {e}")
        
        return articles
    
    def _parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return datetime.now()
        try:
            return date_parser.parse(date_str)
        except:
            return datetime.now()
    
    def _extract_image(self, entry):
        """Extract image URL from RSS entry"""
        if 'media_content' in entry:
            return entry.media_content[0]['url']
        elif 'media_thumbnail' in entry:
            return entry.media_thumbnail[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.get('type', '').startswith('image'):
                    return link.get('href')
        return None
    
    async def _apply_quality_filter(self, articles: List[Article]) -> List[Article]:
        """Use enhanced Ralf's Loop to filter and validate quality articles"""

        if not articles:
            return articles

        async def observe(arts):
            """Observe: Validate data quality and prepare for scoring"""
            # Handle both list input (first iteration) and dict input (subsequent iterations)
            if isinstance(arts, dict):
                if 'articles' in arts:
                    arts = arts['articles']
                else:
                    arts = []

            validated = []
            quality_issues = []

            for art in arts:
                issues = []
                # Check data quality
                if not art.title or len(art.title) < 10:
                    issues.append("title_too_short")
                if not art.summary or len(art.summary) < 50:
                    issues.append("summary_too_short")
                if not art.url or not art.url.startswith('http'):
                    issues.append("invalid_url")
                if not art.image_url:
                    issues.append("no_image")

                if issues:
                    quality_issues.append({
                        "title": art.title[:50],
                        "issues": issues
                    })
                else:
                    validated.append(art)

            self.logger.info(
                f"Data quality check: {len(validated)}/{len(arts)} articles passed validation"
            )
            if quality_issues[:3]:  # Log first 3 issues
                self.logger.debug(f"Quality issues found: {quality_issues[:3]}")

            return {
                "articles": validated,
                "count": len(validated),
                "rejected": len(quality_issues),
                "quality_issues": quality_issues
            }

        async def reflect(observation):
            """Reflect: Score articles for Gen Z relevance with better batching"""
            articles_list = observation["articles"]
            scores = []

            # Score in batches to manage API calls
            batch_size = 30  # Increased from 20
            batches = [articles_list[i:i + batch_size] for i in range(0, len(articles_list), batch_size)]

            for batch_idx, batch in enumerate(batches):
                self.logger.debug(f"Scoring batch {batch_idx + 1}/{len(batches)} ({len(batch)} articles)")

                for article in batch:
                    try:
                        # Convert Article dataclass to dict for Claude
                        article_dict = {
                            'title': article.title,
                            'summary': article.summary,
                            'category': article.category
                        }
                        score = await self.claude.analyze_relevance(article_dict)
                        article.relevance_score = score
                        scores.append(score)
                    except Exception as e:
                        self.logger.warning(f"Error scoring article '{article.title[:50]}': {e}")
                        article.relevance_score = 0.5
                        scores.append(0.5)

                # Rate limit between batches
                if batch_idx < len(batches) - 1:
                    await asyncio.sleep(1)

            # Calculate statistics
            avg_score = sum(scores) / len(scores) if scores else 0
            high_quality = sum(1 for s in scores if s >= 0.7)
            medium_quality = sum(1 for s in scores if 0.5 <= s < 0.7)
            low_quality = sum(1 for s in scores if s < 0.5)

            self.logger.info(
                f"Relevance scores - Avg: {avg_score:.2f}, "
                f"High (≥0.7): {high_quality}, Medium (0.5-0.7): {medium_quality}, Low (<0.5): {low_quality}"
            )

            return {
                "confidence": avg_score,
                "scores": scores,
                "avg_score": avg_score,
                "high_quality_count": high_quality,
                "articles": articles_list
            }

        async def act(reflection):
            """Act: Filter articles and ensure quality threshold"""
            articles_list = reflection.get("articles", articles)
            avg_score = reflection.get("avg_score", 0.5)

            # Adaptive threshold based on average quality
            if avg_score >= 0.7:
                threshold = 0.6  # Higher bar when articles are generally good
            elif avg_score >= 0.5:
                threshold = 0.5  # Medium bar
            else:
                threshold = 0.4  # Lower bar when quality is generally low

            self.logger.info(f"Using relevance threshold: {threshold} (based on avg score: {avg_score:.2f})")

            # Filter articles above threshold
            filtered = [
                a for a in articles_list
                if hasattr(a, 'relevance_score') and a.relevance_score and a.relevance_score >= threshold
            ]

            # Ensure minimum articles (top 5 if filtered set is too small)
            if len(filtered) < 5 and articles_list:
                sorted_articles = sorted(
                    articles_list,
                    key=lambda x: getattr(x, 'relevance_score', 0),
                    reverse=True
                )
                filtered = sorted_articles[:max(5, len(filtered))]
                self.logger.info(f"Ensured minimum articles: increased from {len(filtered)} to {len(filtered)}")

            self.logger.info(f"Filtered {len(articles_list)} → {len(filtered)} articles (threshold: {threshold})")

            return {"articles": filtered, "threshold": threshold}

        result = await self.run_ralfs_loop(
            articles,
            observe,
            reflect,
            act,
            max_iterations=2,  # Increased to allow for refinement
            confidence_threshold=0.75
        )

        # Extract articles from result
        if isinstance(result, dict) and "articles" in result:
            return result["articles"]
        elif isinstance(result, list):
            return result
        else:
            return articles
