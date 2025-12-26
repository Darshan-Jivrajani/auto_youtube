import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

url = sys.argv[1]
repeat_times = int(sys.argv[2])
watch_time = int(sys.argv[3])

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--autoplay-policy=no-user-gesture-required")
options.add_argument("--disable-web-security")
options.add_argument("--disable-features=VizDisplayCompositor")
options.add_argument("--disable-background-timer-throttling")
options.add_argument("--disable-backgrounding-occluded-windows")
options.add_argument("--disable-renderer-backgrounding")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

# Block ad domains
options.add_argument("--adblock")
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "profile.default_content_setting_values.notifications": 2
})

def skip_ads_aggressive(driver, wait):
    """Aggressive ad skipping with multiple strategies"""
    all_ad_selectors = [
        # Skip buttons
        ".ytp-ad-skip-button-container",
        "#skip-button", 
        ".ytp-ad-skip-button",
        ".ytp-ad-skip-button-modern",
        '[data-testid="ytp-ad-skip-button"]',
        '[aria-label*="Skip"]',
        '[title*="Skip"]',
        # Ad overlay close buttons
        ".ytp-ad-overlay-close-button",
        ".ytp-ad-text",
        # Video ad controls
        ".video-ads.ytp-ad-module",
        ".ytp-ad-player-overlay",
        # New ad formats
        ".ytp-ad-overlay-container",
        ".ytp-ad-module",
        "[id*='ad'] .ytp-button"
    ]
    
    for selector in all_ad_selectors:
        try:
            skip_button = driver.find_element(By.CSS_SELECTOR, selector)
            driver.execute_script("arguments[0].click();", skip_button)
            print("✅ Ad skipped!")
            time.sleep(1)
            return True
        except NoSuchElementException:
            continue
    
    # JavaScript ad mute/kill
    try:
        driver.execute_script("""
            // Mute all ads
            var videos = document.querySelectorAll('video');
            for(var i=0; i<videos.length; i++) {
                if (videos[i].muted === false) {
                    videos[i].muted = true;
                    videos[i].pause();
                }
            }
            // Remove ad overlays
            var adOverlays = document.querySelectorAll('[id*=\"ad\"], .ytp-ad-module, .video-ads');
            for(var i=0; i<adOverlays.length; i++) {
                adOverlays[i].remove();
            }
        """)
    except:
        pass
    
    return False

for i in range(repeat_times):
    print(f"Run {i + 1}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)

        # Aggressive initial ad clear
        time.sleep(3)
        skip_ads_aggressive(driver, wait)

        # Start video if needed
        video_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
        time.sleep(2)
        
        is_paused = driver.execute_script("return arguments[0].paused", video_element)
        
        if is_paused:
            driver.execute_script("arguments[0].play(); arguments[0].muted = false;", video_element)
            print("🎥 Video started")

        # Continuous ad monitoring (more frequent)
        start_time = time.time()
        while time.time() - start_time < watch_time:
            skip_ads_aggressive(driver, WebDriverWait(driver, 3))
            time.sleep(2)  # Check every 2 seconds

        print(f"✅ Watch time completed: {watch_time}s")

    except TimeoutException:
        print("❌ Timeout error")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        driver.quit()

print("🎉 Finished all runs!")
