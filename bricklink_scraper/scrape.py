from __future__ import annotations

import re
import datetime as dt
import urllib.parse
from typing import Optional, Callable

import bs4

from config import (
    BS4_HTML_PARSER,
    CATEGORIES_PAGE_CACHE_TIMEOUT,
    COLORED_PART_DETAILS_CACHE_TIMEOUT,
    PART_DETAILS_CACHE_TIMEOUT,
    PARTS_LIST_PAGE_CACHE_TIMEOUT,
)
from utils import (
    ScrapeError,
    RequestUtil,
    Print,
    parse_url,
    next_non_string_sibling,
    ensure_valid_item_id,
    normalize_str,
)
from database import db, Category, Part, ColoredPart


### Category page
SELECTOR_CATEGORY_LINK = "a[href^='/catalogList.asp?']"
SELECTOR_CATEGORY_LINK_B = "b"
# Number of items in category
RE_CATEGORY_ITEMS_COUNT = re.compile(r"\((\d+)\)")

### Item list page
SELECTOR_ITEMS_LIST_LINK = "table a[href^='/v2/catalog/catalogitem.page?']"
SELECTOR_ITEMS_LIST_CATALOG_DIV = "div.catalog-list__pagination--top"
SELECTOR_ITEMS_LIST_ITEM_ID_SPAN = "#id_divBlock_Main > table > tbody > tr > td > span > span"
# Number of items and pages in a category
RE_ITEMS_LIST_PAGE_COUNT = re.compile(
    r"(\d+)\s+items\s+found.\s+page\s+(\d+)\s+of\s+(\d+)",
    re.MULTILINE | re.DOTALL,
)

### Common item details page
SELECTOR_ITEM_NAME = "span#item-name-title"
SELECTOR_ITEM_WEIGHT = "span#item-weight-info"
SELECTOR_ITEM_COLORS_LIST = (
    "#_idTabContentsP .pciPGTabColorDropdownList > .pciSelectColorColorItem"
)
ITEM_COLOR_DIV_COLOR_ATTR = "data-color"
ITEM_COLOR_DIV_NAME_ATTR = "data-name"
ITEM_COLOR_DIV_RGB_ATTR = "data-rgb"
# String used for missing item info
MISSING_ITEM_INFO_STRING = "?"
ITEM_WEIGHT_UNIT = "g"

### Colored item details page
SELECTOR_ITEM_DETAILS_BOX_TD = (
    "#id-main-legacy-table > tr table > tr:nth-of-type(3) > td > table > tr > td"
)
SELECTOR_ITEM_DETAILS_TR = f"{SELECTOR_ITEM_DETAILS_BOX_TD} > table > tr"
SELECTOR_ITEM_DETAILS_MESSAGE = f"{SELECTOR_ITEM_DETAILS_BOX_TD} > center > font"
# String used for missing item info
MISSING_COLORED_ITEM_INFO_STRING = "(unavailable)"
# Regular expressions for extracting item counts and prices
RE_COUNT_COMMON = r"\:\s*(\-?\d+)"
RE_PRICE_COMMON = r"\:\s*([a-z]+)\s+\$?([0-9\,]+\.\d{2})"
RE_TIMES_SOLD = re.compile(rf"times\s+sold{RE_COUNT_COMMON}")
RE_TOTAL_LOTS = re.compile(rf"total\s+lots{RE_COUNT_COMMON}")
RE_TOTAL_QTY = re.compile(rf"total\s+qty{RE_COUNT_COMMON}")
RE_MIN_PRICE = re.compile(rf"min\s+price{RE_PRICE_COMMON}")
RE_AVG_PRICE = re.compile(rf"avg\s+price{RE_PRICE_COMMON}")
RE_QTY_AVG_PRICE = re.compile(rf"qty\s+avg\s+price{RE_PRICE_COMMON}")
RE_MAX_PRICE = re.compile(rf"max\s+price{RE_PRICE_COMMON}")

# Allowed redirect from parts list for a category with single part
RE_ALLOWED_SINGLE_PART_REDIRECT = re.compile(
    r"^https\:\/\/www\.bricklink\.com\/v2\/catalog\/catalogitem\.page\?P\=[a-zA-Z0-9\.\-\_]+$"
)


