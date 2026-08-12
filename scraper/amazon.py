import re
import time
import random
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

# Try these in order — Amazon changes selectors periodically
PRICE_SELECTORS = [
    "#priceblock_ourprice",
    "#priceblock_dealprice",
    "#price_inside_buybox",
    ".a-price .a-offscreen",
    "#corePrice_feature_div .a-offscreen",
    "#apex_offerDisplay_desktop .a-offscreen",
    "#corePriceDisplay_desktop_feature_div .a-offscreen",
    "#newBuyBoxPrice",
]


def _parse_price(text: str) -> float | None:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def get_amazon_data(url: str) -> tuple[str | None, float | None]:
    """
    Scrape an Amazon India product page.
    Returns (product_name, price). Either can be None on failure.
    """
    try:
        time.sleep(random.uniform(2, 4))  # polite delay

        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=30)

        if resp.status_code != 200:
            print(f"  [Amazon] HTTP {resp.status_code}")
            return None, None

        soup = BeautifulSoup(resp.text, "lxml")

        # Product name
        name = None
        name_elem = soup.select_one("#productTitle")
        if name_elem:
            name = name_elem.get_text().strip()

        # Price — primary selectors
        price = None
        for sel in PRICE_SELECTORS:
            elem = soup.select_one(sel)
            if elem:
                price = _parse_price(elem.get_text())
                if price:
                    break

        # Fallback: whole + fraction parts
        if not price:
            whole = soup.select_one(".a-price-whole")
            frac  = soup.select_one(".a-price-fraction")
            if whole:
                w = re.sub(r"[^\d]", "", whole.get_text())
                f = re.sub(r"[^\d]", "", frac.get_text()) if frac else "0"
                try:
                    price = float(f"{w}.{f}") if w else None
                except ValueError:
                    pass

        return name, price

    except Exception as e:
        print(f"  [Amazon] Error: {e}")
        return None, None
