# -*- coding: utf-8 -*-
"""
爬蟲基礎類別
定義統一介面供各銀行模組繼承
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime


class BaseScraper(ABC):
    """銀行爬蟲基礎類別"""
    
    def __init__(self, bank_name: str):
        self.bank_name = bank_name
        self.offers: List[Dict] = []
    
    @abstractmethod
    async def scrape(self, page) -> List[Dict]:
        """
        爬取優惠資料
        
        Args:
            page: Playwright page 物件
            
        Returns:
            優惠列表，每筆格式：
            {
                "bank": str,      # 銀行名稱
                "category": str,  # 分類
                "title": str,     # 優惠標題
                "url": str        # 連結
            }
        """
        pass
    
    def deduplicate(self, offers: List[Dict]) -> List[Dict]:
        """去除重複優惠"""
        seen = set()
        unique = []
        for o in offers:
            key = (o["bank"], o["title"], o["url"])
            if key not in seen:
                seen.add(key)
                unique.append(o)
        return unique
    
    def add_metadata(self, offers: List[Dict], category: str = None) -> List[Dict]:
        """加入銀行名稱與分類"""
        for o in offers:
            o["bank"] = self.bank_name
            if category:
                o["category"] = category
        return offers