class BricklinkUrl:
    """
    Examle URLs:

    Categories list:
    https://www.bricklink.com/catalogTree.asp?itemType=P

    Items list for a category:
    https://www.bricklink.com/catalogList.asp?v=0&pg=1&catString=5&catType=P

    General item information:
    https://www.bricklink.com/v2/catalog/catalogitem.page?P=3005#T=P

    Detailed item information for specific color:
    https://www.bricklink.com/catalogPG.asp?P=3005&ColorID=0
    """

    BASE_URL = "https://www.bricklink.com/"

    CATEGORIES_PAGE = "catalogTree.asp"
    ITEMS_LIST_PAGE = "catalogList.asp"
    GENERAL_ITEM_INFO_PAGE = "v2/catalog/catalogitem.page"
    ITEM_DETAILS_PAGE = "catalogPG.asp"

    ITEM_TYPE_KEY = "itemType"
    ITEM_TYPE_PART = "P"

    SHOW_IMAGES_KEY = "v"
    SHOW_IMAGES_OFF = "0"

    PAGE_KEY = "pg"

    CATEGORY_KEY = "catString"

    CATEGORY_TYPE_KEY = "catType"
    CATEGORY_TYPE_PART = "P"

    PART_ID_KEY = "P"
    COLOR_ID_KEY = "ColorID"

    PRICE_TAB_ADDITIONAL_PART = "#T=P"

    @classmethod
    def _url(cls, page: str, params: dict[str, str], end: str = "") -> str:
        params_str = urllib.parse.urlencode(params)
        return f"{cls.BASE_URL}{page}?{params_str}{end}"

    @classmethod
    def categories(cls) -> str:
        return cls._url(cls.CATEGORIES_PAGE, {cls.ITEM_TYPE_KEY: cls.ITEM_TYPE_PART})

    @classmethod
    def parts_list(cls, category_id: str, page: int = 1) -> str:
        return cls._url(
            cls.ITEMS_LIST_PAGE,
            {
                cls.SHOW_IMAGES_KEY: cls.SHOW_IMAGES_OFF,
                cls.PAGE_KEY: str(page),
                cls.CATEGORY_KEY: category_id,
                cls.CATEGORY_TYPE_KEY: cls.CATEGORY_TYPE_PART,
            },
        )

    @classmethod
    def part_info(cls, part_id: str) -> str:
        return cls._url(
            cls.GENERAL_ITEM_INFO_PAGE,
            {cls.PART_ID_KEY: part_id},
            end=cls.PRICE_TAB_ADDITIONAL_PART,
        )

    @classmethod
    def part_details(cls, part_id: str, color_id: str) -> str:
        return cls._url(
            cls.ITEM_DETAILS_PAGE,
            {cls.PART_ID_KEY: part_id, cls.COLOR_ID_KEY: color_id},
        )


