# -*- coding: utf-8 -*-
"""
銀行信用卡優惠統一爬蟲 v1
- 中國信託 (CTBC)
- 國泰世華 (Cathay)
- 聯邦銀行 (Union Bank / UBot)
"""

import asyncio
import json
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

# 檢測是否在 CI 環境 (GitHub Actions)
IS_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

# ============================================================
# 中國信託 (CTBC) 設定
# ============================================================
CTBC_CATEGORIES = [
    {"name": "精選．中信卡優惠", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_special_offer.html"},
    {"name": "餐飲優惠", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_food.html"},
    {"name": "旅遊玩家", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_travel.html"},
    {"name": "百貨藥妝", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_grocery.html"},
    {"name": "行動支付", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_payment.html"},
    {"name": "超商量販", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_retail.html"},
    {"name": "線上購物", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_shopping.html"},
    {"name": "更多優惠", "url": "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_offer_others.html"},
]

# 中國信託提取優惠的 JavaScript
CTBC_EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    // 模式 1: 精選優惠頁面 (使用 a.twrbo-c-thumb)
    const style1 = Array.from(document.querySelectorAll('a.twrbo-c-thumb'));
    style1.forEach(el => {
        let title = el.getAttribute('title') || el.innerText.trim();
        let href = el.getAttribute('href');
        
        let image = null;
        // 1. 嘗試找 img 標籤
        let img = el.querySelector('img');
        if (img) image = img.src;
        
        // 2. 嘗試找 style background-image
        if (!image) {
            let style = el.getAttribute('style');
            if (style) {
                let match = style.match(/background-image:\s*url\(['"]?(.*?)['"]?\)/);
                if (match) image = match[1];
            }
        }
        
        // 3. 嘗試找 data-src (常見於 span)
        if (!image) {
            let span = el.querySelector('[data-src]');
            if (span) image = span.getAttribute('data-src');
        }

        if (title && href && href !== '#' && !seen.has(title)) {
            seen.add(title);
            offers.push({ title, url: href, image });
        }
    });

    // 模式 2: 分類明細頁面 (使用 ng-scope 卡片結構)
    const allDivs = Array.from(document.querySelectorAll('div.ng-scope, li.ng-scope'));
    allDivs.forEach(card => {
        const titleEl = card.querySelector('h3, .twrbo-c-h3, strong');
        if (!titleEl) return;
        
        let title = titleEl.innerText.trim();
        if (!title || seen.has(title)) return;
        
        // 找圖片
        let img = card.querySelector('img');
        let image = img ? img.src : null;
        
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
            offers.push({ title, url: href, image });
        }
    });

    // 模式 3: 使用 twrbo-l-productCard
    const style3 = Array.from(document.querySelectorAll('.twrbo-l-productCard'));
    style3.forEach(card => {
        const titleEl = card.querySelector('.twrbo-c-h3, h3');
        let img = card.querySelector('img');
        let image = img ? img.src : null;
        
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
            offers.push({ title, url: href, image });
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
        // 處理圖片相對路徑
        let finalImage = o.image;
        if (finalImage && !finalImage.startsWith('http')) {
            try {
                finalImage = new URL(finalImage, window.location.href).href;
            } catch(e) {
                finalImage = null;
            }
        }
        return { title: o.title, url: finalUrl, image: finalImage };
    });
}
"""

CTBC_CHECK_NEXT_PAGE_SCRIPT = """
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


# ============================================================
# 國泰世華 (Cathay) 設定
# ============================================================
CATHAY_URL = "https://www.cathay-cube.com.tw/cathaybk/personal/event/overview"

CATHAY_EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    // 嘗試多種選擇器
    const cards = document.querySelectorAll('a.eventcard, a[class*="eventcard"], div[class*="event"] a[href*="/event/"]');
    cards.forEach(card => {
        // 找圖片
        const img = card.querySelector('img');
        let image = img ? img.src : null;
        
        // 找標題 (嘗試多種方式)
        let title = null;
        const titleEl = card.querySelector('h3, h4, .title, [class*="title"]');
        if (titleEl) {
            title = titleEl.innerText.trim();
        } else {
            // 從 alt 屬性或 innerText 取得
            title = (img && img.alt) || card.innerText.trim().split('\\n')[0];
        }
        
        let href = card.getAttribute('href');
        
        if (title && href && !seen.has(title) && title.length > 2) {
            seen.add(title);
            // 處理相對路徑
            if (!href.startsWith('http')) {
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


# ============================================================
# 聯邦銀行 (UBot) 設定
# ============================================================
UBOT_CATEGORIES = [
    {"name": "強打優惠", "url": "https://card.ubot.com.tw/CardActivity?category=強打優惠"},
    {"name": "卡片優惠", "url": "https://card.ubot.com.tw/CardActivity?category=卡片優惠"},
    {"name": "百貨零售", "url": "https://card.ubot.com.tw/CardActivity?category=百貨零售"},
    {"name": "旅遊優惠", "url": "https://card.ubot.com.tw/CardActivity?category=旅遊優惠"},
    {"name": "交通汽修", "url": "https://card.ubot.com.tw/CardActivity?category=交通汽修"},
    {"name": "網購數位", "url": "https://card.ubot.com.tw/CardActivity?category=網購數位"},
    {"name": "生活繳費", "url": "https://card.ubot.com.tw/CardActivity?category=生活繳費"},
    {"name": "購物娛樂", "url": "https://card.ubot.com.tw/CardActivity?category=購物娛樂"},
]

UBOT_EXTRACT_SCRIPT = """
() => {
    const offers = [];
    const seen = new Set();
    
    document.querySelectorAll('.card').forEach(card => {
        // 找圖片
        const img = card.querySelector('img');
        let image = img ? img.src : null;
        
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
        if (image && !image.startsWith('http')) {
            image = window.location.origin + image;
        }
        
        if (title && href) {
            seen.add(title);
            offers.push({ title, url: href, image });
        }
    });
    
    return offers;
}
"""

UBOT_GET_PAGES_SCRIPT = """
() => {
    const pages = document.querySelectorAll('.pagingNumber');
    return Array.from(pages).map(p => p.innerText.trim()).filter(t => t);
}
"""


# ============================================================
# 爬蟲功能
# ============================================================

async def scrape_ctbc(page) -> list:
    """爬取中國信託所有分類優惠"""
    print("\n" + "=" * 50)
    print("開始爬取: 中國信託 (CTBC)")
    print("=" * 50)
    
    all_offers = []
    
    for cat in CTBC_CATEGORIES:
        print(f"\n  分類: {cat['name']}...")
        try:
            await page.goto(cat["url"], wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # 先嘗試在主文檔提取 (精選優惠頁面的內容在主文檔)
            main_offers = await page.evaluate(CTBC_EXTRACT_SCRIPT)
            
            if main_offers and len(main_offers) > 0:
                print(f"    從主文檔找到 {len(main_offers)} 筆")
                existing_titles = {o["title"] for o in all_offers}
                for offer in main_offers:
                    if offer["title"] not in existing_titles:
                        offer["bank"] = "中國信託"
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
                        current_offers = await iframe.evaluate(CTBC_EXTRACT_SCRIPT)
                        
                        existing_titles = {o["title"] for o in all_offers}
                        for offer in current_offers:
                            if offer["title"] not in existing_titles:
                                offer["bank"] = "中國信託"
                                offer["category"] = cat["name"]
                                all_offers.append(offer)
                        
                        # 檢查是否有下一頁
                        next_page_info = await iframe.evaluate(CTBC_CHECK_NEXT_PAGE_SCRIPT)
                        
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
    
    print(f"\n  中國信託總計: {len(all_offers)} 筆")
    return all_offers


async def scrape_cathay(page) -> list:
    """爬取國泰世華優惠"""
    print("\n" + "=" * 50)
    print("開始爬取: 國泰世華 (Cathay)")
    print("=" * 50)
    
    all_offers = []
    
    try:
        await page.goto(CATHAY_URL, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(8000)  # 增加等待時間讓 React 完全渲染
        
        # 先滾動幾次觸發內容載入
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
        
        # 檢查目前有多少卡片
        initial_count = await page.evaluate("document.querySelectorAll('a.eventcard, a[class*=\"eventcard\"]').length")
        print(f"  初始載入: {initial_count} 筆")
        
        # 持續點擊「展開更多」直到沒有更多
        max_clicks = 50  # 增加最大點擊次數 (共140項需要更多次)
        for i in range(max_clicks):
            # 滾動到底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(800)
            
            # 找「展開更多」按鈕 (嘗試多種選擇器)
            load_more = await page.query_selector('a.dot-animate-wrapper')
            if not load_more:
                load_more = await page.query_selector('[class*="dot-animate"]')
            if not load_more:
                load_more = await page.query_selector('text=展開更多')
            if not load_more:
                # 嘗試含有「展開」文字的連結
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
        offers = await page.evaluate(CATHAY_EXTRACT_SCRIPT)
        
        for offer in offers:
            offer["bank"] = "國泰世華"
            offer["category"] = "信用卡優惠"
            all_offers.append(offer)
        
        print(f"\n  國泰世華總計: {len(all_offers)} 筆")
        
    except Exception as e:
        print(f"  錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    return all_offers


async def scrape_ubot(page) -> list:
    """爬取聯邦銀行所有分類優惠"""
    print("\n" + "=" * 50)
    print("開始爬取: 聯邦銀行 (UBot)")
    print("=" * 50)
    
    all_offers = []
    
    for cat in UBOT_CATEGORIES:
        print(f"\n  分類: {cat['name']}...")
        try:
            await page.goto(cat["url"], wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # 取得頁數
            page_numbers = await page.evaluate(UBOT_GET_PAGES_SCRIPT)
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
                current_offers = await page.evaluate(UBOT_EXTRACT_SCRIPT)
                
                existing_titles = {o["title"] for o in all_offers}
                for offer in current_offers:
                    if offer["title"] not in existing_titles:
                        offer["bank"] = "聯邦銀行"
                        offer["category"] = cat["name"]
                        all_offers.append(offer)
            
            print(f"    累計: {len(all_offers)} 筆")
            
        except Exception as e:
            print(f"    錯誤: {e}")
    
    print(f"\n  聯邦銀行總計: {len(all_offers)} 筆")
    return all_offers


def deduplicate(offers: list) -> list:
    """去除重複"""
    seen = set()
    unique = []
    for o in offers:
        key = (o["bank"], o["title"], o["url"])
        if key not in seen:
            seen.add(key)
            unique.append(o)
    return unique


def save_to_csv(offers: list, filename: str = "all_bank_offers.csv"):
    """儲存為 CSV"""
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["bank", "category", "title", "url", "image"])
        writer.writeheader()
        writer.writerows(offers)
    print(f"已儲存 CSV: {filename}")


def save_to_json(offers: list, filename: str = "all_bank_offers.json"):
    """儲存為 JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"已儲存 JSON: {filename}")


async def main():
    print("=" * 60)
    print("銀行信用卡優惠統一爬蟲")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_offers = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=IS_CI,  # CI 環境用 headless，本機可開視窗
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # 爬取各銀行
        ctbc_offers = await scrape_ctbc(page)
        all_offers.extend(ctbc_offers)
        
        cathay_offers = await scrape_cathay(page)
        all_offers.extend(cathay_offers)
        
        ubot_offers = await scrape_ubot(page)
        all_offers.extend(ubot_offers)
        
        await browser.close()
    
    # 去重
    all_offers = deduplicate(all_offers)
    
    print("\n" + "=" * 60)
    print(f"總計: {len(all_offers)} 筆優惠 (已去重)")
    print("=" * 60)
    
    # 儲存
    save_to_csv(all_offers)
    save_to_json(all_offers)
    
    # 更新資料庫
    try:
        from database import init_db, clear_offers, add_offers
        print("\n正在更新資料庫...")
        init_db()  # 確保資料表存在
        clear_offers()  # 清除舊資料
        add_offers(all_offers)  # 匯入新資料
        print("資料庫更新完成！")
    except Exception as e:
        print(f"資料庫更新失敗: {e}")
    
    # 顯示各銀行統計
    print("\n各銀行統計:")
    from collections import Counter
    bank_counts = Counter(o["bank"] for o in all_offers)
    for bank, count in sorted(bank_counts.items(), key=lambda x: -x[1]):
        print(f"  {bank}: {count} 筆")
    
    print(f"\n完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
