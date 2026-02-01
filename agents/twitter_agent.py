from agents.base_agent import BaseAgent
from events.event_types import EventType, Event
from pathlib import Path
import os
import time
import asyncio
import json

class TwitterAgent(BaseAgent):
    """Twitter/X publishing"""
    
    def __init__(self, event_bus):
        super().__init__("twitter_agent", event_bus)
        self.client = self._init_twitter()
    
    def _init_twitter(self):
        """Initialize Twitter client"""
        try:
            import tweepy
            
            bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
            consumer_key = os.getenv("TWITTER_API_KEY")
            consumer_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_token_secret = os.getenv("TWITTER_ACCESS_SECRET")
            
            if not all([bearer_token, consumer_key, consumer_secret, access_token, access_token_secret]):
                self.logger.warning("Twitter credentials not fully configured")
                return None
            
            return tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
        except ImportError:
            self.logger.warning("Tweepy not installed. Twitter publishing will fail.")
            return None
        except Exception as e:
            self.logger.warning(f"Error initializing Twitter client: {e}")
            return None
    
    def _setup_event_listeners(self):
        # Subscribe to ready to publish events
        asyncio.create_task(self.event_bus.subscribe(EventType.READY_TO_PUBLISH, self.process))
    
    async def process(self, event: Event):
        """Publish Twitter thread"""
        week_id = event.data.get('week_id')
        if not week_id:
            self.logger.error("No week_id in ready to publish event")
            return
        
        if not self.client:
            self.logger.error("Twitter client not initialized")
            return
        
        self.logger.info(f"Publishing Twitter thread for week {week_id}")
        
        try:
            # Load tweets
            tweets_path = f"data/approved/week-{week_id}/twitter.json"
            if not Path(tweets_path).exists():
                self.logger.error(f"Twitter data not found at {tweets_path}")
                return
            
            with open(tweets_path, 'r') as f:
                tweets = json.load(f)
            
            # Post thread
            prev_id = None
            for tweet in sorted(tweets, key=lambda x: x.get('position', 0)):
                text = tweet.get('text', '')
                if not text:
                    continue
                
                try:
                    response = self.client.create_tweet(
                        text=text,
                        in_reply_to_tweet_id=prev_id
                    )
                    prev_id = response.data['id']
                    self.logger.info(f"Posted tweet {tweet.get('position', 0)}")
                    await asyncio.sleep(10)  # Rate limiting
                except Exception as e:
                    self.logger.error(f"Error posting tweet: {e}")
                    break
            
            await self.emit_event(EventType.TWITTER_PUBLISHED, {"week_id": week_id})
            self.logger.info(f"Twitter thread published for week {week_id}")
        except Exception as e:
            self.logger.error(f"Error publishing to Twitter: {e}")
            await self.emit_event(EventType.ERROR_OCCURRED, {"error": str(e), "agent": "twitter"})
