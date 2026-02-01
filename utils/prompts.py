RELEVANCE_ANALYSIS = """Analyze this news article for relevance to Gen Z audiences (ages 16-26).

Title: {title}
Summary: {summary}
Category: {category}

Rate relevance from 0.0 to 1.0 based on:
- Interest to young people
- Cultural relevance  
- Impact on their lives
- Engagement potential

Return ONLY a number between 0.0 and 1.0."""

STORY_RANKING = """Rank these news stories by importance for Gen Z readers.
Consider: relevance, impact, engagement potential, timeliness.

Stories:
{stories}

Return a JSON array of story indices in ranked order (most important first)."""

SCRIPT_GENERATION = """Create a {duration}-minute podcast script for a weekly news show.

Tone: Excited teenager with composure - energetic but credible
Target: Gen Z listeners
Word count: ~{word_count} words

Stories:
{stories}

Structure:
- Intro (15 sec): Hook listeners
- Story segments ({main_duration} min): Cover top stories
- Outro (15 sec): Call to action

Make it conversational. Use [PAUSE] for breaks. Explain why stories matter."""

NEWSLETTER_FORMATTING = """Write engaging newsletter content for these stories.

Tone: Excited teenager with composure
Audience: Gen Z
Format: HTML-friendly text

Stories:
{stories}

For each story:
- Catchy headline
- 100-150 word summary
- Why it matters to Gen Z

Use short sentences, active voice, occasional exclamation points."""
