from __future__ import annotations
import json

import os
import sys
import time
import glob
import random
import gzip
import re
import unicodedata
import datetime as dt
from urllib import parse
from base64 import b32encode
from typing import Optional

import requests
import bs4

from config import (
    CONVERSION_RATES_EXPIRY_TIME,
    CONVERSION_RATES_FILE_PREFIX,
    SAVED_CONVERSION_RATES_DATETIME_FORMAT,
    USER_AGENTS,
    CURRENCY_INFO_URL,
    CURRENCY_NAME_MAP,
    VALID_ITEM_ID_CHARACTERS,
    UNICODE_NORMALIZE_FORM,
    SAVED_PAGE_DATETIME_FORMAT,
    CURRENCY_INFO_RESPONSE_RESULT,
    CURRENCY_INFO_RESPONSE_SUCCESS,
    CURRENCY_INFO_RESPONSE_RATES,
    DEFAULT_PAGE_CACHE_TIMEOUT,
    MAX_REQUEST_RETRIES,
    REQUEST_RETRY_MIN_PAUSE,
    REQUEST_RETRY_MAX_PAUSE,
)


class ScrapeError(RuntimeError):
    pass


class RequestLimitReached(Exception):
    pass


class Print:

    COLORS_ENABLED = sys.stdout.isatty()

    COLOR_DEBUG = "\033[90m"
    COLOR_WARNING = "\033[33m"
    COLOR_ERROR = "\033[31m"
    COLOR_END = "\033[0m"

    # TODO: Add as command line argument
    TRACE_ENEBLED = False

    @classmethod
    def _print(cls, msg: str, prefix: str, color: Optional[str] = None) -> None:
        if cls.COLORS_ENABLED and color:
            print(f"{color}{prefix}: {msg}{cls.COLOR_END}", flush=True)
        else:
            print(f"{prefix}: {msg}", flush=True)

    @classmethod
    def trace(cls, msg: str) -> None:
        if cls.TRACE_ENEBLED:
            cls._print(msg, prefix="T", color=cls.COLOR_DEBUG)

    @classmethod
    def debug(cls, msg: str) -> None:
        cls._print(msg, prefix="D", color=cls.COLOR_DEBUG)

    @classmethod
    def info(cls, msg: str) -> None:
        cls._print(msg, prefix="I")

    @classmethod
    def warning(cls, msg: str) -> None:
        cls._print(msg, prefix="W", color=cls.COLOR_WARNING)

    @classmethod
    def error(cls, msg: str) -> None:
        cls._print(msg, prefix="E", color=cls.COLOR_ERROR)


class Page:
    def __init__(self, source: str, timestamp: dt.datetime) -> None:
        self.source: str = source
        self.timestamp: dt.datetime = timestamp


def parse_url(url: str) -> tuple[parse.SplitResult, dict[str, str]]:
    parsed_url = parse.urlsplit(url)
    parsed_query = dict(parse.parse_qsl(parsed_url.query))
    return parsed_url, parsed_query


def next_non_string_sibling(tag: bs4.element.Tag) -> bs4.element.Tag:
    next_sibling = tag.next_sibling
    while isinstance(next_sibling, bs4.element.NavigableString):
        next_sibling = next_sibling.next_sibling
    return next_sibling


def ensure_valid_item_id(item_id: str) -> None:
    if set(item_id) - set(VALID_ITEM_ID_CHARACTERS) != set():
        raise ScrapeError(f"Invalid item number/id: {item_id!r}")


def normalize_str(text: str) -> str:
    return unicodedata.normalize(UNICODE_NORMALIZE_FORM, text)


