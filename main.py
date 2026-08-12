import json
import time
import schedule
from datetime import datetime, timedelta

from config import CHECK_INTERVAL_HOURS, ALERT_COOLDOWN_HOURS, ALERTS_LOG_FILE
from scraper.amazon import get_amazon_data
from scraper.flipkart import get_flipkart_data
from notifier import send_price_alert


# ── Alert dedup helpers (uses a simple JSON file, no DB) ─────────────────────

def load_alerts_log() -> dict:
    try:
        with open(ALERTS_LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_alerts_log(log: dict):
    with open(ALERTS_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def already_alerted(url: str, log: dict) -> bool:
    last_str = log.get(url)
    if not last_str:
        return False
    last_time = datetime.fromisoformat(last_str)
    return datetime.now() - last_time < timedelta(hours=ALERT_COOLDOWN_HOURS)


def mark_alerted(url: str, log: dict):
    log[url] = datetime.now().isoformat()


# ── Product loader ────────────────────────────────────────────────────────────

def load_products() -> list[dict]:
    with open("products.json", "r") as f:
        return json.load(f).get("products", [])


# ── Core check ────────────────────────────────────────────────────────────────

def check_prices():
    print(f"\n{'═' * 55}")
    print(f"  🔍  Check started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═' * 55}")

    products = load_products()

    if not products:
        print("⚠️  products.json is empty — nothing to track.")
        return

    alerts_log = load_alerts_log()

    for product in products:
        url          = product.get("url", "").strip()
        platform     = product.get("platform", "").lower().strip()
        name_override = product.get("name", "")
        target_price = product.get("target_price")

        # Validate entry
        if not url or platform not in ("amazon", "flipkart"):
            print(f"⚠️  Skipping invalid entry: {product}")
            continue

        if target_price is None:
            print(f"⚠️  No target_price set for: {name_override or url[:50]}")
            continue

        label = name_override or url[:60]
        print(f"\n📦  {label}")
        print(f"    Platform : {platform.upper()}")
        print(f"    Target   : ₹{target_price:,.0f}")

        # ── Scrape current price ──────────────────────────────────────
        if platform == "amazon":
            scraped_name, current_price = get_amazon_data(url)
        else:
            scraped_name, current_price = get_flipkart_data(url)

        product_name = name_override or scraped_name or "Unknown Product"

        if current_price is None:
            print("    ❌  Could not fetch price. Skipping.")
            continue

        print(f"    Current  : ₹{current_price:,.0f}")

        # ── Compare with target ───────────────────────────────────────
        if current_price <= target_price:
            if already_alerted(url, alerts_log):
                print(f"    ⏭️   Already alerted within {ALERT_COOLDOWN_HOURS}h — skipping.")
                continue

            print("    🎯  TARGET HIT! Sending alert…")
            success = send_price_alert(
                product_name, platform, current_price, target_price, url
            )
            if success:
                mark_alerted(url, alerts_log)
        else:
            gap = current_price - target_price
            print(f"    ✅  ₹{gap:,.0f} above target — no alert.")

    save_alerts_log(alerts_log)

    print(f"\n{'═' * 55}")
    print(f"  ✅  Check complete.")
    print(f"{'═' * 55}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("🚀  Price Tracker starting…")

    # Run immediately at startup
    check_prices()

    # Then every N hours
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(check_prices)
    print(f"⏰  Scheduled every {CHECK_INTERVAL_HOURS} hour(s). Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
