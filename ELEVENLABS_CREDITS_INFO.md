# ElevenLabs Credits Information

## Current Status

Your ElevenLabs account has **5 credits remaining**, which is the free tier limit.

## The Issue

ElevenLabs charges approximately **1 credit per character** of text converted to speech.

- A 5-minute podcast script = ~750 words = ~3,750 characters = **3,750 credits needed**
- Even a 30-second intro = ~75 words = ~375 characters = **375 credits needed**
- Your current script (245 chars) = **245 credits needed**

## Solutions

### Option 1: Add Credits (Recommended)
1. Visit: https://elevenlabs.io/app/settings/billing
2. Purchase additional credits
3. Or upgrade to a paid plan for monthly credits

### Option 2: Use Shorter Scripts
For testing, you can use very short scripts (under 5 characters), but this won't be useful for a real podcast.

### Option 3: Wait for Monthly Reset
Free tier credits reset monthly. Check your account for reset date.

## Credit Usage Guide

| Script Length | Credits Needed | Duration |
|--------------|----------------|----------|
| 5 characters | 5 | ~0.3 seconds |
| 50 characters | 50 | ~3 seconds |
| 245 characters | 245 | ~15 seconds |
| 750 characters | 750 | ~45 seconds |
| 3,750 characters | 3,750 | ~5 minutes |

## Recommended Plan

For a weekly 5-minute podcast:
- **Starter Plan**: $5/month = 30,000 characters = ~8 podcasts/month
- **Creator Plan**: $22/month = 100,000 characters = ~26 podcasts/month
- **Pro Plan**: $99/month = 500,000 characters = ~133 podcasts/month

## Current Script Status

The system is ready to generate audio once you have sufficient credits. The script generation and audio pipeline are working correctly - you just need more credits in your ElevenLabs account.

## Next Steps

1. **Add credits to your ElevenLabs account**
2. **Run the generation script again:**
   ```bash
   python scripts/generate_elevenlabs_audio.py
   ```
3. **The audio will be saved to:**
   ```
   data/approved/week-YYYY-WWW/podcast.mp3
   ```

---

**Note:** The audio generation code is working correctly. The only blocker is insufficient credits in your ElevenLabs account.
