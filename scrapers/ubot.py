# -*- coding: utf-8 -*-
"""
聯邦銀行 (UBot) 信用卡優惠爬蟲
"""

from typing import List, Dict
from .base import BaseScraper


# 分類設定
CATEGORIES = [
    {"name": "強打優惠", "url": "https://card.ubot.com.tw/CardActivity?category=強打優惠"},
    {"name": "卡片優惠", "url": "https://card.ubot.com.tw/CardActivity?category=卡片優惠"},
    {"name": "百貨零售", "url": "https://card.ubot.com.tw/CardActivity?category=百貨零售"},
    {"name": "旅遊優惠", "url": "https://card.ubot.com.tw/CardActivity?category=旅遊優惠"},
    {"name": "交通汽修", "url": "https://card.ubot.com.tw/CardActivity?category=交通汽修"},
    {"name": "網購數位", "url": "https://card.ubot.com.tw/CardActivity?category=網購數位"},
    {"name": "生活繳費", "url": "https://card.ubot.com.tw/CardActivity?category=生活繳費"},
    {"name": "購物娛樂", "url": "https://card.ubot.com.tw/CardActivity?category=購物娛樂"},
]

# 提取優惠的 JavaScript
EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    document.querySelectorAll('.card').forEach(card => {
        // 找標題 (card-body 內第一個文字區塊)
        const body = card.querySelector('.card-body');
        if (!body) return;
        
        // 嘗試多種方式取得標題
        let title = null;
        const titleEl = body.querySelector('h3, h4, h5, .card-title');
        if (titleEl) {
            title = titleEl.innerText.trim();
        } else {
            // 取 card-body 內第一段文字
            const texts = body.innerText.split('\\n').filter(t => t.trim());
            title = texts[0] ? texts[0].trim() : null;
        }
        
        if (!title || seen.has(title)) return;
        
        // 找連結
        const linkEl = card.closest('a') || card.querySelector('a');
        let href = linkEl ? linkEl.getAttribute('href') : null;
        
        if (href && !href.startsWith('http')) {
            href = window.location.origin + href;
        }
        
        if (title && href) {
            seen.add(title);
            offers.push({ title, url: href });
        }
    });
    
    return offers;
}
"""

GET_PAGES_SCRIPT = """
() => {
    const pages = document.querySelectorAll('.pagingNumber');
    return Array.from(pages).map(p => p.innerText.trim()).filter(t => t);
}
"""


class UBotScraper(BaseScraper):
    """聯邦銀行爬蟲"""
    
    def __init__(self):
        super().__init__("聯邦銀行")
    
    async def scrape(self, page) -> List[Dict]:
        """爬取聯邦銀行所有分類優惠"""
        print(f"\n{'='*50}")
        print(f"開始爬取: {self.bank_name}")
        print("="*50)
        
        all_offers = []
        
        for cat in CATEGORIES:
            print(f"\n  分類: {cat['name']}...")
            try:
                await page.goto(cat["url"], wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)
                
                # 取得頁數
                page_numbers = await page.evaluate(GET_PAGES_SCRIPT)
                total_pages = len(page_numbers) if page_numbers else 1
                print(f"    共 {total_pages} 頁")
                
                for p in range(1, total_pages + 1):
                    if p > 1:
                        # 點擊頁碼
                        page_btn = await page.query_selector(f'.pagingNumber:text("{p}")')
                        if page_btn:
                            await page_btn.click()
                            await page.wait_for_timeout(2000)
                    
                    # 滾動以確保所有卡片載入
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(500)
                    
                    # 提取當前頁面的優惠
                    current_offers = await page.evaluate(EXTRACT_SCRIPT)
                    
                    existing_titles = {o["title"] for o in all_offers}
                    for offer in current_offers:
                        if offer["title"] not in existing_titles:
                            offer["bank"] = self.bank_name
                            offer["category"] = cat["name"]
                            all_offers.append(offer)
                
                print(f"    累計: {len(all_offers)} 筆")
                
            except Exception as e:
                print(f"    錯誤: {e}")
        
        print(f"\n  {self.bank_name}總計: {len(all_offers)} 筆")
        return self.deduplicate(all_offers)
