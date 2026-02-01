"""
API Key management utility that checks multiple sources for API keys.
Supports:
- Environment variables
- .env file
- Cursor's environment (if available)
"""
import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class APIKeyManager:
    """Manages API keys from multiple sources"""
    
    # Common environment variable names that might be used
    KEY_MAPPINGS = {
        'ANTHROPIC_API_KEY': [
            'ANTHROPIC_API_KEY',
            'CLAUDE_API_KEY',
            'CURSOR_ANTHROPIC_API_KEY',
            'ANTHROPIC_KEY'
        ],
        'ELEVENLABS_API_KEY': [
            'ELEVENLABS_API_KEY',
            'ELEVENLABS_KEY',
            'CURSOR_ELEVENLABS_API_KEY'
        ],
        'ELEVENLABS_VOICE_ID': [
            'ELEVENLABS_VOICE_ID',
            'ELEVENLABS_VOICE'
        ],
        'TWITTER_API_KEY': [
            'TWITTER_API_KEY',
            'TWITTER_CONSUMER_KEY',
            'CURSOR_TWITTER_API_KEY'
        ],
        'TWITTER_API_SECRET': [
            'TWITTER_API_SECRET',
            'TWITTER_CONSUMER_SECRET',
            'CURSOR_TWITTER_API_SECRET'
        ],
        'TWITTER_ACCESS_TOKEN': [
            'TWITTER_ACCESS_TOKEN',
            'CURSOR_TWITTER_ACCESS_TOKEN'
        ],
        'TWITTER_ACCESS_SECRET': [
            'TWITTER_ACCESS_SECRET',
            'CURSOR_TWITTER_ACCESS_SECRET'
        ],
        'TWITTER_BEARER_TOKEN': [
            'TWITTER_BEARER_TOKEN',
            'TWITTER_BEARER',
            'CURSOR_TWITTER_BEARER_TOKEN'
        ],
    }
    
    @classmethod
    def get_key(cls, key_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get API key from multiple sources, checking in order:
        1. Direct environment variable (key_name)
        2. Alternative environment variable names
        3. .env file (already loaded by dotenv)
        
        Args:
            key_name: Standard key name (e.g., 'ANTHROPIC_API_KEY')
            default: Default value if not found
            
        Returns:
            API key value or None
        """
        # First, try the exact key name
        value = os.getenv(key_name)
        if value:
            return value
        
        # Try alternative names
        if key_name in cls.KEY_MAPPINGS:
            for alt_name in cls.KEY_MAPPINGS[key_name]:
                value = os.getenv(alt_name)
                if value:
                    return value
        
        return default
    
    @classmethod
    def get_all_keys(cls) -> Dict[str, Optional[str]]:
        """Get all API keys"""
        return {
            'ANTHROPIC_API_KEY': cls.get_key('ANTHROPIC_API_KEY'),
            'ELEVENLABS_API_KEY': cls.get_key('ELEVENLABS_API_KEY'),
            'ELEVENLABS_VOICE_ID': cls.get_key('ELEVENLABS_VOICE_ID'),
            'TWITTER_API_KEY': cls.get_key('TWITTER_API_KEY'),
            'TWITTER_API_SECRET': cls.get_key('TWITTER_API_SECRET'),
            'TWITTER_ACCESS_TOKEN': cls.get_key('TWITTER_ACCESS_TOKEN'),
            'TWITTER_ACCESS_SECRET': cls.get_key('TWITTER_ACCESS_SECRET'),
            'TWITTER_BEARER_TOKEN': cls.get_key('TWITTER_BEARER_TOKEN'),
        }
    
    @classmethod
    def check_keys(cls) -> Dict[str, bool]:
        """Check which keys are available"""
        keys = cls.get_all_keys()
        return {key: value is not None and value != '' for key, value in keys.items()}
    
    @classmethod
    def print_status(cls):
        """Print status of all API keys"""
        status = cls.check_keys()
        print("\n📋 API Key Status:")
        print("=" * 50)
        for key, available in status.items():
            status_icon = "✅" if available else "❌"
            print(f"{status_icon} {key}: {'Available' if available else 'Not found'}")
        print("=" * 50)
        
        # Show which keys are critical
        critical_keys = ['ANTHROPIC_API_KEY']
        missing_critical = [key for key in critical_keys if not status.get(key)]
        if missing_critical:
            print(f"\n⚠️  Missing critical keys: {', '.join(missing_critical)}")
        else:
            print("\n✅ All critical keys are available!")
