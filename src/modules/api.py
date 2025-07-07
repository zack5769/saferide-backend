from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .service import get_route_from_graphhopper, get_rain_info
from src.core.logger import get_logger

logger = get_logger(__name__)


app = FastAPI()

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では具体的なドメインを指定することを推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/route/{start}/{goal}",
         description="雨を考慮したルートを取得する")
async def route(start: str, goal: str):
    """
    指定された開始地点と目的地の間の雨データを取得するエンドポイント。
    
    Args:
        start (str): 開始地点の座標（例: "35.6762,139.6503"）
        goal (str): 目的地の座標（例: "35.7169,139.7774"）
        
    Returns:
        dict: 雨データとルート情報を含む辞書
    """
    logger.info("/route called with start=%s goal=%s", start, goal)
    rain_data = get_rain_info(start, goal)
    response = get_route_from_graphhopper(start, goal, rain_data)
    logger.debug("Route response: %s", response)
    return response


@app.get("/normal_route/{start}/{goal}",
         description="通常のルートを取得する")
async def normal_route(start: str, goal: str):
    """
    指定された開始地点と目的地の間の通常のルートを取得するエンドポイント。
    
    Args:
        start (str): 開始地点の座標（例: "35.6762,139.6503"）
        goal (str): 目的地の座標（例: "35.7169,139.7774"）
        
    Returns:
        dict: 通常のルート情報を含む辞書
    """
    logger.info("/normal_route called with start=%s goal=%s", start, goal)
    response = get_route_from_graphhopper(start, goal)
    logger.debug("Normal route response: %s", response)
    return response