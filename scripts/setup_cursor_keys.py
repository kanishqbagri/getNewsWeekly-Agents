#!/usr/bin/env python3
"""
Helper script to extract API keys from Cursor's configuration and set up .env file.
This script checks common locations where Cursor might store API keys.
"""
import os
import json
from pathlib import Path
import sys

def find_cursor_config():
    """Find Cursor configuration directory"""
    home = Path.home()
    
    # Common Cursor config locations
    possible_paths = [
        home / ".cursor" / "settings.json",
        home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json",
        home / ".config" / "Cursor" / "User" / "settings.json",
        home / ".cursor" / "config.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def extract_keys_from_cursor_config(config_path):
    """Extract API keys from Cursor's settings.json"""
    keys = {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Check for common key patterns in Cursor settings
        # Cursor might store keys in various formats
        if isinstance(config, dict):
            # Direct keys
            for key_name in ['anthropicApiKey', 'anthropic_api_key', 'ANTHROPIC_API_KEY']:
                if key_name in config:
                    keys['ANTHROPIC_API_KEY'] = config[key_name]
            
            # Check nested structures
            if 'apiKeys' in config:
                api_keys = config['apiKeys']
                if isinstance(api_keys, dict):
                    keys.update({
                        'ANTHROPIC_API_KEY': api_keys.get('anthropic') or api_keys.get('claude'),
                        'ELEVENLABS_API_KEY': api_keys.get('elevenlabs'),
                    })
            
            # Check for environment variable references
            if 'env' in config:
                env_vars = config['env']
                if isinstance(env_vars, dict):
                    keys.update({
                        k: v for k, v in env_vars.items() 
                        if 'API_KEY' in k or 'TOKEN' in k
                    })
                    
    except Exception as e:
        print(f"⚠️  Could not read Cursor config: {e}")
    
    return keys

def check_environment_variables():
    """Check for API keys in environment variables"""
    keys = {}
    env_vars = [
        'ANTHROPIC_API_KEY',
        'CLAUDE_API_KEY',
        'ELEVENLABS_API_KEY',
        'TWITTER_API_KEY',
        'TWITTER_BEARER_TOKEN',
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            keys[var] = value
    
    return keys

def create_env_file(keys, env_path):
    """Create or update .env file with found keys"""
    existing_keys = {}
    
    # Read existing .env if it exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    existing_keys[key] = value
    
    # Merge found keys with existing
    all_keys = {**existing_keys, **keys}
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write("# Gastown News Agents - API Keys\n")
        f.write("# Generated/updated by setup_cursor_keys.py\n\n")
        
        # Write all keys
        for key, value in all_keys.items():
            if value:  # Only write non-empty values
                f.write(f"{key}={value}\n")
            else:
                # Keep placeholder if no value found
                f.write(f"# {key}=xxxxx\n")
    
    return len([v for v in all_keys.values() if v])

def main():
    """Main setup function"""
    print("🔧 Setting up API keys from Cursor configuration...\n")
    
    env_path = Path(__file__).parent.parent / ".env"
    found_keys = {}
    
    # 1. Check Cursor config
    config_path = find_cursor_config()
    if config_path:
        print(f"✅ Found Cursor config at: {config_path}")
        cursor_keys = extract_keys_from_cursor_config(config_path)
        if cursor_keys:
            print(f"   Found {len(cursor_keys)} keys in Cursor config")
            found_keys.update(cursor_keys)
        else:
            print("   No API keys found in Cursor config")
    else:
        print("⚠️  Could not find Cursor configuration file")
        print("   Cursor may store API keys in Settings > API Keys")
    
    # 2. Check environment variables
    env_keys = check_environment_variables()
    if env_keys:
        print(f"✅ Found {len(env_keys)} keys in environment variables")
        found_keys.update(env_keys)
    
    # 3. Create/update .env file
    if found_keys:
        count = create_env_file(found_keys, env_path)
        print(f"\n✅ Created/updated .env file with {count} keys")
        print(f"   Location: {env_path}")
    else:
        print("\n⚠️  No API keys found. Creating .env template...")
        create_env_file({}, env_path)
        print(f"   Please add your API keys to: {env_path}")
        print("\n   To get API keys:")
        print("   - Anthropic: https://console.anthropic.com/")
        print("   - ElevenLabs: https://elevenlabs.io/")
        print("   - Twitter: https://developer.twitter.com/")
    
    print("\n💡 Tip: You can also set API keys in Cursor Settings > API Keys")
    print("   The system will automatically detect them from environment variables.")

if __name__ == "__main__":
    main()
