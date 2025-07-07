import sys
import os
import json
from datetime import datetime, timezone, timedelta

SRC_PATH = './src'
YAHOO_API_KEY = os.environ.get('YAHOO_API_KEY')

if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

from src.modules.values import bounding_box, coordinate
from src.modules.rain_data import RainData
from src.core.logger import get_logger

logger = get_logger(__name__)


def main():
    
    logger.info("Starting safe ride rain data collection...")
    
    start = coordinate(34.72389503571166, 137.72146106062718)
    goal = coordinate(34.67685020650209, 137.75257104803205)
    logger.info("Start: %s", start)
    logger.info("Goal: %s", goal)
    
    bbox = bounding_box(start, goal)
    logger.debug("Bounding box: %s", bbox)
    
    grid_coordinates = bbox.create_grid()
    logger.debug("Generated %d grid coordinates", len(grid_coordinates))
    
    # 日時を正しいdatetimeオブジェクトに変換（明示的にJSTを指定）
    JST = timezone(timedelta(hours=9))
    target_date = datetime.now(JST)
    logger.debug("Target date (JST): %s", target_date)
    logger.debug("Target date (UTC): %s", target_date.astimezone(timezone.utc))
    logger.debug("Local time: %s", datetime.now())
    
    rain_data = RainData(appid=YAHOO_API_KEY)
    logger.info("Fetching rain data...")
    
    try:
        rain_data.get(coordinate_list=grid_coordinates, date=target_date)
        logger.info("Rain data successfully retrieved and saved to rain_data.json")
    except Exception as e:
        logger.error("Error fetching rain data: %s", e)
    try:
        geojson = rain_data.to_geojson()
        with open('rain_data.geojson', 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        logger.info("GeoJSON data successfully written to rain_data.json")
    except Exception as e:
        logger.error("Error converting rain data to GeoJSON: %s", e)
    try:
        geojson = rain_data.to_request_json()
        with open('rain_data.json', 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        logger.info("GeoJSON data successfully written to rain_data.json")
    except Exception as e:
        logger.error("Error converting rain data to GeoJSON: %s", e)

if __name__ == "__main__":
    main()

