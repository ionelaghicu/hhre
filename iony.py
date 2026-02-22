import base64
import logging
import random
import requests
from seleniumbase import SB

# ---------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def get_geo_data():
    """Fetch geolocation data from IP-API."""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Geo request failed: {e}")
        return None


def decode_base64_name(encoded_name: str) -> str:
    """Decode Base64 channel name."""
    try:
        return base64.b64decode(encoded_name).decode("utf-8")
    except Exception as e:
        logging.error(f"Base64 decode failed: {e}")
        return None


def click_if_present(driver, selector: str, timeout: int = 4):
    """Click an element if it exists."""
    if driver.is_element_present(selector):
        driver.cdp.click(selector, timeout=timeout)
        driver.sleep(2)


def prepare_driver(driver, url, timezone, geoloc):
    """Open URL, accept cookies, start watching if needed."""
    driver.activate_cdp_mode(url, tzone=timezone, geoloc=geoloc)
    driver.sleep(2)

    click_if_present(driver, 'button:contains("Accept")')
    driver.sleep(2)

    driver.sleep(12)
    click_if_present(driver, 'button:contains("Start Watching")')
    click_if_present(driver, 'button:contains("Accept")')

    return driver


# ---------------------------------------------------------
# Main Script
# ---------------------------------------------------------
def main():
    # Load geolocation
    geo_data = get_geo_data()
    if not geo_data:
        logging.error("Cannot continue without geolocation data.")
        return

    latitude = geo_data["lat"]
    longitude = geo_data["lon"]
    timezone_id = geo_data["timezone"]
    proxy_str = False

    # Decode channel name
    encoded_name = "YnJ1dGFsbGVz"
    full_name = decode_base64_name(encoded_name)
    if not full_name:
        logging.error("Cannot decode channel name.")
        return

    url = f"https://www.twitch.tv/{full_name}"

    logging.info(f"Starting watcher for: {url}")

    # ---------------------------------------------------------
    # Main Loop
    # ---------------------------------------------------------
    while True:
        with SB(
            uc=True,
            locale="en",
            ad_block=True,
            chromium_arg="--disable-webgl",
            proxy=proxy_str
        ) as driver:

            rnd_wait = random.randint(450, 800)
            logging.info(f"New session started. Random wait: {rnd_wait}s")

            # Prepare main driver
            prepare_driver(driver, url, timezone_id, (latitude, longitude))

            # Check if stream is live
            if driver.is_element_present("#live-channel-stream-information"):
                logging.info("Stream detected as LIVE.")

                # Accept again if needed
                click_if_present(driver, 'button:contains("Accept")')

                # Spawn second driver
                driver2 = driver.get_new_driver(undetectable=True)
                prepare_driver(driver2, url, timezone_id, (latitude, longitude))

                driver.sleep(rnd_wait)

            else:
                logging.info("Stream offline. Exiting loop.")
                break


if __name__ == "__main__":
    main()
