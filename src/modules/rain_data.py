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
        logger.debug("Starting rain data fetch for %d coordinates on %s", len(coordinate_list), date_str)
        
        # coordinate_listを10個ずつに分割
        chunk_size = 10
        chunks = [coordinate_list[i:i + chunk_size] for i in range(0, len(coordinate_list), chunk_size)]
        logger.debug("Split coordinates into %d chunks of size %d", len(chunks), chunk_size)
        
        merged_data = {"Feature": []}
        total_features = 0


        # URLは一度に10座標が上限だった
        for chunk_index, chunk in enumerate(chunks):
            coord_pairs = ' '.join([f'{coord.lon},{coord.lat}' for coord in chunk])
            url = f'https://map.yahooapis.jp/weather/V1/place?coordinates={coord_pairs}&appid={self.appid}&output=json&date={date_str}'
            logger.debug("Processing chunk %d/%d with %d coordinates", chunk_index + 1, len(chunks), len(chunk))
            logger.debug("Request URL: %s", url)
                
            try:
                response = requests.get(url)
                logger.debug("Response status: %d for chunk %d", response.status_code, chunk_index + 1)
                
                if response.status_code != 200:
                    logger.error("Error fetching data for chunk %d: %s - %s", chunk_index + 1, response.status_code, response.text)
                    continue
                
                chunk_data = response.json()
                logger.debug("Received JSON data for chunk %d, data keys: %s", chunk_index + 1, list(chunk_data.keys()))
                
                if "Feature" in chunk_data:
                    features_count = len(chunk_data["Feature"])
                    merged_data["Feature"].extend(chunk_data["Feature"])
                    total_features += features_count
                    logger.debug("Added %d features from chunk %d, total features: %d", features_count, chunk_index + 1, total_features)
                else:
                    logger.debug("No 'Feature' key found in chunk %d response", chunk_index + 1)
                    
            except Exception as e:
                logger.error("Exception while processing chunk %d: %s", chunk_index + 1, e)
                continue
        
        self.data = merged_data
        logger.debug("Rain data fetch completed. Total features: %d", total_features)
        


    def to_geojson(self, grid_size: float = 0.04):
        """
        雨が降っているグリッドのGeoJSON形式のFeatureCollectionを生成
        10分ごとの降雨予報（01ビット配列）を追加←もしかしたら今後つかうかも

        Args:
            grid_size (float): グリッドのサイズ
        Returns:
            dict: GeoJSON形式のFeatureCollection
        """
        logger.debug("Converting rain data to GeoJSON with grid_size: %f", grid_size)
        features = []
        processed_features = 0
        rain_features = 0
        
        for feat in self.data.get("Feature", []):
            processed_features += 1
            try:
                lon, lat = map(float, feat["Geometry"]["Coordinates"].split(","))
                weather_list = feat["Property"]["WeatherList"]["Weather"]
                logger.debug("Processing feature %d at coordinates (%f, %f)", processed_features, lon, lat)

                # 予報情報のビット配列（0は晴れ, 1が雨）
                rain_forecast_bits = [
                    1 if (w.get("Type") == "forecast" and w.get("Rainfall", 0) > 0) else 0
                    for w in weather_list if w.get("Type") == "forecast"
                ]
                
                # 降雨量の詳細をログ出力
                rainfall_values = [w.get("Rainfall", 0) for w in weather_list]
                logger.debug("Rainfall values for feature %d: %s", processed_features, rainfall_values)
                
                # いずれかでrainfall>0ならポリゴン作成
                if any(w.get("Rainfall", 0) > 0 for w in weather_list):
                    rain_features += 1
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
                    logger.debug("Created rain polygon for feature %d", processed_features)
                else:
                    logger.debug("No rain detected for feature %d", processed_features)
                    
            except Exception as e:
                logger.warning("Skip feature %d due to error: %s", processed_features, e)
                continue
        
        logger.debug("GeoJSON conversion completed. Processed: %d features, Rain features: %d", processed_features, rain_features)
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
        logger.debug("Converting rain data to GraphHopper request format")
        geojson = self.to_geojson()
        features = geojson.get("features", [])
        logger.debug("Got %d features from GeoJSON conversion", len(features))
        
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
            logger.debug("Created priority rule and modified feature for area %d", i)
        
        result = {
            "priority": priority,
            "areas": {
                "type": "FeatureCollection",
                "features": modified_features
            }
        }
        logger.debug("GraphHopper request format conversion completed. Priority rules: %d, Areas: %d", len(priority), len(modified_features))
        return result

