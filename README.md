# Instagram Unfollow Bot

An automated script to unfollow Instagram accounts that don't follow you back. Designed to run safely on GitHub Codespaces in headless mode.

## Features

- 🔐 Automatic login with session cookie persistence
- 📊 Parses Instagram data download files (JSON)
- 🎯 Identifies accounts that don't follow back
- 🤖 Automates unfollowing with safety delays
- 📝 Progress logging and error handling
- 🍪 Session persistence to avoid repeated logins
- 🛡️ Batch processing with breaks to avoid rate limits

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Chrome (for GitHub Codespaces)

```bash
sudo apt-get update && sudo apt-get install -y chromium-browser chromium-chromedriver
```

### 3. Download Your Instagram Data

1. Go to Instagram Settings → Privacy and Security → Download Your Information
2. Request a download (select JSON format)
3. Wait for Instagram to prepare your data (usually takes a few hours)
4. Download and extract the archive

### 4. Upload Instagram Data Files

Place these files in the project directory:
- `followers_1.json` (from `followers` folder)
- `following.json` (from `following` folder)

### 5. Configure Credentials

Edit `unfollow_bot.py` and update these variables:

```python
USERNAME = "your_instagram_username"
PASSWORD = "your_instagram_password"
```

## Usage

### Run Interactively

```bash
python unfollow_bot.py
```

The script will:
1. Load your Instagram data files
2. Show how many accounts don't follow back
3. Ask for confirmation before starting
4. Process unfollows with progress updates

### Run in Background

When running in background mode, you must use the `--yes` flag to skip the confirmation prompt:

```bash
nohup python unfollow_bot.py --yes > output.log 2>&1 &
```

Monitor progress:
```bash
tail -f output.log
```

**Note**: The `--yes` flag skips the confirmation prompt and automatically proceeds with unfollowing. Use with caution!

## Configuration

You can adjust these settings in `unfollow_bot.py`:

```python
delay_range = (10, 20)      # Random delay between unfollows (seconds)
batch_size = 30             # Accounts per batch
batch_delay = 180           # Break between batches (seconds, 3 minutes)
```

## Safety Features

- ⏱️ Random delays (10-20 seconds) between each unfollow
- 🛑 Batch breaks (3 minutes after every 30 unfollows)
- ✅ Confirmation prompt before starting
- 📊 Progress logging with success/failure status
- 🔄 Graceful error handling (continues on failures)
- 💾 Session cookies saved for future runs

## Output

The script prints:
- Progress: `[1/100] Processing: username`
- Success: `✓ Successfully unfollowed username`
- Failures: `✗ Failed to unfollow username`
- Final summary with totals

## Troubleshooting

### Chrome crashes or initialization failures

If Chrome crashes during startup, try these steps:

1. **Verify Chrome installation:**
   ```bash
   ls -la /usr/bin/chromium-browser
   ls -la /usr/bin/chromedriver
   ```

2. **Reinstall Chrome:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y chromium-browser chromium-chromedriver
   ```

3. **Check system resources:**
   ```bash
   free -h  # Check available memory
   df -h    # Check disk space
   ```

4. **The script will automatically:**
   - Try system Chrome first
   - Fallback to webdriver-manager if system Chrome fails
   - Test Chrome stability before proceeding
   - Provide detailed error messages

### Chrome not found
If system Chrome isn't available, the script will fallback to webdriver-manager automatically.

### Login issues
Delete `instagram_cookies.pkl` to force a fresh login.

### JSON parsing errors
Ensure your Instagram data files are valid JSON. Check the file structure matches Instagram's export format.

### Element not found errors
Instagram's UI may change. The script includes error handling to skip problematic accounts and continue.

## Files

- `unfollow_bot.py` - Main script
- `requirements.txt` - Python dependencies
- `instagram_cookies.pkl` - Saved session (auto-generated)
- `output.log` - Log file (if running in background)

## Notes

- The script is designed for headless operation in Codespaces
- Always review the list of accounts before confirming
- Instagram may rate-limit aggressive unfollowing; the delays help mitigate this
- Use at your own risk - ensure compliance with Instagram's Terms of Service

## License

This script is provided as-is for educational purposes. Use responsibly.

