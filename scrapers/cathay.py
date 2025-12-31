# -*- coding: utf-8 -*-
"""
國泰世華 (Cathay) 信用卡優惠爬蟲
"""

from typing import List, Dict
from .base import BaseScraper


# 優惠頁面 URL
CATHAY_URL = "https://www.cathay-cube.com.tw/cathaybk/personal/event/overview"

# 提取優惠的 JavaScript
EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    // 嘗試多種選擇器
    const cards = document.querySelectorAll('a.eventcard, a[class*="eventcard"], div[class*="event"] a[href*="/event/"]');
    cards.forEach(card => {
        // 找標題 (嘗試多種方式)
        let title = null;
        const titleEl = card.querySelector('h3, h4, .title, [class*="title"]');
        if (titleEl) {
            title = titleEl.innerText.trim();
        } else {
            // 從 alt 屬性或 innerText 取得
            const img = card.querySelector('img');
            title = (img && img.alt) || card.innerText.trim().split('\\n')[0];
        }
        
        let href = card.getAttribute('href');
        
        if (title && href && !seen.has(title) && title.length > 2) {
            seen.add(title);
            // 處理相對路徑
            if (!href.startsWith('http')) {
                href = window.location.origin + href;
            }
            offers.push({ title, url: href });
        }
    });
    
    return offers;
}
"""


class CathayScraper(BaseScraper):
    """國泰世華爬蟲"""
    
    def __init__(self):
        super().__init__("國泰世華")
    
    async def scrape(self, page) -> List[Dict]:
        """爬取國泰世華優惠"""
        print(f"\n{'='*50}")
        print(f"開始爬取: {self.bank_name}")
        print("="*50)
        
        all_offers = []
        
        try:
            await page.goto(CATHAY_URL, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_timeout(8000)  # 等待 React 完全渲染
            
            # 先滾動幾次觸發內容載入
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            
            # 檢查目前有多少卡片
            initial_count = await page.evaluate("document.querySelectorAll('a.eventcard, a[class*=\"eventcard\"]').length")
            print(f"  初始載入: {initial_count} 筆")
            
            # 持續點擊「展開更多」直到沒有更多
            max_clicks = 50
            for i in range(max_clicks):
                # 滾動到底部
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(800)
                
                # 找「展開更多」按鈕
                load_more = await page.query_selector('a.dot-animate-wrapper')
                if not load_more:
                    load_more = await page.query_selector('[class*="dot-animate"]')
                if not load_more:
                    load_more = await page.query_selector('text=展開更多')
                if not load_more:
                    load_more = await page.query_selector('a:has-text("展開")')
                
                if not load_more:
                    print(f"  已展開全部內容 (點擊 {i} 次)")
                    break
                
                # 檢查按鈕是否可見
                is_visible = await load_more.is_visible()
                if not is_visible:
                    print(f"  已展開全部內容 (點擊 {i} 次)")
                    break
                
                try:
                    await load_more.click()
                    await page.wait_for_timeout(1200)
                    if (i + 1) % 5 == 0:
                        current_count = await page.evaluate("document.querySelectorAll('a.eventcard, a[class*=\"eventcard\"]').length")
                        print(f"  點擊展開更多... ({i + 1}) - 目前 {current_count} 筆")
                except Exception as click_err:
                    print(f"  點擊失敗: {click_err}")
                    break
            
            # 最後滾動確保全部載入
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(500)
            
            # 提取所有優惠
            offers = await page.evaluate(EXTRACT_SCRIPT)
            
            for offer in offers:
                offer["bank"] = self.bank_name
                offer["category"] = "信用卡優惠"
                all_offers.append(offer)
            
            print(f"\n  {self.bank_name}總計: {len(all_offers)} 筆")
            
        except Exception as e:
            print(f"  錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        return self.deduplicate(all_offers)
