import json
import time
import random
import pickle
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class InstagramUnfollowBot:
    def __init__(self, username, password, cookies_file='instagram_cookies.pkl'):
        self.username = username
        self.password = password
        self.driver = None
        self.cookies_file = cookies_file
        
    def setup_driver(self, headless=True):
        """Initialize Chrome driver with options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Headless mode (required for Codespaces)
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
        
        # Try to use system ChromeDriver first (for Codespaces)
        try:
            self.driver = webdriver.Chrome(options=options)
        except:
            # Fall back to webdriver-manager
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        
        if not headless:
            self.driver.maximize_window()
        
    def save_cookies(self):
        """Save cookies to file"""
        pickle.dump(self.driver.get_cookies(), open(self.cookies_file, "wb"))
        print("Session saved!")
    
    def load_cookies(self):
        """Load cookies from file"""
        if os.path.exists(self.cookies_file):
            cookies = pickle.load(open(self.cookies_file, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            return True
        return False
    
    def is_logged_in(self):
        """Check if already logged in"""
        try:
            self.driver.get('https://www.instagram.com/')
            time.sleep(3)
            # If we can find the search bar or profile icon, we're logged in
            try:
                self.driver.find_element(By.XPATH, "//span[contains(@aria-label, 'Search')]")
                return True
            except:
                pass
            try:
                self.driver.find_element(By.XPATH, "//a[contains(@href, '/accounts/edit/')]")
                return True
            except:
                pass
        except:
            pass
        return False
    
    def login(self):
        """Login to Instagram or use saved session"""
        # Try to load saved cookies first
        self.driver.get('https://www.instagram.com/')
        time.sleep(2)
        
        if self.load_cookies():
            print("Found saved session, attempting to use it...")
            self.driver.refresh()
            time.sleep(3)
            
            if self.is_logged_in():
                print("✓ Successfully logged in using saved session!")
                return True
            else:
                print("Saved session expired, logging in again...")
        
        print("Logging in to Instagram...")
        self.driver.get('https://www.instagram.com/accounts/login/')
        time.sleep(3)
        
        try:
            # Enter username
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
            username_input.send_keys(self.username)
            
            # Enter password
            password_input = self.driver.find_element(By.NAME, 'password')
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Handle "Save Your Login Info" prompt
            try:
                not_now = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]"))
                )
                not_now.click()
            except:
                pass
            
            # Handle "Turn on Notifications" prompt
            try:
                not_now = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now.click()
            except:
                pass
            
            print("Login successful!")
            time.sleep(2)
            
            # Save cookies for next time
            self.save_cookies()
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
        
        return True
    
    def load_instagram_data(self, followers_file, following_file):
        """Load followers and following from Instagram data download"""
        print("Loading Instagram data...")
        
        with open(followers_file, 'r') as f:
            followers_data = json.load(f)
        
        with open(following_file, 'r') as f:
            following_data = json.load(f)
        
        # Extract usernames from the data structure
        followers = set()
        for item in followers_data:
            if 'string_list_data' in item:
                for data in item['string_list_data']:
                    followers.add(data['value'])
        
        following = set()
        for item in following_data.get('relationships_following', []):
            if 'string_list_data' in item:
                for data in item['string_list_data']:
                    following.add(data['value'])
        
        # Find accounts that don't follow back
        not_following_back = following - followers
        
        print(f"Followers: {len(followers)}")
        print(f"Following: {len(following)}")
        print(f"Not following back: {len(not_following_back)}")
        
        return list(not_following_back)
    
    def unfollow_user(self, username):
        """Unfollow a specific user"""
        try:
            # Navigate to user profile
            self.driver.get(f'https://www.instagram.com/{username}/')
            time.sleep(random.uniform(2, 4))
            
            # Click Following button
            following_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Following') or contains(., 'Requested')]"))
            )
            following_button.click()
            time.sleep(1)
            
            # Confirm unfollow in the popup
            unfollow_confirm = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Unfollow')]"))
            )
            unfollow_confirm.click()
            
            print(f"✓ Unfollowed: {username}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to unfollow {username}: {e}")
            return False
    
    def unfollow_all(self, usernames, delay_range=(30, 60), batch_size=20, batch_delay=300):
        """
        Unfollow all users in the list with delays to avoid detection
        
        Args:
            usernames: List of usernames to unfollow
            delay_range: Tuple (min, max) seconds between unfollows
            batch_size: Number of unfollows before taking a long break
            batch_delay: Seconds to wait between batches
        """
        print(f"\nStarting to unfollow {len(usernames)} accounts...")
        print("This will take a while to avoid Instagram rate limits.\n")
        
        unfollowed = 0
        failed = 0
        
        for i, username in enumerate(usernames, 1):
            print(f"[{i}/{len(usernames)}] Processing: {username}")
            
            if self.unfollow_user(username):
                unfollowed += 1
            else:
                failed += 1
            
            # Random delay between unfollows
            if i < len(usernames):
                delay = random.uniform(*delay_range)
                print(f"Waiting {delay:.1f} seconds...\n")
                time.sleep(delay)
            
            # Longer break after batch
            if i % batch_size == 0 and i < len(usernames):
                print(f"\n⏸ Completed batch of {batch_size}. Taking a {batch_delay//60} minute break...\n")
                time.sleep(batch_delay)
        
        print("\n" + "="*50)
        print(f"Unfollowing complete!")
        print(f"Successfully unfollowed: {unfollowed}")
        print(f"Failed: {failed}")
        print("="*50)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


def main():
    # Configuration
    USERNAME = "your_instagram_username"
    PASSWORD = "your_instagram_password"
    
    # Paths to your Instagram data files
    FOLLOWERS_FILE = "followers_1.json"  # Adjust path as needed
    FOLLOWING_FILE = "following.json"    # Adjust path as needed
    
    # Run headless? (must be True for Codespaces)
    HEADLESS = True  # Runs without browser window - perfect for cloud/background
    
    # Create bot instance
    bot = InstagramUnfollowBot(USERNAME, PASSWORD)
    
    try:
        # Setup and login
        bot.setup_driver(headless=HEADLESS)
        
        if not bot.login():
            print("Login failed. Exiting...")
            return
        
        # Load data and get list of accounts to unfollow
        not_following_back = bot.load_instagram_data(FOLLOWERS_FILE, FOLLOWING_FILE)
        
        if not not_following_back:
            print("No accounts to unfollow!")
            return
        
        # Ask for confirmation
        print(f"\nReady to unfollow {len(not_following_back)} accounts.")
        response = input("Do you want to proceed? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
        
        # Start unfollowing with FAST MODE delays
        bot.unfollow_all(
            not_following_back,
            delay_range=(10, 20),  # FAST: 10-20 seconds between unfollows
            batch_size=30,          # FAST: 30 unfollows per batch
            batch_delay=180         # FAST: 3 minute break between batches
        )
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        bot.close()


if __name__ == "__main__":
    main()