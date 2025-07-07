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


def main():
    
    print("Starting safe ride rain data collection...")
    
    start = coordinate(34.72389503571166, 137.72146106062718)
    goal = coordinate(34.67685020650209, 137.75257104803205)
    print(f"Start: {start}")
    print(f"Goal: {goal}")
    
    bbox = bounding_box(start, goal)
    print(f"Bounding box: {bbox}")
    
    grid_coordinates = bbox.create_grid()
    print(f"Generated {len(grid_coordinates)} grid coordinates")
    
    # 日時を正しいdatetimeオブジェクトに変換（明示的にJSTを指定）
    JST = timezone(timedelta(hours=9))
    target_date = datetime.now(JST)
    print(f"Target date (JST): {target_date}")
    print(f"Target date (UTC): {target_date.astimezone(timezone.utc)}")
    print(f"Local time: {datetime.now()}")
    
    rain_data = RainData(appid=YAHOO_API_KEY)
    print("Fetching rain data...")
    
    try:
        rain_data.get(coordinate_list=grid_coordinates, date=target_date)
        print("Rain data successfully retrieved and saved to rain_data.json")
    except Exception as e:
        print(f"Error fetching rain data: {e}")
    try:
        geojson = rain_data.to_geojson()
        with open('rain_data.geojson', 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        print("GeoJSON data successfully written to rain_data.json")
    except Exception as e:
        print(f"Error converting rain data to GeoJSON: {e}")
    try:
        geojson = rain_data.to_request_json()
        with open('rain_data.json', 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        print("GeoJSON data successfully written to rain_data.json")
    except Exception as e:
        print(f"Error converting rain data to GeoJSON: {e}")

if __name__ == "__main__":
    main()