"""
OpenWeatherMap 数据采集器
官方文档: https://openweathermap.org/api
"""

import requests
from datetime import datetime
from loguru import logger
import yaml
import os


class OpenWeatherCollector:
    """OpenWeatherMap 数据采集器"""
    
    def __init__(self, config_path=None):
        """
        初始化 OpenWeatherMap 采集器
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../../config/config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.config = config['weather_data_sources']['openweathermap']
        self.api_key = self.config['api_key']
        self.base_url = self.config['base_url']
        self.units = self.config['units']  # metric for Celsius
        
        logger.info("OpenWeatherMap 采集器初始化成功")
    
    def get_current_weather(self, city_name):
        """
        获取当前天气
        API: https://openweathermap.org/current
        
        Args:
            city_name: 城市名称
            
        Returns:
            当前天气数据
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': self.units,
                'lang': 'zh_cn'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_data = {
                'station_id': f"openweather_{data['id']}",
                'station_name': data['name'],
                'observation_time': datetime.fromtimestamp(data['dt']),
                'temperature': float(data['main']['temp']),
                'feels_like': float(data['main']['feels_like']),
                'temperature_min': float(data['main']['temp_min']),
                'temperature_max': float(data['main']['temp_max']),
                'humidity': float(data['main']['humidity']),
                'pressure': float(data['main']['pressure']),
                'wind_speed': float(data['wind']['speed']),
                'wind_direction': float(data['wind'].get('deg', 0)),
                'cloud_cover': float(data['clouds']['all']),
                'visibility': float(data.get('visibility', 0)) / 1000,  # 转换为 km
                'weather_code': str(data['weather'][0]['id']),
                'weather_text': data['weather'][0]['description'],
                'longitude': float(data['coord']['lon']),
                'latitude': float(data['coord']['lat']),
                'data_source': 'openweathermap',
                'data_quality': 'good'
            }
            
            # 降水数据（如果有）
            if 'rain' in data:
                weather_data['precipitation_1h'] = float(data['rain'].get('1h', 0))
            
            logger.info(f"获取 OpenWeatherMap 数据成功: {city_name}, 温度: {weather_data['temperature']}℃")
            return weather_data
            
        except Exception as e:
            logger.error(f"获取 OpenWeatherMap 数据失败: {city_name}, 错误: {str(e)}")
            return None
    
    def get_forecast_5days(self, city_name):
        """
        获取5天预报（每3小时）
        API: https://openweathermap.org/forecast5
        
        Args:
            city_name: 城市名称
            
        Returns:
            预报列表
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': self.units,
                'lang': 'zh_cn'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecasts = []
            station_id = f"openweather_{data['city']['id']}"
            
            for item in data['list']:
                forecast = {
                    'station_id': station_id,
                    'forecast_time': datetime.fromtimestamp(item['dt']),
                    'temperature': float(item['main']['temp']),
                    'temperature_min': float(item['main']['temp_min']),
                    'temperature_max': float(item['main']['temp_max']),
                    'humidity': float(item['main']['humidity']),
                    'pressure': float(item['main']['pressure']),
                    'wind_speed': float(item['wind']['speed']),
                    'wind_direction': float(item['wind'].get('deg', 0)),
                    'cloud_cover': float(item['clouds']['all']),
                    'weather_text': item['weather'][0]['description'],
                    'precipitation_3h': float(item.get('rain', {}).get('3h', 0)),
                    'data_source': 'openweathermap'
                }
                forecasts.append(forecast)
            
            logger.info(f"获取 OpenWeatherMap 预报成功: {city_name}, 共 {len(forecasts)} 条")
            return forecasts
            
        except Exception as e:
            logger.error(f"获取 OpenWeatherMap 预报失败: {city_name}, 错误: {str(e)}")
            return None
    
    def get_historical_data(self, city_name, start_timestamp):
        """
        获取历史数据（需要付费订阅）
        API: https://openweathermap.org/history
        
        Args:
            city_name: 城市名称
            start_timestamp: 开始时间戳
            
        Returns:
            历史数据列表
        """
        logger.warning("OpenWeatherMap 历史数据需要付费订阅")
        return None


if __name__ == "__main__":
    """测试 OpenWeatherMap 采集器"""
    
    # 配置日志
    logger.add(
        "../../logs/openweather_collector.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    # 创建采集器
    collector = OpenWeatherCollector()
    
    # 测试采集
    print("\n📍 测试采集北京天气 (OpenWeatherMap):")
    weather = collector.get_current_weather("Beijing,CN")
    if weather:
        print(f"✅ 温度: {weather['temperature']}℃")
        print(f"✅ 湿度: {weather['humidity']}%")
        print(f"✅ 天气: {weather['weather_text']}")
    
    print("\n📍 测试采集5天预报:")
    forecast = collector.get_forecast_5days("Beijing,CN")
    if forecast:
        print(f"✅ 获取 {len(forecast)} 条预报数据")


