# Using Cursor's API Keys with Gastown News Agents

This guide explains how to leverage Cursor's API key configuration with the Gastown News Agents system.

## Quick Setup

### Option 1: Automatic Detection (Recommended)

The system automatically checks multiple sources for API keys:

1. **Environment variables** (set by Cursor or system)
2. **`.env` file** in the project root
3. **Cursor's settings** (if accessible)

Run the setup script:
```bash
source venv/bin/activate
python scripts/setup_cursor_keys.py
```

### Option 2: Manual Configuration

1. **Check Cursor Settings:**
   - Open Cursor Settings (Cmd/Ctrl + ,)
   - Go to "API Keys" or "Settings"
   - Look for Anthropic/Claude API key

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Add your API keys to `.env`:**
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ELEVENLABS_API_KEY=your-elevenlabs-key
   # ... etc
   ```

## How It Works

The system uses `utils/api_keys.py` which:

1. **Checks environment variables first** - Cursor may set these automatically
2. **Falls back to `.env` file** - Your local configuration
3. **Supports multiple key name formats** - Handles variations like:
   - `ANTHROPIC_API_KEY`
   - `CLAUDE_API_KEY`
   - `CURSOR_ANTHROPIC_API_KEY`

## Checking Key Status

Run the check script to see which keys are available:

```bash
python scripts/check_api_keys.py
```

This will show:
- ✅ Available keys
- ❌ Missing keys
- 💡 Next steps if keys are missing

## Cursor-Specific Configuration

### If Cursor Stores Keys in Settings

Cursor may store API keys in:
- `~/.cursor/settings.json`
- `~/Library/Application Support/Cursor/User/settings.json`
- Environment variables set by Cursor

The `setup_cursor_keys.py` script attempts to extract keys from these locations.

### Setting Keys in Cursor

1. Open Cursor Settings
2. Navigate to API Keys section
3. Add your Anthropic API key
4. The system should automatically detect it

## Environment Variable Priority

The system checks keys in this order:

1. Direct environment variable (e.g., `ANTHROPIC_API_KEY`)
2. Alternative names (e.g., `CLAUDE_API_KEY`)
3. `.env` file
4. Cursor configuration files

## Troubleshooting

### Keys Not Found

1. **Run the check script:**
   ```bash
   python scripts/check_api_keys.py
   ```

2. **Verify environment variables:**
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

3. **Check `.env` file exists:**
   ```bash
   ls -la .env
   ```

4. **Manually set in `.env`:**
   ```bash
   echo "ANTHROPIC_API_KEY=your-key" >> .env
   ```

### Cursor Keys Not Detected

If Cursor has API keys configured but they're not detected:

1. Check Cursor Settings > API Keys
2. Export them as environment variables:
   ```bash
   export ANTHROPIC_API_KEY=$(cursor-get-api-key anthropic)
   ```
3. Or manually copy them to `.env` file

## Security Notes

- ⚠️ Never commit `.env` file to git (it's in `.gitignore`)
- ✅ Use environment variables for production
- ✅ Keep API keys secure and rotate them regularly

## Next Steps

Once keys are configured:

1. **Test the setup:**
   ```bash
   python scripts/check_api_keys.py
   ```

2. **Run a test scrape:**
   ```bash
   python scripts/run_daily_scrape.py
   ```

3. **Check logs** if there are issues:
   ```bash
   tail -f logs/scraper_agent.log
   ```
