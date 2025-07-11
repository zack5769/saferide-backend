from fastapi import FastAPI, Path, HTTPException
from starlette.middleware.cors import CORSMiddleware
from typing import Dict, Any

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
         description="雨を考慮したルートを取得する",
         response_model=Dict[str, Any])
async def route(
    start: str = Path(
        ...,
        description="開始地点の座標（緯度,経度）",
        example="35.6762,139.6503"
    ),
    goal: str = Path(
        ...,
        description="目的地の座標（緯度,経度）",
        example="35.7169,139.7774"
    )
):
    """
    指定された開始地点と目的地の間の雨データを取得するエンドポイント。
    
    Args:
        start (str): 開始地点の座標（例: "35.6762,139.6503"）
        goal (str): 目的地の座標（例: "35.7169,139.7774"）
        
    Returns:
        dict: 雨データとルート情報を含む辞書
        
    Raises:
        HTTPException: GraphHopperへのリクエストが失敗した場合
    """
    logger.info("/route called with start=%s goal=%s", start, goal)
    rain_data, rain_tile_list = get_rain_info(start, goal)
    response = get_route_from_graphhopper(start, goal, rain_data)
    
    # GraphHopperからのエラーレスポンスをチェック
    if "error" in response:
        status_code = response.get("status_code", 500)
        error_message = response["error"]
        logger.error("GraphHopper error: %s", error_message)
        
        # GraphHopperのAPIエラーの場合は400番台エラーとして返す
        if status_code in [400, 404, 422]:
            raise HTTPException(status_code=status_code, detail=error_message)
        else:
            # その他のエラーは500として返す
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_message}")
    
    logger.debug("Route response: %s", response)
    return {"response": response, "rain_tile_list": rain_tile_list}


@app.get("/normal_route/{start}/{goal}",
         description="通常のルートを取得する",
         response_model=Dict[str, Any])
async def normal_route(
    start: str = Path(
        ...,
        description="開始地点の座標（緯度,経度）",
        example="35.6762,139.6503"
    ),
    goal: str = Path(
        ...,
        description="目的地の座標（緯度,経度）",
        example="35.7169,139.7774"
    )
):
    """
    指定された開始地点と目的地の間の通常のルートを取得するエンドポイント。
    
    Args:
        start (str): 開始地点の座標（例: "35.6762,139.6503"）
        goal (str): 目的地の座標（例: "35.7169,139.7774"）
        
    Returns:
        dict: 通常のルート情報を含む辞書
        
    Raises:
        HTTPException: GraphHopperへのリクエストが失敗した場合
    """
    logger.info("/normal_route called with start=%s goal=%s", start, goal)
    response = get_route_from_graphhopper(start, goal)
    
    # GraphHopperからのエラーレスポンスをチェック
    if "error" in response:
        status_code = response.get("status_code", 500)
        error_message = response["error"]
        logger.error("GraphHopper error: %s", error_message)
        
        # GraphHopperのAPIエラーの場合は400番台エラーとして返す
        if status_code in [400, 404, 422]:
            raise HTTPException(status_code=status_code, detail=error_message)
        else:
            # その他のエラーは500として返す
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_message}")
    
    logger.debug("Normal route response: %s", response)
    return response