# src/core/value_objects/coordinates.py
from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class Coordinates:
    """
    Value Object для географических координат.
    """
    
    latitude: float
    longitude: float
    
    def __post_init__(self) -> None:
        """Валидация координат"""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(
                f"Latitude must be between -90 and 90, got {self.latitude}"
            )
        
        if not (-180 <= self.longitude <= 180):
            raise ValueError(
                f"Longitude must be between -180 and 180, got {self.longitude}"
            )
    
    # ========== Свойства ==========
    
    @property
    def is_valid(self) -> bool:
        """Проверяет валидность координат"""
        return (-90 <= self.latitude <= 90) and (-180 <= self.longitude <= 180)
    
    @property
    def latitude_radians(self) -> float:
        """Широта в радианах"""
        return math.radians(self.latitude)
    
    @property
    def longitude_radians(self) -> float:
        """Долгота в радианах"""
        return math.radians(self.longitude)
    
    # ========== Методы ==========
    
    def distance_to(self, other: 'Coordinates') -> float:
        """
        Вычисляет расстояние до другой точки в километрах
        (используя формулу гаверсинусов)
        """
        R = 6371  # Радиус Земли в км
        
        lat1, lon1 = self.latitude_radians, self.longitude_radians
        lat2, lon2 = other.latitude_radians, other.longitude_radians
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def is_within_radius(self, center: 'Coordinates', radius_km: float) -> bool:
        """Проверяет, находится ли точка в радиусе от центра"""
        return self.distance_to(center) <= radius_km
    
    def format_decimal(self, precision: int = 6) -> str:
        """Форматирует координаты в десятичном виде"""
        return f"{self.latitude:.{precision}f}, {self.longitude:.{precision}f}"
    
    def format_dms(self) -> str:
        """Форматирует координаты в градусах, минутах, секундах"""
        lat_deg = abs(self.latitude)
        lat_min = (lat_deg % 1) * 60
        lat_sec = (lat_min % 1) * 60
        lat_dir = 'N' if self.latitude >= 0 else 'S'
        
        lon_deg = abs(self.longitude)
        lon_min = (lon_deg % 1) * 60
        lon_sec = (lon_min % 1) * 60
        lon_dir = 'E' if self.longitude >= 0 else 'W'
        
        return (
            f"{int(lat_deg)}°{int(lat_min)}'{lat_sec:.1f}\"{lat_dir} "
            f"{int(lon_deg)}°{int(lon_min)}'{lon_sec:.1f}\"{lon_dir}"
        )
    
    def get_center_with(self, other: 'Coordinates') -> 'Coordinates':
        """Вычисляет среднюю точку между двумя координатами"""
        return Coordinates(
            latitude=(self.latitude + other.latitude) / 2,
            longitude=(self.longitude + other.longitude) / 2
        )
    
    # ========== Специальные методы ==========
    
    def __str__(self) -> str:
        return f"{self.latitude}, {self.longitude}"
    
    def __repr__(self) -> str:
        return f"Coordinates(lat={self.latitude}, lon={self.longitude})"