import sys

from utils import ScrapeError
from scrape import run_scrape


def main() -> None:
    try:
        run_scrape()
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, exiting...")
        sys.exit(3)
    except ScrapeError as err:
        print("\nE: Scraping failed.")
        print(f"E: {err!s}")
        sys.exit(2)


if __name__ == "__main__":
    main()