class CategoryScrape:
    def __init__(self, name: str, category_id: str, parts_count: int):
        self.name = name
        self.category_id = category_id
        self.parts_count = parts_count
        self._db_record: Optional[Category] = None

    @classmethod
    def scrape_from_page(cls, page_source: str) -> list[CategoryScrape]:
        bs = bs4.BeautifulSoup(page_source, BS4_HTML_PARSER)
        category_a_list = bs.select(SELECTOR_CATEGORY_LINK)
        categories = []
        for category_a in category_a_list:
            category_name_b = category_a.find(SELECTOR_CATEGORY_LINK_B)
            if not category_name_b:
                raise ScrapeError(
                    f"Failed to find category name in category link: {category_a.text!r}"
                )
            category_name = category_name_b.text.strip()
            category_id = parse_url(category_a["href"])[1]["catString"]
            count_span = next_non_string_sibling(category_a)
            if count_span.name != "span":
                raise ScrapeError(
                    f"Expected span element after category link but got: {count_span.name!r}"
                )
            count_span_text = count_span.text.strip()
            match = RE_CATEGORY_ITEMS_COUNT.match(count_span_text)
            if not match:
                raise ScrapeError(f"Failed to parse category items count: {count_span_text!r}")
            count = int(match.group(1))
            categories.append(cls(category_name, category_id, count))
        return categories

    @property
    def db_record(self) -> Category:
        if self._db_record is None:
            self._db_record = (
                Category.select().where(Category.category_id == self.category_id).first()
            )
            if self._db_record is None:
                Print.info(f"Creating category {self.name!r}...")
                self._db_record = Category.create(name=self.name, category_id=self.category_id)
        return self._db_record

    def missing_items_count(self) -> int:
        parts_in_db: int = self.db_record.parts.count()
        return self.parts_count - parts_in_db

    @staticmethod
    def _get_items_from_list_page(list_page_source: str) -> list[str]:
        bs = bs4.BeautifulSoup(list_page_source, BS4_HTML_PARSER)
        part_a_list = bs.select(SELECTOR_ITEMS_LIST_LINK)
        parts = []
        for part_a in part_a_list:
            part_id = part_a.text.strip()
            # Check that it looks like a valid part number
            ensure_valid_item_id(part_id)
            parts.append(part_id)
        return parts

    def scrape_parts(self) -> None:
        Print.info(f"Scraping parts list for category: {self.name!r}")
        allowed_redirect = (
            dict(allow_redirect_to=RE_ALLOWED_SINGLE_PART_REDIRECT)
            if self.parts_count == 1
            else {}
        )
        first_page_source = (
            RequestUtil.instance()
            .get_page(
                BricklinkUrl.parts_list(self.category_id, page=1),
                cache_timeout=PARTS_LIST_PAGE_CACHE_TIMEOUT,
                **allowed_redirect,
            )
            .source
        )
        bs = bs4.BeautifulSoup(first_page_source, BS4_HTML_PARSER)
        # Categories with single part are redirected to the part page
        if self.parts_count == 1 and len(bs.select(SELECTOR_ITEMS_LIST_CATALOG_DIV)) == 0:
            part_id_span = bs.select(SELECTOR_ITEMS_LIST_ITEM_ID_SPAN)[0]
            part_id = part_id_span.text.strip()
            ensure_valid_item_id(part_id)
            total_items = 1
            parts = [part_id]
        else:
            pages_bar = bs.select(SELECTOR_ITEMS_LIST_CATALOG_DIV)[0]
            pages_bar_content = pages_bar.text.strip()
            matches = RE_ITEMS_LIST_PAGE_COUNT.findall(pages_bar_content.lower())
            if len(matches) != 1 or matches[0][1] != "1":  # Current page should be 1
                raise ScrapeError(f"Failed to parse item and page numbers: {pages_bar_content!r}")
            total_pages = int(matches[0][2])
            total_items = int(matches[0][0])

            parts = []
            parts += self._get_items_from_list_page(first_page_source)
            for page_n in range(2, total_pages + 1):
                page_source = (
                    RequestUtil.instance()
                    .get_page(
                        BricklinkUrl.parts_list(self.category_id, page=page_n),
                        cache_timeout=PARTS_LIST_PAGE_CACHE_TIMEOUT,
                    )
                    .source
                )
                parts += self._get_items_from_list_page(page_source)
            if len(parts) != total_items:
                raise ScrapeError(
                    f"Total number or parsed items in category {self.name!r} does not match."
                    f" Expected: {total_items}, got: {len(parts)}."
                )
        if len(parts) != len(set(parts)):
            raise ScrapeError(f"Unexpected repeating items in category {self.name!r}.")
        Print.info(f"Found {total_items} parts in category {self.name!r}: {parts!r}")

        Print.debug("Starting scrape for missing parts...")
        for part_id in parts:
            with db.atomic():
                part_scrape = PartScrape(part_id, self)
                part_scrape.scrape()


