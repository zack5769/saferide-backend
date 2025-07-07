import json
import requests
from datetime import datetime

from .values import coordinate
from src.core.logger import get_logger

logger = get_logger(__name__)

class RainData:
    def __init__(self, appid: str):
        self.appid = appid
        self.num_rain_tiles = 0


    def get(self, coordinate_list: list[coordinate], date: datetime):
        date_str = date.strftime('%Y%m%d%H%M')
        
        # coordinate_listを10個ずつに分割
        chunk_size = 10
        chunks = [coordinate_list[i:i + chunk_size] for i in range(0, len(coordinate_list), chunk_size)]
        
        merged_data = {"Feature": []}
        total_features = 0


        # URLは一度に10座標が上限だった
        for chunk_index, chunk in enumerate(chunks):
            coord_pairs = ' '.join([f'{coord.lon},{coord.lat}' for coord in chunk])
            url = f'https://map.yahooapis.jp/weather/V1/place?coordinates={coord_pairs}&appid={self.appid}&output=json&date={date_str}'
                
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    logger.error("Error fetching data for chunk %d: %s - %s", chunk_index + 1, response.status_code, response.text)
                    continue
                
                chunk_data = response.json()
                
                if "Feature" in chunk_data:
                    features_count = len(chunk_data["Feature"])
                    merged_data["Feature"].extend(chunk_data["Feature"])
                    total_features += features_count
                else:
                    pass
                    
            except Exception as e:
                logger.error("Exception while processing chunk %d: %s", chunk_index + 1, e)
                continue
        
        self.data = merged_data
        


    def to_geojson(self, grid_size: float = 0.04):
        """
        雨が降っているグリッドのGeoJSON形式のFeatureCollectionを生成
        10分ごとの降雨予報（01ビット配列）を追加←もしかしたら今後つかうかも

        Args:
            grid_size (float): グリッドのサイズ
        Returns:
            dict: GeoJSON形式のFeatureCollection
        """
        features = []
        for feat in self.data.get("Feature", []):
            try:
                lon, lat = map(float, feat["Geometry"]["Coordinates"].split(","))
                weather_list = feat["Property"]["WeatherList"]["Weather"]

                # 予報情報のビット配列（0は晴れ, 1が雨）
                rain_forecast_bits = [
                    1 if (w.get("Type") == "forecast" and w.get("Rainfall", 0) > 0) else 0
                    for w in weather_list if w.get("Type") == "forecast"
                ]
                # いずれかでrainfall>0ならポリゴン作成
                if any(w.get("Rainfall", 0) > 0 for w in weather_list):
                    self.num_rain_tiles += 1
                    half = grid_size / 2
                    poly = [
                        [round(lon - half, 6), round(lat - half, 6)],
                        [round(lon - half, 6), round(lat + half, 6)],
                        [round(lon + half, 6), round(lat + half, 6)],
                        [round(lon + half, 6), round(lat - half, 6)],
                        [round(lon - half, 6), round(lat - half, 6)]
                    ]
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [poly]
                        },
                        "properties": {
                            "id": feat.get("Id"),
                            "rain": True,
                            "rain_forecast_bits": rain_forecast_bits
                        }
                    })
            except Exception as e:
                logger.warning("Skip feature due to error: %s", e)
                continue
        return {
            "type": "FeatureCollection",
            "features": features
        }
    

    def to_request_json(self):
        """
        RainDataのGeoJSONをGraphHopperのリクエスト形式に変換
        雨が降るエリアを回避するためのpriority設定とareas定義を生成
        
        Returns:
            dict: GraphHopperリクエスト用のpriority・areas設定
        """
        geojson = self.to_geojson()
        features = geojson.get("features", [])
        
        # priority設定を生成（各エリアのmultiply_byを0にして回避）
        priority = []
        modified_features = []
        
        for i, feature in enumerate(features):
            # priorityにif条件を追加
            priority.append({
                "if": f"in_{i}",
                "multiply_by": "0"
            })
            
            # featureにidを追加し、propertiesを空にする
            modified_feature = {
                "type": "Feature",
                "id": str(i),
                "properties": {},
                "geometry": feature["geometry"]
            }
            modified_features.append(modified_feature)
        
        return {
            "priority": priority,
            "areas": {
                "type": "FeatureCollection",
                "features": modified_features
            }
        }

