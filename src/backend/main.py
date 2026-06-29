from fastapi import FastAPI, Response, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import sys
import os
import requests
from src.backend.core.database import fetch_offers, get_filters
from geopy.geocoders import Nominatim
import subprocess
import json

app = FastAPI(title="信用卡優惠 API")
geolocator = Nominatim(user_agent="ccard_war_room")

# 動態設定允許的 CORS 網域（從環境變數 ALLOWED_ORIGINS 讀取）
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_raw:
    allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",")]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 金鑰驗證依賴項
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    expected_key = os.environ.get("API_KEY")
    # 如果環境變數中設定了 API_KEY，則前端發送的 x_api_key 必須與之相符
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="無權存取：無效或未提供 API 金鑰 (X-API-Key)")

@app.get("/api/image-proxy")
async def image_proxy(url: str):
    if not url:
        return Response(status_code=400)
    
    # 根據網址決定 Referer 繞過防盜連
    referer = ""
    if "ctbcbank.com" in url:
        referer = "https://www.ctbcbank.com/"
    elif "cathay-cube.com" in url or "cathaybk.com" in url:
        referer = "https://www.cathaybk.com.tw/"
    elif "ubot.com.tw" in url:
        referer = "https://card.ubot.com.tw/"
    elif "esunbank.com" in url:
        referer = "https://www.esunbank.com/"
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type", "image/jpeg")
            return Response(content=r.content, media_type=content_type)
        else:
            return Response(status_code=r.status_code)
    except Exception as e:
        return Response(status_code=500)

@app.get("/api/map-locate")
async def get_location(query: str):
    clean_query = query.replace("中國信託", "").replace("國泰世華", "").replace("聯邦銀行", "").replace("玉山銀行", "").replace("優惠", "").strip()
    if len(clean_query) < 2:
        clean_query = query
        
    location = geolocator.geocode(clean_query + " 台北市")
    if location:
        return {"lat": location.latitude, "lon": location.longitude}
    return {"error": "Location not found"}

@app.get("/api/filters")
async def get_all_filters():
    # 直接回傳從 database.py 處理好的完整結果
    return get_filters()

@app.get("/api/status")
async def get_status():
    status_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "status.json")
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "空閒"}

@app.post("/api/refresh", dependencies=[Depends(verify_api_key)])
async def refresh_data():
    try:
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        scraper_script = os.path.join(project_dir, "bank_offers_scraper.py")
        # 建立 status.json 初始狀態
        with open(os.path.join(project_dir, "status.json"), "w", encoding="utf-8") as f:
            import json
            json.dump({"status": "更新中..."}, f, ensure_ascii=False)
            
        subprocess.Popen([sys.executable, scraper_script], cwd=project_dir)
        return {"status": "開始更新"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/offers")
async def get_offers(
    search: Optional[str] = None,
    bank: Optional[str] = None,
    category: Optional[str] = None
):
    return fetch_offers(search, bank, category)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
