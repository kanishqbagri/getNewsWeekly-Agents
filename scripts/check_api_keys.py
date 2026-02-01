#!/usr/bin/env python3
"""
Check API key availability from multiple sources.
This script helps identify which API keys are available.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_keys import APIKeyManager
from dotenv import load_dotenv

# Load .env if it exists
load_dotenv()

def main():
    """Check and display API key status"""
    print("🔍 Checking API keys from multiple sources...")
    print("   (Environment variables, .env file, Cursor settings)\n")
    
    APIKeyManager.print_status()
    
    # Get all keys (without showing values)
    keys = APIKeyManager.get_all_keys()
    available_count = sum(1 for v in keys.values() if v)
    total_count = len(keys)
    
    print(f"\n📊 Summary: {available_count}/{total_count} keys available")
    
    # Provide next steps
    if not keys.get('ANTHROPIC_API_KEY'):
        print("\n💡 Next steps:")
        print("   1. Check Cursor Settings > API Keys for Anthropic")
        print("   2. Or create .env file with: ANTHROPIC_API_KEY=your_key")
        print("   3. Or set environment variable: export ANTHROPIC_API_KEY=your_key")

if __name__ == "__main__":
    main()
