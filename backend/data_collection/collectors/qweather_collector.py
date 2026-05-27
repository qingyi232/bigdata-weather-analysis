"""
和风天气数据采集器
官方文档: https://dev.qweather.com/docs/api/
"""

import requests
import time
from datetime import datetime
from loguru import logger
import yaml
import os


class QWeatherCollector:
    """和风天气数据采集器"""
    
    def __init__(self, config_path=None):
        """
        初始化和风天气采集器
        
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
        
        self.config = config['weather_data_sources']['qweather']
        self.api_key = self.config['api_key']
        self.base_url = self.config['base_url']
        self.locations = self.config['locations']
        
        # 城市ID缓存
        self.location_cache = {}
        
        logger.info("和风天气采集器初始化成功")
    
    def get_location_id(self, city_name):
        """
        获取城市 Location ID
        
        Args:
            city_name: 城市名称
            
        Returns:
            Location ID
        """
        # 检查缓存
        if city_name in self.location_cache:
            return self.location_cache[city_name]
        
        try:
            url = "https://geoapi.qweather.com/v2/city/lookup"
            params = {
                'location': city_name,
                'key': self.api_key,
                'lang': 'zh'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == '200' and len(data['location']) > 0:
                location_id = data['location'][0]['id']
                self.location_cache[city_name] = location_id
                logger.info(f"获取城市ID成功: {city_name} -> {location_id}")
                return location_id
            else:
                logger.error(f"获取城市ID失败: {city_name}, 响应: {data}")
                return None
                
        except Exception as e:
            logger.error(f"获取城市ID异常: {city_name}, 错误: {str(e)}")
            return None
    
    def get_realtime_weather(self, city_name):
        """
        获取实时天气数据
        API: https://dev.qweather.com/docs/api/weather/weather-now/
        
        Args:
            city_name: 城市名称
            
        Returns:
            实时天气数据字典
        """
        try:
            location_id = self.get_location_id(city_name)
            if not location_id:
                return None
            
            url = f"{self.base_url}/weather/now"
            params = {
                'location': location_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == '200':
                now = data['now']
                
                weather_data = {
                    'station_id': f"qweather_{location_id}",
                    'station_name': city_name,
                    'observation_time': datetime.strptime(now['obsTime'], '%Y-%m-%dT%H:%M%z'),
                    'temperature': float(now['temp']),
                    'feels_like': float(now['feelsLike']),
                    'humidity': float(now['humidity']),
                    'pressure': float(now['pressure']),
                    'wind_speed': float(now['windSpeed']),
                    'wind_direction': float(now['wind360']),
                    'wind_direction_text': now['windDir'],
                    'wind_scale': now['windScale'],
                    'precipitation': float(now['precip']),
                    'cloud_cover': float(now['cloud']) if now.get('cloud') else None,
                    'visibility': float(now['vis']),
                    'weather_code': now['icon'],
                    'weather_text': now['text'],
                    'dew_point': float(now.get('dew', 0)),
                    'data_source': 'qweather',
                    'data_quality': 'good'
                }
                
                logger.info(f"获取实时天气成功: {city_name}, 温度: {weather_data['temperature']}℃")
                return weather_data
            else:
                logger.error(f"获取实时天气失败: {city_name}, 响应码: {data['code']}")
                return None
                
        except Exception as e:
            logger.error(f"获取实时天气异常: {city_name}, 错误: {str(e)}")
            return None
    
    def get_hourly_forecast(self, city_name, hours=24):
        """
        获取逐小时预报
        API: https://dev.qweather.com/docs/api/weather/weather-hourly-forecast/
        
        Args:
            city_name: 城市名称
            hours: 预报小时数 (24 或 72 或 168)
            
        Returns:
            小时预报列表
        """
        try:
            location_id = self.get_location_id(city_name)
            if not location_id:
                return None
            
            url = f"{self.base_url}/weather/{hours}h"
            params = {
                'location': location_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == '200':
                forecasts = []
                
                for hour in data['hourly']:
                    forecast = {
                        'station_id': f"qweather_{location_id}",
                        'forecast_time': datetime.strptime(hour['fxTime'], '%Y-%m-%dT%H:%M%z'),
                        'temperature': float(hour['temp']),
                        'humidity': float(hour['humidity']),
                        'pressure': float(hour['pressure']),
                        'wind_speed': float(hour['windSpeed']),
                        'wind_direction': float(hour['wind360']),
                        'wind_direction_text': hour['windDir'],
                        'precipitation': float(hour['precip']),
                        'weather_code': hour['icon'],
                        'weather_text': hour['text'],
                        'data_source': 'qweather'
                    }
                    forecasts.append(forecast)
                
                logger.info(f"获取小时预报成功: {city_name}, 共 {len(forecasts)} 条")
                return forecasts
            else:
                logger.error(f"获取小时预报失败: {city_name}, 响应码: {data['code']}")
                return None
                
        except Exception as e:
            logger.error(f"获取小时预报异常: {city_name}, 错误: {str(e)}")
            return None
    
    def get_daily_forecast(self, city_name, days=7):
        """
        获取逐天预报
        API: https://dev.qweather.com/docs/api/weather/weather-daily-forecast/
        
        Args:
            city_name: 城市名称
            days: 预报天数 (3, 7, 10, 15, 30)
            
        Returns:
            每日预报列表
        """
        try:
            location_id = self.get_location_id(city_name)
            if not location_id:
                return None
            
            url = f"{self.base_url}/weather/{days}d"
            params = {
                'location': location_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == '200':
                forecasts = []
                
                for day in data['daily']:
                    forecast = {
                        'station_id': f"qweather_{location_id}",
                        'date': datetime.strptime(day['fxDate'], '%Y-%m-%d'),
                        'temperature_max': float(day['tempMax']),
                        'temperature_min': float(day['tempMin']),
                        'humidity_avg': float(day['humidity']),
                        'pressure_avg': float(day['pressure']),
                        'wind_speed_max': float(day['windSpeedDay']),
                        'precipitation_total': float(day['precip']),
                        'weather_text_day': day['textDay'],
                        'weather_text_night': day['textNight'],
                        'data_source': 'qweather'
                    }
                    forecasts.append(forecast)
                
                logger.info(f"获取每日预报成功: {city_name}, 共 {len(forecasts)} 条")
                return forecasts
            else:
                logger.error(f"获取每日预报失败: {city_name}, 响应码: {data['code']}")
                return None
                
        except Exception as e:
            logger.error(f"获取每日预报异常: {city_name}, 错误: {str(e)}")
            return None
    
    def get_weather_warnings(self, city_name):
        """
        获取天气预警
        API: https://dev.qweather.com/docs/api/warning/weather-warning/
        
        Args:
            city_name: 城市名称
            
        Returns:
            预警列表
        """
        try:
            location_id = self.get_location_id(city_name)
            if not location_id:
                return None
            
            url = f"{self.base_url}/warning/now"
            params = {
                'location': location_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == '200':
                warnings = []
                
                if 'warning' in data and len(data['warning']) > 0:
                    for warning in data['warning']:
                        alert = {
                            'alert_id': warning['id'],
                            'alert_type': warning['typeName'],
                            'alert_level': warning['level'],
                            'alert_title': warning['title'],
                            'alert_text': warning['text'],
                            'start_time': datetime.strptime(warning['startTime'], '%Y-%m-%dT%H:%M%z'),
                            'end_time': datetime.strptime(warning['endTime'], '%Y-%m-%dT%H:%M%z'),
                            'publish_time': datetime.strptime(warning['pubTime'], '%Y-%m-%dT%H:%M%z'),
                            'status': 'active',
                            'data_source': 'qweather',
                            'source_url': warning.get('url', '')
                        }
                        warnings.append(alert)
                    
                    logger.info(f"获取天气预警成功: {city_name}, 共 {len(warnings)} 条")
                else:
                    logger.info(f"暂无天气预警: {city_name}")
                
                return warnings
            else:
                logger.error(f"获取天气预警失败: {city_name}, 响应码: {data['code']}")
                return None
                
        except Exception as e:
            logger.error(f"获取天气预警异常: {city_name}, 错误: {str(e)}")
            return None
    
    def get_air_quality(self, city_name):
        """
        获取空气质量
        API: https://dev.qweather.com/docs/api/air/air-now/
        
        Args:
            city_name: 城市名称
            
        Returns:
            空气质量数据
        """
        try:
            location_id = self.get_location_id(city_name)
            if not location_id:
                return None
            
            url = f"{self.base_url}/air/now"
            params = {
                'location': location_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == '200':
                air = data['now']
                
                air_data = {
                    'station_id': f"qweather_{location_id}",
                    'observation_time': datetime.strptime(air['pubTime'], '%Y-%m-%dT%H:%M%z'),
                    'aqi': int(air['aqi']),
                    'aqi_level': air['level'],
                    'aqi_category': air['category'],
                    'primary_pollutant': air['primary'],
                    'pm2_5': float(air['pm2p5']),
                    'pm10': float(air['pm10']),
                    'no2': float(air['no2']),
                    'so2': float(air['so2']),
                    'co': float(air['co']),
                    'o3': float(air['o3']),
                    'data_source': 'qweather'
                }
                
                logger.info(f"获取空气质量成功: {city_name}, AQI: {air_data['aqi']}")
                return air_data
            else:
                logger.error(f"获取空气质量失败: {city_name}, 响应码: {data['code']}")
                return None
                
        except Exception as e:
            logger.error(f"获取空气质量异常: {city_name}, 错误: {str(e)}")
            return None
    
    def collect_all_cities(self):
        """
        采集所有配置城市的实时天气数据
        
        Returns:
            所有城市的天气数据列表
        """
        all_data = []
        
        for city in self.locations:
            logger.info(f"开始采集城市: {city}")
            
            # 实时天气
            realtime = self.get_realtime_weather(city)
            if realtime:
                all_data.append(realtime)
            
            # 天气预警
            warnings = self.get_weather_warnings(city)
            if warnings:
                all_data.extend(warnings)
            
            # 避免请求过快
            time.sleep(0.5)
        
        logger.info(f"采集完成，共 {len(all_data)} 条数据")
        return all_data


if __name__ == "__main__":
    """测试和风天气采集器"""
    
    # 配置日志
    logger.add(
        "../../logs/qweather_collector.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    # 创建采集器
    collector = QWeatherCollector()
    
    # 测试单个城市
    print("\n📍 测试采集北京实时天气:")
    weather = collector.get_realtime_weather("北京")
    if weather:
        print(f"✅ 温度: {weather['temperature']}℃")
        print(f"✅ 湿度: {weather['humidity']}%")
        print(f"✅ 天气: {weather['weather_text']}")
    
    print("\n📍 测试采集北京小时预报:")
    hourly = collector.get_hourly_forecast("北京", 24)
    if hourly:
        print(f"✅ 获取 {len(hourly)} 小时预报")
    
    print("\n📍 测试采集北京天气预警:")
    warnings = collector.get_weather_warnings("北京")
    if warnings:
        print(f"⚠️  共 {len(warnings)} 条预警")
    else:
        print("✅ 暂无预警")
    
    print("\n🌍 测试采集所有城市:")
    all_data = collector.collect_all_cities()
    print(f"✅ 共采集 {len(all_data)} 条数据")


