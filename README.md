# Gastown News Agents

Multi-agent news curation system for Gen Z audiences. This system autonomously scrapes, curates, and publishes news content across multiple formats including newsletters, podcasts, Twitter threads, and a modern website.

## Features

- **Daily News Scraping**: Automatically scrapes news from multiple sources across 6 categories
- **Intelligent Curation**: Uses Claude AI to rank and select the most relevant stories for Gen Z
- **Multi-Format Publishing**: Generates newsletters, podcasts, Twitter threads, and website content
- **Event-Driven Architecture**: Gastown pattern with event bus for agent communication
- **Quality Refinement**: Ralf's Loop for iterative quality improvement in critical agents
- **Autonomous Operation**: Runs on schedule with minimal human intervention

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Website dependencies
cd website
npm install
cd ..
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `ELEVENLABS_VOICE_ID`: Your ElevenLabs voice ID
- `TWITTER_API_KEY`, `TWITTER_API_SECRET`, etc.: Twitter/X API credentials
- `EMAIL_SENDER`, `EMAIL_PASSWORD`: Email credentials for approval notifications

### 3. Run Daily Scraper

```bash
python scripts/run_daily_scrape.py
```

This will scrape news from all configured sources and save to `data/raw/`.

### 4. Run Weekly Consolidation (Friday)

```bash
python scripts/run_weekly_consolidation.py
```

This will:
- Aggregate the week's news
- Rank stories using AI
- Send an approval email
- Save processed data to `data/processed/`

### 5. Approve and Publish

After receiving the approval email:

1. Review the stories in the email
2. Create approval file:
   ```bash
   mkdir -p data/approved/week-YYYY-WWW
   touch data/approved/week-YYYY-WWW/APPROVED.txt
   ```

3. Run publishing pipeline:
   ```bash
   python scripts/run_publishing_pipeline.py YYYY-WWW
   ```

This will generate:
- Newsletter HTML
- Podcast MP3
- Twitter thread
- Website content

## Scheduling

Add to crontab for automatic operation:

```bash
# Daily scrape at 9 AM
0 9 * * * cd /path/to/gastown-news-agents && /path/to/venv/bin/python scripts/run_daily_scrape.py

# Weekly consolidation Friday at 8 PM
0 20 * * 5 cd /path/to/gastown-news-agents && /path/to/venv/bin/python scripts/run_weekly_consolidation.py
```

## Architecture

### Event-Driven Pattern (Gastown)

Agents communicate via an event bus:
- `ScraperAgent` → `NEWS_SCRAPED`
- `ConsolidationAgent` → `APPROVAL_REQUESTED`
- `FormatterAgent` → `CONTENT_FORMATTED`
- `AudioAgent` → `AUDIO_GENERATED`
- `TwitterAgent` → `TWITTER_PUBLISHED`
- `WebsiteAgent` → `WEBSITE_PUBLISHED`

### Ralf's Loop

Quality refinement loop used in:
- **ScraperAgent**: Filters articles by Gen Z relevance
- **ConsolidationAgent**: Selects and ranks stories for weekly digest

### Agents

1. **ScraperAgent**: Daily news scraping from RSS feeds and web sources
2. **ConsolidationAgent**: Weekly aggregation and ranking
3. **FormatterAgent**: Multi-format content generation
4. **AudioAgent**: Podcast generation with ElevenLabs
5. **TwitterAgent**: Twitter/X thread publishing
6. **WebsiteAgent**: Astro website generation and deployment

## Configuration

### Categories

Edit `config/categories.yaml` to modify:
- News categories and priorities
- Minimum stories per category
- Keywords for relevance

### Sources

Edit `config/sources.yaml` to add/remove news sources:
- RSS feed URLs
- Web scraping URLs
- Source names and categories

### System Settings

Edit `config/config.yaml` for:
- Scheduling (cron expressions)
- LLM settings (model, temperature)
- Agent timeouts and limits

## Website

The Astro website is located in `website/`:

```bash
cd website
npm run dev    # Development server
npm run build  # Production build
npm run deploy # Deploy to Netlify
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Project Structure

```
gastown-news-agents/
├── agents/          # Agent implementations
├── events/          # Event bus and types
├── utils/           # Utilities (LLM, storage, email)
├── config/          # Configuration files
├── scripts/         # Orchestration scripts
├── website/         # Astro website
├── data/            # Data storage
│   ├── raw/         # Raw scraped data
│   ├── processed/   # Processed weekly data
│   └── approved/    # Approved content
└── tests/           # Test files
```

## Content Specifications

- **Target Audience**: Gen Z (ages 16-26)
- **Tone**: Excited teenager with composure - energetic but credible
- **Newsletter**: Professional HTML, Mailchimp-compatible
- **Twitter/X**: Threads <250 chars per tweet, with thumbnails
- **Podcast**: 5 minutes, MP3, excited but composed teenage voice
- **Website**: Modern, dark mode, mobile-first

## Troubleshooting

### API Key Errors
- Ensure all API keys are set in `.env`
- Check API key permissions and quotas

### Scraping Failures
- Some sources may block automated scraping
- Check network connectivity
- Review logs in `logs/` directory

### Email Not Sending
- Verify SMTP credentials
- Check firewall/security settings
- Review email logs

## License

MIT

## Contributing

This is an autonomous system. To modify:
1. Edit configuration files for behavior changes
2. Modify agent classes for logic changes
3. Update prompts in `utils/prompts.py` for content style

---

Built with ❤️ for Gen Z news consumption
