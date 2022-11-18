import sys
import os
from typing import Optional

import click

from utils import RequestLimitReached, ScrapeError, RequestUtil, Print
import config
from config import (
    CONVERSION_RATES_DIR_NAME,
    REQUEST_DEFAULT_PAUSE_MIN,
    REQUEST_DEFAULT_PAUSE_MAX,
    DEFAULT_REQUEST_SESSIONS,
    DEFAULT_DATA_DIR_RELATIVE_PATH,
    PAGES_DIR_NAME,
    SQLITE_DATABASE_FILENAME,
)

DATA_DIR_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), DEFAULT_DATA_DIR_RELATIVE_PATH)
)


@click.command()
@click.option(
    "--min-pause",
    type=float,
    default=REQUEST_DEFAULT_PAUSE_MIN,
    show_default=True,
    help="Minimum pause before each request in seconds",
)
@click.option(
    "--max-pause",
    type=float,
    default=REQUEST_DEFAULT_PAUSE_MAX,
    show_default=True,
    help="Maximum pause before each request in seconds",
)
@click.option(
    "--sessions-num",
    type=int,
    default=DEFAULT_REQUEST_SESSIONS,
    show_default=True,
    help="Number of sessions to split the requests across (1-8)",
)
@click.option(
    "--requests-limit",
    type=int,
    help="Exit after this many requests are performed, by default there is no limit",
)
@click.option(
    "--data-dir",
    type=str,
    default=DATA_DIR_PATH,
    show_default=True,
    help="Path to data directory where to save the downloaded pages and database",
)
def main(
    min_pause: float,
    max_pause: float,
    sessions_num: int,
    data_dir: str,
    requests_limit: Optional[int] = None,
) -> None:
    config.SQLITE_DATABASE_PATH = os.path.join(data_dir, SQLITE_DATABASE_FILENAME)
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    from scrape import run_scrape

    pages_dir = os.path.join(data_dir, PAGES_DIR_NAME)
    conversion_rates_dir = os.path.join(data_dir, CONVERSION_RATES_DIR_NAME)
    # Create RequestUtil instance
    RequestUtil(
        min_pause=min_pause,
        max_pause=max_pause,
        sessions_num=sessions_num,
        requests_limit=requests_limit,
        pages_dir_path=pages_dir,
        conversion_rates_dir_path=conversion_rates_dir,
    )
    try:
        run_scrape()
    except RequestLimitReached:
        print()
        Print.info("Requests limit reached, exiting...")
        sys.exit(0)
    except KeyboardInterrupt:
        print()
        Print.warning("Received Ctrl+C, exiting...")
        sys.exit(3)
    except ScrapeError as err:
        print()
        Print.error("Scraping failed.")
        Print.error(str(err))
        sys.exit(2)


if __name__ == "__main__":
    main()