class PartScrape:
    def __init__(self, part_id: str, category: CategoryScrape):
        self.part_id = part_id
        self.category = category
        self.db_record = Part.select().where(Part.item_id == self.part_id).first()

    def _get_title(self, bs: bs4.BeautifulSoup) -> str:
        title_span_list = bs.select(SELECTOR_ITEM_NAME)
        if len(title_span_list) != 1:
            raise ScrapeError(
                "Parts expected to have exactly one title, got:"
                f" {[el.text for el in title_span_list]!r}"
            )
        title: str = title_span_list[0].text.strip()
        return title

    def _get_weight(self, bs: bs4.BeautifulSoup) -> Optional[float]:
        weight_span_list = bs.select(SELECTOR_ITEM_WEIGHT)
        if not weight_span_list:
            Print.warning(f"Warning: no weight for part id: {self.part_id!r}")
            return None
        if len(weight_span_list) != 1:
            raise ScrapeError(
                "Expected exactly one part weight span, got:"
                f" {[el.text for el in weight_span_list]!r}"
            )
        weight = weight_span_list[0].text.strip()
        if weight == MISSING_ITEM_INFO_STRING:
            return None
        if not weight.endswith(ITEM_WEIGHT_UNIT):
            raise ScrapeError(
                f"Item weight expected to be in unit {ITEM_WEIGHT_UNIT!r}: {weight!r}"
            )
        if not weight[: -len(ITEM_WEIGHT_UNIT)].replace(".", "", 1).isdigit():
            raise ScrapeError(
                f"Item weight expected to be a number: {weight[:-len(ITEM_WEIGHT_UNIT)]!r}"
            )
        return float(weight[: -len(ITEM_WEIGHT_UNIT)])

    def scrape(self) -> None:
        if self.db_record is not None:
            return  # Part already scraped
        Print.debug(
            f"Scraping details for part with id: {self.part_id!r} (category:"
            f" {self.category.name!r})"
        )
        page_source = (
            RequestUtil.instance()
            .get_page(
                BricklinkUrl.part_info(self.part_id),
                cache_timeout=PART_DETAILS_CACHE_TIMEOUT,
            )
            .source
        )
        bs = bs4.BeautifulSoup(page_source, BS4_HTML_PARSER)
        title = self._get_title(bs)
        weight = self._get_weight(bs)
        self.db_record = Part.create(
            item_id=self.part_id,
            item_name=title,
            weight=weight,
            category=self.category.db_record,
        )

        colors_div_list = bs.select(SELECTOR_ITEM_COLORS_LIST)
        if len(colors_div_list) == 0:
            Print.warning(
                f"Warning: part has no color options, so no sell info: {self.part_id!r}"
            )
            return
        colors = [
            (
                color_div.attrs[ITEM_COLOR_DIV_COLOR_ATTR],
                color_div.attrs[ITEM_COLOR_DIV_NAME_ATTR],
                color_div.attrs[ITEM_COLOR_DIV_RGB_ATTR],
            )
            for color_div in colors_div_list
        ]
        Print.debug(
            f"Found the following colors for part {self.part_id!r} (category:"
            f" {self.category.name!r}): {colors!r}"
        )

        Print.debug("Starting scrape for each color...")
        for color_id, color_name, color_rgb in colors:
            colored_part_scrape = ColoredPartScrape(color_id, color_name, color_rgb, self)
            colored_part_scrape.scrape()


