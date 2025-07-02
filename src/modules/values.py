from dataclasses import dataclass
import numpy as np
from typing import List
import json

@dataclass
class coordinate:
    lat: float
    lon: float

    def __post_init__(self):
        self.lat = round(self.lat, 6)
        self.lon = round(self.lon, 6)
    

@dataclass
class bounding_box:
    start: coordinate
    goal: coordinate
    
    def __post_init__(self):
        self.min_lat = min(self.start.lat, self.goal.lat)
        self.max_lat = max(self.start.lat, self.goal.lat)
        self.min_lon = min(self.start.lon, self.goal.lon)
        self.max_lon = max(self.start.lon, self.goal.lon)
        if self.max_lat - self.min_lat < 1:
            self.max_lat += 0.05
            self.min_lat -= 0.05
        if self.max_lon - self.min_lon < 1:
            self.max_lon += 0.1
            self.min_lon -= 0.1


    
    def __str__(self):
        return f"BoundingBox(min_lat={self.min_lat}, max_lat={self.max_lat}, min_lon={self.min_lon}, max_lon={self.max_lon})"
    
    def create_grid(self, grid_deg: float = 0.04) -> List[coordinate]:
        """
        0.04度四方の固定タイルでグリッド分割を行う。
        
        Args:
            grid_deg: グリッドサイズ（度数）デフォルト0.05度
        """
        lat_range = self.max_lat - self.min_lat
        lon_range = self.max_lon - self.min_lon
        
        # 0.05度四方で分割
        n_lat = max(1, int(np.ceil(lat_range / grid_deg)))
        n_lon = max(1, int(np.ceil(lon_range / grid_deg)))

        # 分割数に合わせて等間隔で境界を作り、中心を求める
        lat_edges = np.linspace(self.min_lat, self.max_lat, n_lat + 1)
        lon_edges = np.linspace(self.min_lon, self.max_lon, n_lon + 1)
        grid_coordinates = []
        for i in range(n_lat):
            for j in range(n_lon):
                center_lat = (lat_edges[i] + lat_edges[i+1]) / 2
                center_lon = (lon_edges[j] + lon_edges[j+1]) / 2
                grid_coordinates.append(coordinate(center_lat, center_lon))
        return grid_coordinates