import string
from datetime import timedelta
from typing import Optional

# html parser for BeautifulSoup
BS4_HTML_PARSER = "lxml"

# https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize
UNICODE_NORMALIZE_FORM = "NFKD"

SQLITE_DATABASE_FILENAME = "bricklink.sqlite"
# Path is set later by main.py
SQLITE_DATABASE_PATH: Optional[str] = None

# Currency conversion
CURRENCY_INFO_URL = "https://open.er-api.com/v6/latest/eur"
CURRENCY_INFO_RESPONSE_RESULT = "result"
CURRENCY_INFO_RESPONSE_SUCCESS = "success"
CURRENCY_INFO_RESPONSE_RATES = "rates"
# Bricklink currency name to standard name map
CURRENCY_NAME_MAP = {
    "us": "usd",
    "rol": "ron",
    "au": "aud",
    "ca": "cad",
}

# Local path for saved pages and currency conversion rates
DEFAULT_DATA_DIR_RELATIVE_PATH = "../data"
PAGES_DIR_NAME = "pages"
CONVERSION_RATES_DIR_NAME = "conversion-rates"
CONVERSION_RATES_FILE_PREFIX = "euro-rates-"
# Datetime format for saved pages, needs to be alphabetically sortable
SAVED_PAGE_DATETIME_FORMAT = "%Y%m%d-%H%M%S"
# Datetime format for saved currency conversion rates, needs to be alphabetically sortable
SAVED_CONVERSION_RATES_DATETIME_FORMAT = "%Y%m%d-%H%M%S"

# Allowed (expected) characters in item ids
VALID_ITEM_ID_CHARACTERS = string.ascii_letters + string.digits + "_-."


# Number of sessions to split the requests between (1-10)
DEFAULT_REQUEST_SESSIONS = 1
# Minimum and maximum pause before request
REQUEST_DEFAULT_PAUSE_MIN = 1.0
REQUEST_DEFAULT_PAUSE_MAX = 3.0
# Retring of requests in case of 4xx, 5xx, etc.
MAX_REQUEST_RETRIES = 5
REQUEST_RETRY_MIN_PAUSE = 16.0
REQUEST_RETRY_MAX_PAUSE = 24.0

# Cache timeouts
CATEGORIES_PAGE_CACHE_TIMEOUT = timedelta(minutes=10)
PARTS_LIST_PAGE_CACHE_TIMEOUT = timedelta(hours=4)
PART_DETAILS_CACHE_TIMEOUT = timedelta(days=90)
COLORED_PART_DETAILS_CACHE_TIMEOUT = timedelta(days=90)
DEFAULT_PAGE_CACHE_TIMEOUT = timedelta(days=90)

# Conversion rates expiry time
CONVERSION_RATES_EXPIRY_TIME = timedelta(hours=6)

# List of user agents to pick randomly for each session
# TODO: get agents automatically e.g. <https://www.useragents.me/#most-common-desktop-useragents-json-csv>
USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.3"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.3"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.43"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.4"
    ),
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.",
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/116.0.0.0 Safari/537.36"
    ),
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
]
