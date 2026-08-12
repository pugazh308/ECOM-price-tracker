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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

NAME_SELECTORS = [
    ".B_NuCI",
    "._35KyD6",
    "h1.yhB1nd",
    "span.B_NuCI",
    "h1[class*='yhB1nd']",
]

PRICE_SELECTORS = [
    "._30jeq3._16Jk6d",
    "._30jeq3",
    "._16Jk6d",
    ".CEmiEU",
    "div[class*='30jeq3']",
]


def _parse_price(text: str) -> float | None:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def get_flipkart_data(url: str) -> tuple[str | None, float | None]:
    """
    Scrape a Flipkart product page.
    Returns (product_name, price). Either can be None on failure.
    """
    try:
        time.sleep(random.uniform(2, 4))

        resp = requests.get(url, headers=HEADERS, timeout=30)

        if resp.status_code != 200:
            print(f"  [Flipkart] HTTP {resp.status_code}")
            return None, None

        soup = BeautifulSoup(resp.text, "lxml")

        # Product name
        name = None
        for sel in NAME_SELECTORS:
            elem = soup.select_one(sel)
            if elem:
                name = elem.get_text().strip()
                break

        # Price
        price = None
        for sel in PRICE_SELECTORS:
            elem = soup.select_one(sel)
            if elem:
                price = _parse_price(elem.get_text())
                if price:
                    break

        return name, price

    except Exception as e:
        print(f"  [Flipkart] Error: {e}")
        return None, None
