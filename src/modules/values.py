from dataclasses import dataclass
import numpy as np
from typing import List
import math

@dataclass
class coordinate:
    lat: float
    lon: float

    def __post_init__(self):
        self.lat = round(self.lat, 6)
        self.lon = round(self.lon, 6)

@dataclass 
class tile:
    x: int
    y: int
    zoom: int

    def __str__(self):
        return f"Tile(x={self.x}, y={self.y}, zoom={self.zoom})"

    def to_bbox(self):
        """
        このタイルのバウンディングボックス（lon_min, lat_min, lon_max, lat_max）を返す
        Returns:
            (lon_min, lat_min, lon_max, lat_max): バウンディングボックス
        """
        n = 2.0 ** self.zoom
        lon_min = self.x / n * 360.0 - 180.0
        lon_max = (self.x + 1) / n * 360.0 - 180.0
        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (self.y + 1) / n))))
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * self.y / n))))
        return lon_min, lat_min, lon_max, lat_max

    def to_geojson(self):
        """
        このタイルのGeoJSONのPolygonを返す
        Returns:
            dict: GeoJSON形式のポリゴン
        """
        lon_min, lat_min, lon_max, lat_max = self.to_bbox()
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon_min, lat_min],
                        [lon_min, lat_max],
                        [lon_max, lat_max],
                        [lon_max, lat_min],
                        [lon_min, lat_min]
                    ]]
                },
                "properties": {
                    "x": self.x,
                    "y": self.y,
                    "z": self.zoom
                }
            }]
        }
        return geojson

@dataclass
class bounding_box:
    start: coordinate
    goal: coordinate

    def __post_init__(self):
        self.min_lat = min(self.start.lat, self.goal.lat)
        self.max_lat = max(self.start.lat, self.goal.lat)
        self.min_lon = min(self.start.lon, self.goal.lon)
        self.max_lon = max(self.start.lon, self.goal.lon)
        # 境界が狭すぎる場合は拡張
        if self.max_lat - self.min_lat < 1:
            self.max_lat += 0.05
            self.min_lat -= 0.05
        if self.max_lon - self.min_lon < 1:
            self.max_lon += 0.1
            self.min_lon -= 0.1

    def __str__(self):
        return f"BoundingBox(min_lat={self.min_lat}, max_lat={self.max_lat}, min_lon={self.min_lon}, max_lon={self.max_lon})"


    def create_tiles(self, zoom_level: int = 13) -> List[tile]:
        """
        指定されたズームレベルでタイルを生成する。
        (地図タイルの最小は左上、最大は右下)
        Args:
            zoom_level (int): ズームレベル（デフォルトは13）
        Returns:
            List[tile]: タイルリスト
        """
        min_tile = _deg2num(coordinate(self.max_lat, self.min_lon), zoom_level)
        max_tile = _deg2num(coordinate(self.min_lat, self.max_lon), zoom_level)
        tiles = []
        for xtile in range(min_tile.x, max_tile.x + 1):
            for ytile in range(min_tile.y, max_tile.y + 1):
                tiles.append(tile(xtile, ytile, zoom_level))
        return tiles

    def get_tile_centers(self, tiles: List[tile]) -> List[coordinate]:
        """
        タイルの中心座標を取得する。
        Args:
            tiles (List[tile]): タイルのリスト
        Returns:
            List[coordinate]: タイルの中心座標のリスト
        """
        centers = []
        for t in tiles:
            coord = _num2deg(t)
            centers.append(coord)
        return centers


def _num2deg(tile_obj: tile) -> coordinate:
    """
    タイル座標をタイルの中心の緯度経度に変換する。
    Args:
        tile_obj (tile): タイル座標（x, y, zoom）
    Returns:
        coordinate: タイルの中心の緯度経度座標
    """
    n = 1 << tile_obj.zoom
    # タイルの中心座標を計算するため、0.5を加算
    lon_deg = (tile_obj.x + 0.5) / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * (tile_obj.y + 0.5) / n)))
    lat_deg = math.degrees(lat_rad)
    return coordinate(lat_deg, lon_deg)


def _deg2num(coord: coordinate, zoom_level: int = 13) -> tile:
    """
    緯度経度をタイル座標に変換する。
    Args:
        coord (coordinate): 緯度経度の座標
        zoom_level (int): ズームレベル（デフォルトは13）
    Returns:
        tile: タイル座標（x, y, zoom）
    """
    lat_rad = math.radians(coord.lat)
    n = 1 << zoom_level
    xtile = int((coord.lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return tile(xtile, ytile, zoom_level)

