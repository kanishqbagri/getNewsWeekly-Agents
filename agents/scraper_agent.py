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
                
                # Convert Article objects to dicts for storage
                articles_dicts = []
                for article in filtered:
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
                
                # Save to storage
                self.storage.save_raw(
                    articles_dicts,
                    category.replace(" ", "_")
                )
                
                all_articles.extend(filtered)
                self.logger.info(f"Scraped {len(filtered)} articles from {category}")
                
            except Exception as e:
                self.logger.error(f"Error scraping {category}: {e}")
        
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
        """Parse RSS feed"""
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # Limit to 10 per source
                article = Article(
                    title=entry.get('title', ''),
                    summary=entry.get('summary', entry.get('description', ''))[:500],
                    url=entry.get('link', ''),
                    publish_date=self._parse_date(entry.get('published')),
                    source=source,
                    category=category,
                    image_url=self._extract_image(entry)
                )
                articles.append(article)
                
        except Exception as e:
            self.logger.error(f"RSS parse error for {source}: {e}")
        
        return articles
    
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
        """Use Ralf's Loop to filter quality articles"""
        
        async def observe(arts):
            return {"articles": arts, "count": len(arts)}
        
        async def reflect(observation):
            # Use Claude to assess batch relevance
            scores = []
            articles_to_score = observation["articles"][:20]  # Limit Claude calls
            
            for article in articles_to_score:
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
                    self.logger.warning(f"Error scoring article {article.title}: {e}")
                    article.relevance_score = 0.5
                    scores.append(0.5)
            
            # Score remaining articles with default
            for article in observation["articles"][20:]:
                article.relevance_score = 0.5
            
            avg_score = sum(scores) / len(scores) if scores else 0
            return {
                "confidence": avg_score,
                "scores": scores
            }
        
        async def act(reflection):
            # Filter articles above threshold (lower threshold for demo)
            threshold = 0.4  # Lower threshold to allow more articles through
            filtered = [a for a in articles if hasattr(a, 'relevance_score') and a.relevance_score and a.relevance_score >= threshold]
            # If no articles pass, return top 3 by score
            if not filtered and articles:
                sorted_articles = sorted(articles, key=lambda x: getattr(x, 'relevance_score', 0.5), reverse=True)
                filtered = sorted_articles[:3]
            return {"articles": filtered}
        
        result = await self.run_ralfs_loop(
            articles,
            observe,
            reflect,
            act,
            max_iterations=1  # Simple filter, 1 iteration enough
        )
        
        # Extract articles from result
        if isinstance(result, dict) and "articles" in result:
            return result["articles"]
        elif isinstance(result, list):
            return result
        else:
            return articles
