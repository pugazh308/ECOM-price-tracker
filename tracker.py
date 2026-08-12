"""
Core tracking logic.
For each product, for each platform:
  1. Resolve URL (if keyword given, search first)
  2. Scrape current price
  3. Get all-time low (DB history + PriceHistory.in cache)
  4. Save current price to DB
  5. If current <= all-time low → send email alert
"""
import json
import time
from scraper import amazon, flipkart
from scraper.price_history import get_all_time_low as site_all_time_low
from database import save_price, get_db_all_time_low
from notifier import send_alert
from config import PRODUCTS_FILE


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _effective_all_time_low(product_name: str, platform: str, url: str) -> float | None:
    """
    Best all-time low from two sources:
      - Our local DB (all previous records, NOT counting the current price yet)
      - PriceHistory.in (cached daily)
    """
    db_low   = get_db_all_time_low(product_name, platform)
    site_low = site_all_time_low(url)

    candidates = [x for x in [db_low, site_low] if x is not None]
    return min(candidates) if candidates else None


def _track_platform(product_name: str, platform: str, input_str: str, scraper_mod):
    """Generic handler for one product on one platform."""
    print(f"\n   [{platform}] Input: {input_str[:60]}")

    # Step 1 — resolve URL
    if _is_url(input_str):
        url = input_str
    else:
        print(f"   [{platform}] Searching for keyword...")
        url = scraper_mod.search_keyword(input_str)
        if not url:
            print(f"   [{platform}] ❌ Could not find product for keyword.")
            return
        print(f"   [{platform}] Found: {url[:80]}")

    time.sleep(2)   # polite delay between requests

    # Step 2 — scrape current price
    result = scraper_mod.scrape(url)
    if not result:
        print(f"   [{platform}] ❌ Scrape failed.")
        return

    current_price = result["price"]
    title         = result["title"]
    print(f"   [{platform}] Current price : ₹{current_price:,.0f}")
    print(f"   [{platform}] Title         : {title[:60]}")

    # Step 3 — get all-time low BEFORE saving current price
    all_time_low = _effective_all_time_low(product_name, platform, url)
    if all_time_low:
        print(f"   [{platform}] All-time low  : ₹{all_time_low:,.0f}")
    else:
        print(f"   [{platform}] All-time low  : No history yet (first run)")

    # Step 4 — save current price
    save_price(product_name, platform, current_price, url)

    # Step 5 — compare and alert
    if all_time_low is None:
        print(f"   [{platform}] ⏭  Skipping comparison — no historical data yet.")
        return

    if current_price <= all_time_low:
        print(f"   [{platform}] 🔥 ALL-TIME LOW! Sending alert...")
        send_alert(title, platform, current_price, all_time_low, url)
    else:
        diff = current_price - all_time_low
        print(f"   [{platform}] ℹ  ₹{diff:,.0f} above all-time low. No alert.")


def run():
    print("\n" + "=" * 55)
    print("  🚀  Price Tracker — checking now")
    print("=" * 55)

    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)["products"]

    for product in products:
        name = product["name"]
        print(f"\n📦  {name}")

        if "amazon" in product:
            _track_platform(name, "Amazon", product["amazon"], amazon)

        if "flipkart" in product:
            _track_platform(name, "Flipkart", product["flipkart"], flipkart)

    print("\n" + "=" * 55)
    print("  ✅  Check complete.")
    print("=" * 55 + "\n")
