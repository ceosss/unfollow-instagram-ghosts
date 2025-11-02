#!/usr/bin/env python3
"""
Instagram Unfollow Bot
Automates unfollowing accounts that don't follow back on Instagram.
Designed to run on GitHub Codespaces in headless mode.
"""

import json
import pickle
import random
import time
import sys
from pathlib import Path
from typing import List, Set, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Configuration
USERNAME = "your_instagram_username"  # Change this
PASSWORD = "your_instagram_password"  # Change this
FOLLOWERS_FILE = "followers_1.json"
FOLLOWING_FILE = "following.json"
COOKIES_FILE = "instagram_cookies.pkl"
HEADLESS = True
delay_range = (10, 20)  # seconds between unfollows
batch_size = 30  # accounts per batch
batch_delay = 180  # seconds (3 minutes) between batches

# Chrome binary paths for Codespaces
CHROME_BINARY = "/usr/bin/chromium-browser"
CHROMEDRIVER_BINARY = "/usr/bin/chromedriver"


class InstagramUnfollowBot:
    def __init__(self):
        self.driver = None
        self.unfollowed_count = 0
        self.failed_count = 0
        self.failed_accounts = []

    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with headless configuration for Codespaces."""
        options = webdriver.ChromeOptions()
        
        if HEADLESS:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Try to use system Chrome first (for Codespaces)
        try:
            if Path(CHROME_BINARY).exists():
                options.binary_location = CHROME_BINARY
            
            if Path(CHROMEDRIVER_BINARY).exists():
                service = Service(CHROMEDRIVER_BINARY)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                # Fallback to webdriver-manager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"Warning: System Chrome setup failed ({e}), using webdriver-manager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        return driver

    def load_cookies(self) -> bool:
        """Load saved cookies if they exist."""
        if Path(COOKIES_FILE).exists():
            try:
                cookies = pickle.load(open(COOKIES_FILE, "rb"))
                self.driver.get("https://www.instagram.com")
                time.sleep(2)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Warning: Could not add cookie: {e}")
                
                self.driver.refresh()
                time.sleep(3)
                
                # Check if we're logged in
                if "accounts/login" not in self.driver.current_url:
                    print("✓ Successfully loaded saved session cookies")
                    return True
            except Exception as e:
                print(f"Warning: Could not load cookies: {e}")
        
        return False

    def save_cookies(self):
        """Save current session cookies."""
        try:
            cookies = self.driver.get_cookies()
            pickle.dump(cookies, open(COOKIES_FILE, "wb"))
            print(f"✓ Saved session cookies to {COOKIES_FILE}")
        except Exception as e:
            print(f"Warning: Could not save cookies: {e}")

    def login(self):
        """Login to Instagram or use saved session."""
        print("Attempting to login to Instagram...")
        
        # Try loading cookies first
        if self.load_cookies():
            return
        
        # Login manually
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        
        try:
            # Accept cookies if prompted
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except TimeoutException:
                pass
            
            # Enter username
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.clear()
            username_input.send_keys(USERNAME)
            
            # Enter password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(PASSWORD)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Handle "Save Login Info" popup
            try:
                not_now_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
                time.sleep(2)
            except TimeoutException:
                pass
            
            # Handle "Turn on Notifications" popup
            try:
                not_now_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
                time.sleep(2)
            except TimeoutException:
                pass
            
            # Verify login
            if "accounts/login" not in self.driver.current_url:
                print("✓ Successfully logged in")
                self.save_cookies()
            else:
                raise Exception("Login failed - still on login page")
                
        except Exception as e:
            print(f"✗ Login error: {e}")
            raise

    def parse_json_file(self, filename: str) -> List[dict]:
        """Parse Instagram data JSON file."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Instagram exports have different structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Try common keys
                if "relationships_followers" in data:
                    return data["relationships_followers"]
                elif "relationships_following" in data:
                    return data["relationships_following"]
                elif isinstance(data.get("list"), list):
                    return data["list"]
                else:
                    # Return first list-like value found
                    for value in data.values():
                        if isinstance(value, list):
                            return value
            return []
        except FileNotFoundError:
            print(f"✗ Error: {filename} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing {filename}: {e}")
            return []

    def extract_usernames(self, data: List[dict]) -> Set[str]:
        """Extract usernames from Instagram JSON data."""
        usernames = set()
        
        for item in data:
            if isinstance(item, dict):
                # Try different possible keys
                username = (
                    item.get("string_list_data", [{}])[0].get("value") if isinstance(item.get("string_list_data"), list) else None
                ) or item.get("value") or item.get("username") or item.get("user", {}).get("username")
                
                if username:
                    usernames.add(username.lower())
        
        return usernames

    def get_non_followers(self) -> List[str]:
        """Compare followers and following lists to find non-followers."""
        print(f"Loading {FOLLOWERS_FILE}...")
        followers_data = self.parse_json_file(FOLLOWERS_FILE)
        followers = self.extract_usernames(followers_data)
        print(f"✓ Found {len(followers)} followers")
        
        print(f"Loading {FOLLOWING_FILE}...")
        following_data = self.parse_json_file(FOLLOWING_FILE)
        following = self.extract_usernames(following_data)
        print(f"✓ Found {len(following)} accounts you follow")
        
        # Find accounts you follow but who don't follow back
        non_followers = following - followers
        non_followers_list = sorted(list(non_followers))
        
        print(f"\n✓ Found {len(non_followers_list)} accounts that don't follow back")
        return non_followers_list

    def unfollow_user(self, username: str) -> bool:
        """Navigate to user profile and click unfollow button."""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(2, 4))
            
            # Find and click "Following" button
            try:
                following_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Following')]"))
                )
                following_button.click()
                time.sleep(1)
                
                # Click "Unfollow" in the confirmation dialog
                unfollow_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Unfollow')]"))
                )
                unfollow_button.click()
                time.sleep(random.uniform(1, 2))
                
                return True
            except TimeoutException:
                # Button might say "Follow" instead (already not following)
                try:
                    follow_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Follow')]")
                    print(f"  → Already not following {username}")
                    return True
                except NoSuchElementException:
                    print(f"  → Could not find unfollow button for {username}")
                    return False
                    
        except Exception as e:
            print(f"  → Error unfollowing {username}: {e}")
            return False

    def process_unfollows(self, non_followers: List[str]):
        """Process unfollows with batch delays and random intervals."""
        total = len(non_followers)
        
        print(f"\nStarting unfollow process for {total} accounts...")
        print(f"Settings: {batch_size} accounts per batch, {batch_delay}s break between batches\n")
        
        for i, username in enumerate(non_followers, 1):
            print(f"[{i}/{total}] Processing: {username}")
            
            success = self.unfollow_user(username)
            
            if success:
                self.unfollowed_count += 1
                print(f"  ✓ Successfully unfollowed {username}")
            else:
                self.failed_count += 1
                self.failed_accounts.append(username)
                print(f"  ✗ Failed to unfollow {username}")
            
            # Batch break
            if i % batch_size == 0 and i < total:
                delay_minutes = batch_delay // 60
                print(f"\n⏸ Batch complete. Taking {delay_minutes}-minute break...")
                time.sleep(batch_delay)
                print("✓ Resuming...\n")
            elif i < total:
                # Random delay between unfollows
                delay = random.uniform(*delay_range)
                time.sleep(delay)

    def run(self):
        """Main execution method."""
        try:
            print("=" * 60)
            print("Instagram Unfollow Bot")
            print("=" * 60)
            
            # Confirmation prompt
            non_followers = self.get_non_followers()
            
            if not non_followers:
                print("\nNo accounts to unfollow. Exiting.")
                return
            
            print(f"\n⚠️  WARNING: This will unfollow {len(non_followers)} accounts!")
            response = input("Continue? (yes/no): ").strip().lower()
            
            if response != "yes":
                print("Aborted by user.")
                return
            
            # Setup and login
            self.driver = self.setup_driver()
            print("✓ WebDriver initialized")
            
            try:
                self.login()
                
                # Process unfollows
                self.process_unfollows(non_followers)
                
                # Final summary
                print("\n" + "=" * 60)
                print("SUMMARY")
                print("=" * 60)
                print(f"Total unfollowed: {self.unfollowed_count}")
                print(f"Total failed: {self.failed_count}")
                
                if self.failed_accounts:
                    print(f"\nFailed accounts ({len(self.failed_accounts)}):")
                    for username in self.failed_accounts:
                        print(f"  - {username}")
                
            finally:
                self.save_cookies()
                self.driver.quit()
                print("\n✓ Browser closed")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            if self.driver:
                self.save_cookies()
                self.driver.quit()
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ Fatal error: {e}")
            if self.driver:
                self.save_cookies()
                self.driver.quit()
            sys.exit(1)


if __name__ == "__main__":
    bot = InstagramUnfollowBot()
    bot.run()

