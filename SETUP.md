# Setup Guide

## Initial Setup

1. **Clone/Navigate to project**
   ```bash
   cd gastown-news-agents
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install website dependencies**
   ```bash
   cd website
   npm install
   cd ..
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Required API Keys

- **Anthropic Claude**: Get from https://console.anthropic.com/
- **ElevenLabs**: Get from https://elevenlabs.io/
- **Twitter/X**: Get from https://developer.twitter.com/
- **Email (SMTP)**: Use Gmail app password or other SMTP service

## First Run

1. **Test scraper** (requires internet):
   ```bash
   python scripts/run_daily_scrape.py
   ```

2. **Test consolidation** (requires scraped data):
   ```bash
   python scripts/run_weekly_consolidation.py
   ```

3. **Test website**:
   ```bash
   cd website
   npm run dev
   ```

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### API Errors
- Verify all API keys in `.env` are correct
- Check API quotas and limits

### Scraping Errors
- Some sources may block automated access
- Check network connectivity
- Review logs in `logs/` directory

## Next Steps

1. Set up cron jobs for automated scheduling
2. Configure email for approval notifications
3. Customize content categories in `config/categories.yaml`
4. Add/remove news sources in `config/sources.yaml`
