# Fix ElevenLabs API Key Issue

## Problem

You're using a **restricted project API key** (`kb-el-API-Key`) that only has 5 credits, not your main account key with 10k credits.

## Solution

### Step 1: Get Your Main Account API Key

1. Go to: https://elevenlabs.io/app/settings/api-keys
2. Look for your **main account API key** (not a project-specific key)
3. It should have full permissions and access to your 10k credits

### Step 2: Update .env File

```bash
# Edit .env file
nano .env

# Replace the ELEVENLABS_API_KEY line with:
ELEVENLABS_API_KEY=your_main_account_key_here
```

### Step 3: Verify

```bash
python scripts/check_elevenlabs_account.py
```

This should show your full credit balance.

## How to Identify the Right Key

**Wrong Key (Project Key):**
- Has limited permissions
- Shows "kb-el-API-Key" in error messages
- Only has 5 credits
- Missing `user_read` permission

**Right Key (Main Account Key):**
- Has full permissions
- Access to all your credits (10k)
- Can read user info
- Works with all features

## Quick Fix

1. Get your main API key from ElevenLabs dashboard
2. Update `.env` file:
   ```bash
   ELEVENLABS_API_KEY=sk-your-main-key-here
   ```
3. Run again:
   ```bash
   python scripts/generate_elevenlabs_audio.py
   ```

---

**Note:** The code is working correctly - you just need to use the right API key!
