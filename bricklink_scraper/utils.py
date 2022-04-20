from __future__ import annotations

import os
import time
import glob
import random
import unicodedata
import datetime as dt
from urllib import parse
from base64 import b32encode
from typing import Optional

import requests
import bs4

from config import (
    USER_AGENTS,
    CURRENCY_INFO_URL,
    CURRENCY_NAME_MAP,
    VALID_ITEM_ID_CHARACTERS,
    UNICODE_NORMALIZE_FORM,
    SAVED_PAGE_DATETIME_FORMAT,
    CURRENCY_INFO_RESPONSE_RESULT,
    CURRENCY_INFO_RESPONSE_SUCCESS,
    CURRENCY_INFO_RESPONSE_RATES,
)


class ScrapeError(RuntimeError):
    pass


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
        self, *, min_pause: float, max_pause: float, sessions_num: int, pages_dir_path: str
    ):
        if self._instance is not None:
            raise RuntimeError("RequestUtil is a singleton")
        self.__class__._instance = self
        self._request_min_pause = min_pause
        self._request_max_pause = max_pause
        self._sessions_num = sessions_num
        self._pages_dir_path = pages_dir_path

        self.euro_conversion_rates: Optional[dict[str, float]] = None

        self._current_requests_count: int = 0
        self._current_requests_start_time: float = -1.0

        self._request_sessions: list[tuple[requests.Session, dict[str, str], int]] = [
            (requests.Session(), self._request_headers(ua), 0)
            for ua in random.sample(USER_AGENTS, k=sessions_num)
        ]

    @classmethod
    def _request_headers(cls, user_agent: str) -> dict[str, str]:
        return {
            cls.REQUEST_USER_AGENT_KEY: user_agent,
            **cls.REQUEST_BASE_HEADERS,
        }

    def get_page(self, url: str) -> str:
        encoded_name = self._filename_encode(url)
        glob_matches = glob.glob(os.path.join(self._pages_dir_path, f"{encoded_name}_*.html"))
        if glob_matches:
            local_page_file = sorted(glob_matches)[-1]  # use latest in case of multiple
            print(f"D: Reading page from file {local_page_file}")
            with open(local_page_file, encoding="utf-8") as fh:
                return fh.read()
        datetime_str = dt.datetime.utcnow().strftime(SAVED_PAGE_DATETIME_FORMAT)
        local_page_file = os.path.join(
            self._pages_dir_path,
            f"{encoded_name}_{datetime_str}.html",
        )
        page_source = self._download_page(url)
        if not os.path.isdir(self._pages_dir_path):
            print(f"I: Creating directory for storing page source: {self._pages_dir_path}")
            os.makedirs(self._pages_dir_path, exist_ok=False)
        print(f"D: Saving page to file {local_page_file}")
        with open(local_page_file, "w", encoding="utf-8") as fh:
            fh.write(page_source)
        return page_source

    def convert_to_euro(self, currency: str, amount: float) -> float:
        if self.euro_conversion_rates is None:
            print("I: Downloading currency conversion info...")
            resp = requests.get(CURRENCY_INFO_URL)
            resp.raise_for_status()
            resp_json = resp.json()
            if resp_json[CURRENCY_INFO_RESPONSE_RESULT].lower() != CURRENCY_INFO_RESPONSE_SUCCESS:
                raise ScrapeError(
                    f"Failed to retrieve currency conversion info from: {CURRENCY_INFO_URL}"
                )
            self.euro_conversion_rates = resp_json[CURRENCY_INFO_RESPONSE_RATES]
            print("D: Received conversion rates:", self.euro_conversion_rates)
        currency_name = CURRENCY_NAME_MAP.get(currency.lower(), currency).upper()
        return amount / self.euro_conversion_rates[currency_name]

    @staticmethod
    def _filename_encode(filename: str) -> str:
        return b32encode(filename.encode()).decode()

    def _download_page(self, url: str) -> str:
        if self._current_requests_start_time < 0:
            self._current_requests_start_time = time.time()
        while self._request_sessions:
            sessions = list(enumerate(self._request_sessions))
            session_idx, (session, request_headers, _) = random.choice(sessions)
            pause = random.uniform(self._request_min_pause, self._request_max_pause)
            print(f"D: Sleeping {pause} seconds before request...")
            time.sleep(pause)
            self._current_requests_count += 1
            self._request_sessions[session_idx] = (
                *self._request_sessions[session_idx][:2],
                self._request_sessions[session_idx][2] + 1,
            )
            print(f"I: Downloading page (session {session_idx}): {url}")
            timed_out = False
            try:
                resp = session.get(url, headers=request_headers, timeout=30)
            except requests.exceptions.Timeout:
                # Very long response times can be intentional
                timed_out = True

            if (
                timed_out
                or resp.status_code == 429
                or "quota%20exceeded" in resp.url.lower()
                or "quota exceeded" in resp.text.lower()
            ):
                total_time = time.time() - self._current_requests_start_time
                print(
                    f"W: Bricklinks Quota Exceeded after {self._current_requests_count} total"
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

            resp.raise_for_status()
            if len(resp.history) != 0:
                raise ScrapeError(
                    f"Unexpected redirect when downloading page: {url} -> {resp.url}"
                )
            return resp.text

        print(f"W: Quota Exceeded for all {self._sessions_num} sessions, exiting...")
        raise ScrapeError("Bricklinks Quota Exceeded!")
