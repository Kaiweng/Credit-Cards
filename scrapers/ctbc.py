# -*- coding: utf-8 -*-
"""
中國信託 (CTBC) 信用卡優惠爬蟲
"""

from typing import List, Dict
from .base import BaseScraper


# 分類設定
CATEGORIES = [
    {"name": "精選．中信卡優惠", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_special_offer.html"},
    {"name": "餐飲優惠", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_food.html"},
    {"name": "旅遊玩家", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_travel.html"},
    {"name": "百貨藥妝", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_grocery.html"},
    {"name": "行動支付", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_payment.html"},
    {"name": "超商量販", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_retail.html"},
    {"name": "線上購物", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_shopping.html"},
    {"name": "更多優惠", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_others.html"},
]

# 提取優惠的 JavaScript
EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    // 模式 1: 精選優惠頁面 (使用 a.twrbo-c-thumb)
    const style1 = Array.from(document.querySelectorAll('a.twrbo-c-thumb'));
    style1.forEach(el => {
        let title = el.getAttribute('title') || el.innerText.trim();
        let href = el.getAttribute('href');
        if (title && href && href !== '#' && !seen.has(title)) {
            seen.add(title);
            offers.push({ title, url: href });
        }
    });

    // 模式 2: 分類明細頁面 (使用 ng-scope 卡片結構)
    const allDivs = Array.from(document.querySelectorAll('div.ng-scope, li.ng-scope'));
    allDivs.forEach(card => {
        const titleEl = card.querySelector('h3, .twrbo-c-h3, strong');
        if (!titleEl) return;
        
        let title = titleEl.innerText.trim();
        if (!title || seen.has(title)) return;
        
        const links = Array.from(card.querySelectorAll('a'));
        let activityLink = links.find(a => {
            const href = a.getAttribute('href') || '';
            if (href.startsWith('tel:')) return false;
            return (a.innerText.includes('活動網頁') || 
                    a.innerText.includes('網址') ||
                    a.classList.contains('twrbo-h-linkEffect-url--gy')) &&
                   href.startsWith('http');
        });
        
        if (!activityLink) {
            activityLink = links.find(a => {
                const href = a.getAttribute('href') || '';
                return href.startsWith('http') && !href.includes('ctbcbank.com/twrbo');
            });
        }
        
        let href = activityLink ? activityLink.getAttribute('href') : null;
        if (title && href && href !== '#') {
            seen.add(title);
            offers.push({ title, url: href });
        }
    });

    // 模式 3: 使用 twrbo-l-productCard
    const style3 = Array.from(document.querySelectorAll('.twrbo-l-productCard'));
    style3.forEach(card => {
        const titleEl = card.querySelector('.twrbo-c-h3, h3');
        const links = Array.from(card.querySelectorAll('a'));
        let activityLink = links.find(a => {
            const href = a.getAttribute('href') || '';
            return !href.startsWith('tel:') && a.innerText.includes('活動網頁') && href.startsWith('http');
        }) || links.find(a => {
            const href = a.getAttribute('href') || '';
            return href.startsWith('http') && !href.startsWith('tel:');
        });
        
        let title = titleEl ? titleEl.innerText.trim() : null;
        let href = activityLink ? activityLink.getAttribute('href') : null;
        
        if (title && href && href !== '#' && !href.startsWith('tel:') && !seen.has(title)) {
            seen.add(title);
            offers.push({ title, url: href });
        }
    });

    return offers.map(o => {
        let finalUrl = o.url;
        if (finalUrl && !finalUrl.startsWith('http')) {
            try {
                finalUrl = new URL(finalUrl, window.location.href).href;
            } catch(e) {
                finalUrl = window.location.origin + finalUrl;
            }
        }
        return { title: o.title, url: finalUrl };
    });
}
"""

CHECK_NEXT_PAGE_SCRIPT = """
() => {
    const nextBtn = document.querySelector('.twrbo-c-controller--next');
    if (!nextBtn) return { hasNext: false };
    
    const isDisabled = nextBtn.classList.contains('ng-hide') || 
                       nextBtn.classList.contains('disabled') ||
                       nextBtn.getAttribute('disabled') !== null ||
                       nextBtn.style.display === 'none';
    
    return { hasNext: !isDisabled, selector: '.twrbo-c-controller--next' };
}
"""


class CTBCScraper(BaseScraper):
    """中國信託爬蟲"""
    
    def __init__(self):
        super().__init__("中國信託")
    
    async def scrape(self, page) -> List[Dict]:
        """爬取中國信託所有分類優惠"""
        print(f"\n{'='*50}")
        print(f"開始爬取: {self.bank_name}")
        print("="*50)
        
        all_offers = []
        
        for cat in CATEGORIES:
            print(f"\n  分類: {cat['name']}...")
            try:
                await page.goto(cat["url"], wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)
                
                # 先嘗試在主文檔提取 (精選優惠頁面的內容在主文檔)
                main_offers = await page.evaluate(EXTRACT_SCRIPT)
                
                if main_offers and len(main_offers) > 0:
                    print(f"    從主文檔找到 {len(main_offers)} 筆")
                    existing_titles = {o["title"] for o in all_offers}
                    for offer in main_offers:
                        if offer["title"] not in existing_titles:
                            offer["bank"] = self.bank_name
                            offer["category"] = cat["name"]
                            all_offers.append(offer)
                
                # 再嘗試取得 iframe (其他分類頁面使用 iframe)
                iframe_element = await page.query_selector("#frameweb")
                if iframe_element:
                    iframe = await iframe_element.content_frame()
                    if iframe:
                        await page.wait_for_timeout(2000)
                        
                        page_num = 1
                        max_pages = 20
                        
                        while page_num <= max_pages:
                            # 滾動以觸發延遲載入
                            for _ in range(3):
                                await iframe.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                await page.wait_for_timeout(500)
                            
                            # 提取當前頁面的優惠
                            current_offers = await iframe.evaluate(EXTRACT_SCRIPT)
                            
                            existing_titles = {o["title"] for o in all_offers}
                            for offer in current_offers:
                                if offer["title"] not in existing_titles:
                                    offer["bank"] = self.bank_name
                                    offer["category"] = cat["name"]
                                    all_offers.append(offer)
                            
                            # 檢查是否有下一頁
                            next_page_info = await iframe.evaluate(CHECK_NEXT_PAGE_SCRIPT)
                            
                            if not next_page_info.get("hasNext", False):
                                break
                            
                            try:
                                next_btn = await iframe.query_selector(".twrbo-c-controller--next")
                                if next_btn:
                                    await next_btn.click()
                                    await page.wait_for_timeout(2000)
                                    page_num += 1
                                else:
                                    break
                            except Exception:
                                break
                
                print(f"    累計: {len(all_offers)} 筆")
                
            except Exception as e:
                print(f"    錯誤: {e}")
        
        print(f"\n  {self.bank_name}總計: {len(all_offers)} 筆")
        return self.deduplicate(all_offers)
