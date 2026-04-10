# -*- coding: utf-8 -*-
"""
玉山銀行 (E.SUN Bank) 信用卡優惠爬蟲
"""

import asyncio
from typing import List, Dict
from .base import BaseScraper

# 優惠頁面 URL (全部優惠)
ESUN_URL = "https://www.esunbank.com/zh-tw/personal/credit-card/discount/shops/all"

# 提取優惠的 JavaScript
EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    // 玉山銀行的卡片容器
    const cards = document.querySelectorAll('a.l-cardDiscountAllContent__discount');
    
    cards.forEach(card => {
        // 1. 提取標題 (優先取 title 屬性，其次取內部文字)
        let title = card.getAttribute('title');
        if (!title) {
            const pTags = card.querySelectorAll('p');
            title = Array.from(pTags).map(p => p.innerText.trim()).join(' ');
        }
        
        // 2. 提取圖片
        const img = card.querySelector('img');
        let image = img ? img.src : null;
        
        // 3. 提取連結
        let href = card.getAttribute('href');
        
        if (title && !seen.has(title)) {
            seen.add(title);
            
            // 處理相對路徑
            if (href && !href.startsWith('http')) {
                href = window.location.origin + href;
            }
            if (image && !image.startsWith('http')) {
                image = window.location.origin + image;
            }
            
            offers.push({ title, url: href, image });
        }
    });
    
    return offers;
}
"""

class ESUNScraper(BaseScraper):
    """玉山銀行爬蟲"""
    
    def __init__(self):
        super().__init__("玉山銀行")
    
    async def scrape(self, page) -> List[Dict]:
        """爬取玉山銀行優惠"""
        print(f"\\n{'='*50}")
        print(f"開始爬取: {self.bank_name}")
        print("="*50)
        
        all_offers = []
        
        try:
            await page.goto(ESUN_URL, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # 取得全部分頁
            # 玉山分頁結構: .l-cardDiscountAllContent__pagination 下的按鈕
            page_num = 1
            while True:
                print(f"  正在處理第 {page_num} 頁...")
                
                # 滾動以確保圖片載入
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                
                # 提取當前頁面
                current_offers = await page.evaluate(EXTRACT_SCRIPT)
                
                existing_titles = {o["title"] for o in all_offers}
                for offer in current_offers:
                    if offer["title"] not in existing_titles:
                        offer["bank"] = self.bank_name
                        offer["category"] = "全台優惠"
                        all_offers.append(offer)
                
                # 尋找「下一頁」按鈕
                # 玉山銀行結構: a.page-link[title="前往下一頁"]
                next_page_clicked = False
                next_btn = await page.query_selector('a.page-link[title="前往下一頁"]')
                
                if next_btn:
                    # 確保按鈕在視圖中
                    await next_btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    
                    # 檢查按鈕是否被停用 (例如在最後一頁)
                    is_disabled = await next_btn.evaluate('el => el.classList.contains("disabled") || el.parentElement.classList.contains("disabled")')
                    if not is_disabled:
                        try:
                            # 使用 evaluate 進行點擊以繞過可視性檢查
                            await next_btn.evaluate('el => el.click()')
                            print(f"  已點擊第 {page_num} 頁的下一頁...")
                            await page.wait_for_timeout(3000) # 等待 AJAX 載入
                            page_num += 1
                            next_page_clicked = True
                        except Exception as e:
                            print(f"  點擊下一頁失敗: {e}")
                    else:
                        print("  已達最後一頁 (按鈕已停用)。")
                else:
                    print("  找不到下一頁按鈕。")
                
                if not next_page_clicked:
                    break
                    
                if page_num > 40: # 安全閥
                    break
            
            print(f"\\n  {self.bank_name}總計: {len(all_offers)} 筆")
            
        except Exception as e:
            print(f"  錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        return self.deduplicate(all_offers)

if __name__ == "__main__":
    # 測試程式碼
    from playwright.async_api import async_playwright
    async def test():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            scraper = ESUNScraper()
            results = await scraper.scrape(page)
            print(f"抓取到 {len(results)} 筆資料")
            await browser.close()
    
    asyncio.run(test())