class ColoredPartScrape:
    def __init__(self, color_id: str, color_name: str, color_rgb: str, part: PartScrape):
        self.color_id = color_id
        self.color_name = color_name
        self.color_rgb = color_rgb
        self.part = part
        self.db_record = (
            ColoredPart.select()
            .where(ColoredPart.part == part.db_record, ColoredPart.color_id == color_id)
            .first()
        )

    @staticmethod
    def _price_data_fields_list() -> list[
        list[tuple[str, re.Pattern, Callable[[re.Match, Optional[dt.datetime]], int]]]
    ]:
        def convert_qty(qty_match: re.Match, timestamp: Optional[dt.datetime] = None) -> int:
            return int(qty_match.group(1))

        def convert_price(price_match: re.Match, timestamp: Optional[dt.datetime]) -> int:
            if timestamp is None:
                raise RuntimeError("Page timestamp is required for converting prices")
            return round(
                RequestUtil.instance().convert_to_euro(
                    price_match.group(1),
                    float(price_match.group(2).replace(",", "")),
                    timestamp,
                )
                * 10000
            )

        return [
            [
                ("six_month_new_times_sold", RE_TIMES_SOLD, convert_qty),
                ("six_month_new_total_qty", RE_TOTAL_QTY, convert_qty),
                ("six_month_new_min_price", RE_MIN_PRICE, convert_price),
                ("six_month_new_avg_price", RE_AVG_PRICE, convert_price),
                ("six_month_new_qty_avg_price", RE_QTY_AVG_PRICE, convert_price),
                ("six_month_new_max_price", RE_MAX_PRICE, convert_price),
            ],
            [
                ("six_month_used_times_sold", RE_TIMES_SOLD, convert_qty),
                ("six_month_used_total_qty", RE_TOTAL_QTY, convert_qty),
                ("six_month_used_min_price", RE_MIN_PRICE, convert_price),
                ("six_month_used_avg_price", RE_AVG_PRICE, convert_price),
                ("six_month_used_qty_avg_price", RE_QTY_AVG_PRICE, convert_price),
                ("six_month_used_max_price", RE_MAX_PRICE, convert_price),
            ],
            [
                ("current_new_total_lots", RE_TOTAL_LOTS, convert_qty),
                ("current_new_total_qty", RE_TOTAL_QTY, convert_qty),
                ("current_new_min_price", RE_MIN_PRICE, convert_price),
                ("current_new_avg_price", RE_AVG_PRICE, convert_price),
                ("current_new_qty_avg_price", RE_QTY_AVG_PRICE, convert_price),
                ("current_new_max_price", RE_MAX_PRICE, convert_price),
            ],
            [
                ("current_used_total_lots", RE_TOTAL_LOTS, convert_qty),
                ("current_used_total_qty", RE_TOTAL_QTY, convert_qty),
                ("current_used_min_price", RE_MIN_PRICE, convert_price),
                ("current_used_avg_price", RE_AVG_PRICE, convert_price),
                ("current_used_qty_avg_price", RE_QTY_AVG_PRICE, convert_price),
                ("current_used_max_price", RE_MAX_PRICE, convert_price),
            ],
        ]

    def scrape(self) -> None:
        if self.db_record is not None:
            raise RuntimeError("Colored part already scraped!")
        Print.info(
            f"Scraping full details for part {self.part.part_id!r} with color {self.color_name!r}"
        )
        page = RequestUtil.instance().get_page(
            BricklinkUrl.part_details(self.part.part_id, self.color_id),
            cache_timeout=COLORED_PART_DETAILS_CACHE_TIMEOUT,
        )
        bs = bs4.BeautifulSoup(page.source, BS4_HTML_PARSER)
        td_box_list = bs.select(SELECTOR_ITEM_DETAILS_BOX_TD)
        if len(td_box_list) != 4:
            raise ScrapeError(
                f"Expected exactly 4 info <td> boxes for item {self.part.part_id!r} with color"
                f" {self.color_name!r}."
            )

        price_values = {}
        for td_box, data_fields in zip(td_box_list, self._price_data_fields_list(), strict=True):
            if normalize_str(td_box.text.strip()).lower() == MISSING_COLORED_ITEM_INFO_STRING:
                data_fields_str = ", ".join(field[0] for field in data_fields)
                Print.warning(
                    f"Warning: missing info for item {self.part.part_id!r}, color"
                    f" {self.color_name!r}: {data_fields_str}"
                )
                continue
            info_tr_list = td_box.select("td > table > tr")
            if len(info_tr_list) != 6:
                raise ScrapeError(
                    "Expected exactly 6 lines with detailed info for item"
                    f" {self.part.part_id!r} with color {self.color_name!r}."
                )
            for info_tr, (data_field, data_field_re, cnv_fn) in zip(
                info_tr_list, data_fields, strict=True
            ):
                info_text = normalize_str(info_tr.text.strip()).lower()
                match = data_field_re.match(info_text)
                if not match:
                    raise ScrapeError(
                        f"Failed to parse item info field {data_field}: {info_text!r} with"
                        f" regular expression: {data_field_re!r}"
                    )
                price_values[data_field] = cnv_fn(match, page.timestamp)

        self.db_record = ColoredPart.create(
            part=self.part.db_record,
            color_id=self.color_id,
            color_name=self.color_name,
            color_rgb=self.color_rgb,
            **price_values,
        )


def run_scrape() -> None:
    categories_page_source = (
        RequestUtil.instance()
        .get_page(
            BricklinkUrl.categories(),
            cache_timeout=CATEGORIES_PAGE_CACHE_TIMEOUT,
        )
        .source
    )
    categories = CategoryScrape.scrape_from_page(categories_page_source)
    for category in categories:
        missing = category.missing_items_count()
        if missing < 0:
            Print.warning(
                f"Negative missing element count for category {category.name!r}: {missing} (more"
                " elements in DB than on the website, consider rebuilding DB)"
            )
        elif missing > 0:
            Print.info(
                f"{missing}/{category.parts_count} parts missing from DB for"
                f" {category.name!r}, scraping..."
            )
            category.scrape_parts()
    print("\n")
    Print.info("SUCCESS: All categories fully scraped!")
