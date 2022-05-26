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

# Local path for saved pages
DEFAULT_DATA_DIR_RELATIVE_PATH = "../data"
PAGES_DIR_NAME = "pages"
# Datetime format for saved pages, needs to be alphabetically sortable
SAVED_PAGE_DATETIME_FORMAT = "%Y%m%d-%H%M%S"

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
PART_DETAILS_CACHE_TIMEOUT = timedelta(days=30)
COLORED_PART_DETAILS_CACHE_TIMEOUT = timedelta(days=30)
DEFAULT_PAGE_CACHE_TIMEOUT = timedelta(days=30)

# List of user agents to pick randomly for each session
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93"
    " Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/92.0.4495.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/92.0.4476.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/91.0.4433.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93"
    " Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/90.0.4422.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/89.0.4389.72 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/99.0.3538.77 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/91.0.4450.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4464.5"
    " Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/92.0.4482.0 Safari/537.36 Edg/92.0.874.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/91.0.4472.19 Safari/537.36 Edg/91.0.864.11",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/91.0.4472.19 Safari/537.36 Edg/91.0.864.11",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/91.0.4471.0 Safari/537.36 Edg/91.0.864.1",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93"
    " Safari/537.36 Edg/90.0.818.51",
]
