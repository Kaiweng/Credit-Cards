# -*- coding: utf-8 -*-
"""
爬蟲模組統一介面
"""

from .base import BaseScraper
from .ctbc import CTBCScraper
from .cathay import CathayScraper
from .ubot import UBotScraper

__all__ = [
    "BaseScraper",
    "CTBCScraper",
    "CathayScraper",
    "UBotScraper",
]

# 可用的爬蟲列表
AVAILABLE_SCRAPERS = {
    "ctbc": CTBCScraper,
    "cathay": CathayScraper,
    "ubot": UBotScraper,
}


def get_all_scrapers():
    """取得所有爬蟲實例"""
    return [
        CTBCScraper(),
        CathayScraper(),
        UBotScraper(),
    ]


def get_scraper(bank_code: str) -> BaseScraper:
    """根據銀行代碼取得爬蟲實例"""
    scraper_class = AVAILABLE_SCRAPERS.get(bank_code.lower())
    if scraper_class:
        return scraper_class()
    raise ValueError(f"Unknown bank code: {bank_code}")
