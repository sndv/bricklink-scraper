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
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/103.0.5026.0 Safari/537.36 Edg/103.0.1254.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/103.0.5026.0 Safari/537.36 Edg/103.0.1253.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/102.0.5005.27 Safari/537.36 Edg/102.0.1245.7",
    "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54"
    " Safari/537.36 Edg/101.0.1210.39",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54"
    " Safari/537.36 Edg/101.0.1210.39",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/101.0.4951.61 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54"
    " Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/101.0.4951.41 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127"
    " Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/103.0.5028.0 Safari/537.36 OPR/89.0.4415.0 (Edition developer)",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/101.0.4951.41 Safari/537.36 OPR/87.0.4390.17 (Edition beta)",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; x64; rv:105.0esr) Gecko/20010101 Firefox/105.0esr",
    "Mozilla/5.0 (Windows NT 10.0; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/90.0.4430.93 Safari/537.36 Vivaldi/3.7",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/90.0.4430.93 Safari/537.36 Vivaldi/3.7",
]
