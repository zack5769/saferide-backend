import os
import json
import requests
from datetime import datetime, timezone, timedelta

from .rain_data import RainData
from .values import bounding_box, coordinate, tile
from src.core.logger import get_logger

logger = get_logger(__name__)

YAHOO_API_KEY = os.environ.get('YAHOO_API_KEY')
JST = timezone(timedelta(hours=9))

def get_rain_info(start: str, goal: str):
    """
    指定された開始地点と目的地の間の雨データを取得する関数。
    
    Args:
        start (str): 開始地点の座標（例: "35.6762,139.6503"）
        goal (str): 目的地の座標（例: "35.7169,139.7774"）
        
    Returns:
        dict: 雨データを含む辞書
    """

    logger.info("Fetching rain info between %s and %s", start, goal)

    s_lat, slon = map(float, start.split(','))
    g_lat, glon = map(float, goal.split(','))

    now = datetime.now(JST)

    start_coord = coordinate(s_lat, slon)
    goal_coord = coordinate(g_lat, glon)
    
    bbox = bounding_box(start_coord, goal_coord)
    # grid_coordinates = bbox.create_grid()
    tile_list = bbox.create_tiles(zoom_level=13)
    tile_center_coord_list = bbox.get_tile_centers(tile_list)
    
    rain_data = RainData(YAHOO_API_KEY)
    rain_data.get(coordinate_list=tile_center_coord_list, date=now)
    
    rain_request_data, rain_tile_list = rain_data.to_request_json()

    logger.info("Rain tiles detected: %d", rain_data.num_rain_tiles)
    
    result = rain_request_data
    logger.debug("get_rain_info result: %s", json.dumps(result, ensure_ascii=False))
    return result, rain_tile_list


def get_route_from_graphhopper(start: str, goal: str, rain_avoidance_data: dict = None):
    """
    GraphHopperサーバーにルートリクエストを送信し、雨エリア回避を考慮したルート情報を取得する。
    
    Args:
        start (str): 開始地点の座標（例: "35.6762,139.6503"）
        goal (str): 目的地の座標（例: "35.7169,139.7774"）
        rain_avoidance_data (dict): 雨エリア回避用のpriority・areas設定
        
    Returns:
        dict: GraphHopperからのルート情報
    """
    
    # GraphHopperエンドポイント（Dockerネットワーク内のサービス名を使用）
    url = "http://graphhopper:8989/route"
    
    # リクエストボディを構築
    # 座標をlon, lat形式に変換
    start_lat, start_lon = map(float, start.split(','))
    goal_lat, goal_lon = map(float, goal.split(','))
    
    request_body = {
        "points": [
            [start_lon, start_lat],  # [lon, lat]
            [goal_lon, goal_lat]     # [lon, lat]
        ],
        "profile": "car",
        "points_encoded": False,
        "ch.disable": True
    }
    
    # 雨エリア回避設定を追加
    if rain_avoidance_data and "priority" in rain_avoidance_data and "areas" in rain_avoidance_data:
        request_body["custom_model"] = {
            "priority": rain_avoidance_data["priority"],
            "areas": rain_avoidance_data["areas"]
        }
    
    try:
        logger.info("Sending route request to GraphHopper: %s", url)
        logger.debug("Request body: %s", json.dumps(request_body, indent=2, ensure_ascii=False))
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=request_body, headers=headers, timeout=30)
        
        if response.status_code == 200:
            route_data = response.json()
            logger.info("Route calculation successful")
            return route_data
        else:
            # GraphHopperからのエラーレスポンスを詳細に処理
            try:
                error_json = response.json()
                if "message" in error_json:
                    error_detail = error_json["message"]
                    # GraphHopperの具体的なエラーメッセージを含める
                    if "hints" in error_json and error_json["hints"]:
                        error_detail += " Details: " + "; ".join([
                            hint.get("message", "") for hint in error_json["hints"]
                        ])
                else:
                    error_detail = response.text
            except (json.JSONDecodeError, ValueError):
                error_detail = response.text
            
            error_msg = f"GraphHopper API error: {response.status_code} - {error_detail}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status_code": response.status_code,
                "graphhopper_response": error_json if 'error_json' in locals() else response.text
            }
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request to GraphHopper failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg
        }