class RequestUtil:
    _instance: Optional[RequestUtil] = None

    REQUEST_BASE_HEADERS = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
            "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    REQUEST_USER_AGENT_KEY = "User-Agent"

    @classmethod
    def instance(cls) -> RequestUtil:
        if cls._instance is None:
            raise RuntimeError("RequestUtil instance not initialized")
        return cls._instance

    def __init__(
        self,
        *,
        min_pause: float,
        max_pause: float,
        sessions_num: int,
        requests_limit: Optional[int],
        pages_dir_path: str,
        conversion_rates_dir_path: str,
    ):
        if self._instance is not None:
            raise RuntimeError("RequestUtil is a singleton")
        self.__class__._instance = self
        self._request_min_pause = min_pause
        self._request_max_pause = max_pause
        self._sessions_num = sessions_num
        self._requests_limit = requests_limit
        self._pages_dir_path = pages_dir_path
        self._rates_dir_path = conversion_rates_dir_path

        # Timestamp -> Conversion json file
        self.euro_conversion_rate_files: dict[
            dt.datetime, str
        ] = self._get_euro_conversion_rate_files()
        # Timestamp (matching the one above) -> Conversion table
        self.euro_conversion_rates: dict[dt.datetime, dict[str, float]] = {}

        self._current_requests_count: int = 0
        self._current_requests_start_time: float = -1.0

        self._request_sessions: list[tuple[requests.Session, dict[str, str], int]] = [
            (requests.Session(), self._request_headers(ua), 0)
            for ua in random.sample(USER_AGENTS, k=sessions_num)
        ]

    def _get_euro_conversion_rate_files(self) -> dict[dt.datetime, str]:
        glob_matches = glob.glob(
            os.path.join(self._rates_dir_path, f"{CONVERSION_RATES_FILE_PREFIX}*.json")
        )
        result = {
            dt.datetime.strptime(
                os.path.basename(rates_file_path)
                .removeprefix(CONVERSION_RATES_FILE_PREFIX)
                .split(".")[0],
                SAVED_CONVERSION_RATES_DATETIME_FORMAT,
            ): rates_file_path
            for rates_file_path in glob_matches
        }
        Print.info(f"Found {len(result)} saved currency conversion rate tables")
        return result

    @classmethod
    def _request_headers(cls, user_agent: str) -> dict[str, str]:
        return {
            cls.REQUEST_USER_AGENT_KEY: user_agent,
            **cls.REQUEST_BASE_HEADERS,
        }

    def get_page(
        self,
        url: str,
        cache_timeout: dt.timedelta = DEFAULT_PAGE_CACHE_TIMEOUT,
        allow_redirect_to: Optional[re.Pattern] = None,
    ) -> Page:
        encoded_name = self._filename_encode(url)
        glob_matches = glob.glob(os.path.join(self._pages_dir_path, f"{encoded_name}_*.html.gz"))
        if glob_matches:
            # start with latest in case of multiple
            for local_page_file in reversed(sorted(glob_matches)):
                page_timestamp = dt.datetime.strptime(
                    os.path.basename(local_page_file).split(".")[0].split("_")[1],
                    SAVED_PAGE_DATETIME_FORMAT,
                )
                page_td = dt.datetime.utcnow() - page_timestamp
                if page_td > cache_timeout:
                    Print.info(
                        f"All cached versions of page {url!r} older than {cache_timeout!s}"
                        f" (most recent: {page_td!s} ago), re-downloading page."
                    )
                    break
                Print.debug(f"Reading page {url} from file {local_page_file}")
                try:
                    with gzip.open(local_page_file) as fh:
                        return Page(source=fh.read().decode(), timestamp=page_timestamp)
                except gzip.BadGzipFile:
                    Print.warning(f"Bad gzip file, ignoring: {local_page_file}")
        page_datetime = dt.datetime.utcnow()
        datetime_str = page_datetime.strftime(SAVED_PAGE_DATETIME_FORMAT)
        local_page_file = os.path.join(
            self._pages_dir_path,
            f"{encoded_name}_{datetime_str}.html.gz",
        )
        page_source = self._download_page(url, allow_redirect_to)
        if not os.path.isdir(self._pages_dir_path):
            Print.info(f"Creating directory for storing page source: {self._pages_dir_path}")
            os.makedirs(self._pages_dir_path, exist_ok=False)
        Print.debug(f"Saving page {url} to file {local_page_file}")
        with gzip.open(local_page_file, "wb") as fh:
            fh.write(page_source.encode())
        return Page(source=page_source, timestamp=page_datetime)

    def convert_to_euro(self, currency: str, amount: float, timestamp: dt.datetime) -> float:
        Print.trace(
            f"Converting {amount} {currency.upper()} currency into euro for timestamp {timestamp}"
        )
        euro_conversion_rates = self._get_euro_conversion_rates_for_timestamp(timestamp)
        currency_name = CURRENCY_NAME_MAP.get(currency.lower(), currency).upper()
        return amount / euro_conversion_rates[currency_name]

    def _get_euro_conversion_rates_for_timestamp(
        self, timestamp: dt.datetime
    ) -> dict[str, float]:
        # Check if latest downloaded rate is not too old, download new
        # conversion table in this case; checking current timestamp instead of
        # page timestamp so that we can download the new conversion rates and
        # then use the one closest to the page timestamp which in rare cases
        # may happen to still be the previous one
        if len(self.euro_conversion_rate_files) == 0 or (
            timestamp >= (latest_rates_timestamp := max(self.euro_conversion_rate_files.keys()))
            and dt.datetime.utcnow() - latest_rates_timestamp > CONVERSION_RATES_EXPIRY_TIME
        ):
            self._download_euro_conversion_rates()
        # TODO: Extremely inefficient way to find the closest timestamp
        ts_differences = [
            (file_ts, abs(timestamp - file_ts))
            for file_ts in self.euro_conversion_rate_files.keys()
        ]
        closest_timestamp, difference = min(ts_differences, key=lambda el: el[1])
        Print.trace(
            f"Using closest conversion rates timestamp {closest_timestamp} to target {timestamp}"
        )
        if difference > CONVERSION_RATES_EXPIRY_TIME:
            Print.warning(
                f"Closest conversion rates map still not close enough, difference: {difference}."
                " This can result in inacurrate prices and may be caused by deleting previously"
                " saved conversion rates."
            )
        if closest_timestamp not in self.euro_conversion_rates:
            with open(self.euro_conversion_rate_files[closest_timestamp], encoding="utf-8") as fp:
                self.euro_conversion_rates[closest_timestamp] = json.load(fp)[
                    CURRENCY_INFO_RESPONSE_RATES
                ]
        return self.euro_conversion_rates[closest_timestamp]

    def _download_euro_conversion_rates(self) -> None:
        Print.info("Downloading currency conversion info...")
        resp = requests.get(CURRENCY_INFO_URL)
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json[CURRENCY_INFO_RESPONSE_RESULT].lower() != CURRENCY_INFO_RESPONSE_SUCCESS:
            raise ScrapeError(
                f"Failed to retrieve currency conversion info from: {CURRENCY_INFO_URL}"
            )
        euro_conversion_rates = resp_json[CURRENCY_INFO_RESPONSE_RATES]
        Print.debug(f"Received conversion rates: {euro_conversion_rates!r}")
        timestamp = dt.datetime.utcnow()
        datetime_str = timestamp.strftime(SAVED_CONVERSION_RATES_DATETIME_FORMAT)
        rates_filepath = os.path.join(
            self._rates_dir_path, f"{CONVERSION_RATES_FILE_PREFIX}{datetime_str}.json"
        )
        Print.info(f"Saving downloaded currency conversion rates to file {rates_filepath}")
        assert not os.path.exists(rates_filepath)
        if not os.path.isdir(self._rates_dir_path):
            Print.info(
                "Creating directory for storing currency conversion rates:"
                f" {self._rates_dir_path}"
            )
            os.mkdir(self._rates_dir_path)
        with open(rates_filepath, "w", encoding="utf-8") as fp:
            json.dump(resp_json, fp)
        # Parse the timestamp string instead of using the original in order
        # to have a timestamp based on the filename as it is for the rest
        save_timestamp = dt.datetime.strptime(
            datetime_str, SAVED_CONVERSION_RATES_DATETIME_FORMAT
        )
        self.euro_conversion_rate_files[save_timestamp] = rates_filepath
        self.euro_conversion_rates[save_timestamp] = euro_conversion_rates

    @staticmethod
    def _filename_encode(filename: str) -> str:
        return b32encode(filename.encode()).decode()

    def _download_page(self, url: str, allow_redirect_to: Optional[re.Pattern]) -> str:
        if (
            self._requests_limit is not None
            and self._current_requests_count >= self._requests_limit
        ):
            raise RequestLimitReached()
        if self._current_requests_start_time < 0:
            self._current_requests_start_time = time.time()
        daily_offline_retries = unexpected_status_retries = 0
        while self._request_sessions:
            sessions = list(enumerate(self._request_sessions))
            session_idx, (session, request_headers, _) = random.choice(sessions)
            pause = random.uniform(self._request_min_pause, self._request_max_pause)
            Print.debug(f"Sleeping {pause} seconds before request...")
            time.sleep(pause)
            self._current_requests_count += 1
            self._request_sessions[session_idx] = (
                *self._request_sessions[session_idx][:2],
                self._request_sessions[session_idx][2] + 1,
            )
            Print.info(f"Downloading page (session {session_idx}): {url}")
            timed_out = False
            try:
                resp = session.get(url, headers=request_headers, timeout=30)
            except requests.exceptions.Timeout:
                # Very long response times can be intentional
                timed_out = True
            except requests.exceptions.ConnectionError as err:
                if "timed out" not in str(err).lower():
                    raise
                timed_out = True

            if (
                timed_out
                or resp.status_code == 429
                or "quota%20exceeded" in resp.url.lower()
                or "quota exceeded" in resp.text.lower()
            ):
                total_time = time.time() - self._current_requests_start_time
                Print.warning(
                    f"Bricklinks Quota Exceeded after {self._current_requests_count} total"
                    f" requests performed in {total_time} seconds, averaging 1 request per"
                    f" {total_time/self._current_requests_count} seconds and after"
                    f" {self._request_sessions[session_idx][2]} requests with this session,"
                    " averaging 1 request per"
                    f" {total_time/self._request_sessions[session_idx][2]} seconds. Session idx:"
                    f" {session_idx} ({self._sessions_num} total), user agent:"
                    f" {USER_AGENTS.index(request_headers[self.REQUEST_USER_AGENT_KEY])}."
                )
                self._request_sessions.pop(session_idx)
                continue

            if resp.status_code != 200 and unexpected_status_retries < MAX_REQUEST_RETRIES:
                unexpected_status_retries += 1
                pause = random.uniform(REQUEST_RETRY_MIN_PAUSE, REQUEST_RETRY_MAX_PAUSE)
                Print.warning(
                    f"Received status code: {resp.status_code}, retrying in {pause} seconds"
                    f" ({unexpected_status_retries}/{MAX_REQUEST_RETRIES})..."
                )
                time.sleep(pause)
                continue

            resp.raise_for_status()
            if len(resp.history) != 0:
                if "oops.asp?err=dailyOffline" in resp.url:
                    if daily_offline_retries < 10:
                        daily_offline_retries += 1
                        Print.warning(
                            "Bricklink offline, waiting 20 minutes before trying again"
                            f" ({daily_offline_retries}/10)..."
                        )
                        time.sleep(20 * 60)
                        continue
                    raise ScrapeError("Bricklink offline for more than 200 minutes")

                if not (allow_redirect_to and allow_redirect_to.match(resp.url)):
                    raise ScrapeError(
                        f"Unexpected redirect when downloading page: {url} -> {resp.url}"
                    )
            return resp.text

        Print.warning(f"Quota Exceeded for all {self._sessions_num} sessions, exiting...")
        raise ScrapeError("Bricklinks Quota Exceeded!")
