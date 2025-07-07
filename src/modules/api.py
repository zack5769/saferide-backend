from fastapi import FastAPI

from .service import get_route_from_graphhopper, get_rain_info


app = FastAPI()

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
    rain_data = get_rain_info(start, goal)
    return get_route_from_graphhopper(start, goal, rain_data)