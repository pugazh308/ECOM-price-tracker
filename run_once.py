"""One-shot price check, for use in CI (GitHub Actions) instead of the persistent loop in main.py."""
from main import check_prices

if __name__ == "__main__":
    check_prices()
