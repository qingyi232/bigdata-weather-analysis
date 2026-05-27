"""
Kafka 生产者 - 将采集的天气数据发送到 Kafka
基于大数据的天气数据分析与可视化系统
"""

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from datetime import datetime
from loguru import logger
import yaml
import os
import time


class WeatherKafkaProducer:
    """天气数据 Kafka 生产者"""
    
    def __init__(self, config_path=None):
        """
        初始化 Kafka 生产者
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.kafka_config = config['kafka']
        self.topics = self.kafka_config['topics']
        
        # 创建 Kafka 生产者
        self.producer = self._create_producer()
        
        logger.info("Kafka 生产者初始化成功")
    
    def _create_producer(self):
        """创建 Kafka 生产者实例"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                compression_type=self.kafka_config['producer']['compression_type'],
                batch_size=self.kafka_config['producer']['batch_size'],
                linger_ms=self.kafka_config['producer']['linger_ms'],
                acks=self.kafka_config['producer']['acks'],
                value_serializer=lambda v: json.dumps(
                    v, 
                    default=self._json_serializer
                ).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            logger.info(f"Kafka 生产者连接成功: {self.kafka_config['bootstrap_servers']}")
            return producer
            
        except Exception as e:
            logger.error(f"Kafka 生产者创建失败: {str(e)}")
            raise
    
    def _json_serializer(self, obj):
        """JSON 序列化辅助函数"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def send_realtime_weather(self, weather_data):
        """
        发送实时天气数据到 Kafka
        
        Args:
            weather_data: 天气数据字典
            
        Returns:
            是否发送成功
        """
        try:
            # 使用站点ID作为key，保证同一站点的数据发送到同一分区
            key = weather_data.get('station_id', 'unknown')
            
            # 添加时间戳
            weather_data['kafka_timestamp'] = datetime.now().isoformat()
            
            # 发送到 Kafka
            future = self.producer.send(
                self.topics['realtime_weather'],
                key=key,
                value=weather_data
            )
            
            # 等待发送完成
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"实时天气数据发送成功: {key}, "
                f"Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka 发送失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"发送实时天气数据异常: {str(e)}")
            return False
    
    def send_historical_weather(self, historical_data):
        """
        发送历史天气数据到 Kafka
        
        Args:
            historical_data: 历史数据字典
            
        Returns:
            是否发送成功
        """
        try:
            key = historical_data.get('station_id', 'unknown')
            historical_data['kafka_timestamp'] = datetime.now().isoformat()
            
            future = self.producer.send(
                self.topics['historical_weather'],
                key=key,
                value=historical_data
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(f"历史天气数据发送成功: {key}, Offset: {record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"发送历史天气数据异常: {str(e)}")
            return False
    
    def send_weather_alert(self, alert_data):
        """
        发送天气预警到 Kafka
        
        Args:
            alert_data: 预警数据字典
            
        Returns:
            是否发送成功
        """
        try:
            key = alert_data.get('alert_id', 'unknown')
            alert_data['kafka_timestamp'] = datetime.now().isoformat()
            
            future = self.producer.send(
                self.topics['alerts'],
                key=key,
                value=alert_data
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.warning(
                f"天气预警发送成功: {alert_data.get('alert_type')}, "
                f"等级: {alert_data.get('alert_level')}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"发送天气预警异常: {str(e)}")
            return False
    
    def send_prediction(self, prediction_data):
        """
        发送天气预测结果到 Kafka
        
        Args:
            prediction_data: 预测数据字典
            
        Returns:
            是否发送成功
        """
        try:
            key = prediction_data.get('station_id', 'unknown')
            prediction_data['kafka_timestamp'] = datetime.now().isoformat()
            
            future = self.producer.send(
                self.topics['predictions'],
                key=key,
                value=prediction_data
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(f"天气预测发送成功: {key}, Offset: {record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"发送天气预测异常: {str(e)}")
            return False
    
    def send_batch(self, data_list, data_type='realtime'):
        """
        批量发送数据到 Kafka
        
        Args:
            data_list: 数据列表
            data_type: 数据类型 (realtime/historical/alert/prediction)
            
        Returns:
            发送成功的数量
        """
        success_count = 0
        
        send_method = {
            'realtime': self.send_realtime_weather,
            'historical': self.send_historical_weather,
            'alert': self.send_weather_alert,
            'prediction': self.send_prediction
        }.get(data_type)
        
        if not send_method:
            logger.error(f"未知的数据类型: {data_type}")
            return 0
        
        for data in data_list:
            if send_method(data):
                success_count += 1
        
        logger.info(f"批量发送完成: 总数 {len(data_list)}, 成功 {success_count}")
        return success_count
    
    def flush(self):
        """刷新缓冲区，确保所有消息都已发送"""
        try:
            self.producer.flush()
            logger.info("Kafka 生产者缓冲区已刷新")
        except Exception as e:
            logger.error(f"刷新缓冲区失败: {str(e)}")
    
    def close(self):
        """关闭 Kafka 生产者"""
        try:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka 生产者已关闭")
        except Exception as e:
            logger.error(f"关闭 Kafka 生产者失败: {str(e)}")


class WeatherDataCollectionService:
    """天气数据采集服务（整合所有数据源）"""
    
    def __init__(self, config_path=None):
        """初始化数据采集服务"""
        # 导入采集器
        from collectors.qweather_collector import QWeatherCollector
        from collectors.openweather_collector import OpenWeatherCollector
        
        # 初始化采集器
        self.qweather = QWeatherCollector(config_path)
        self.openweather = OpenWeatherCollector(config_path)
        
        # 初始化 Kafka 生产者
        self.kafka_producer = WeatherKafkaProducer(config_path)
        
        logger.info("天气数据采集服务初始化成功")
    
    def collect_and_send_realtime(self):
        """采集并发送实时天气数据"""
        logger.info("===== 开始采集实时天气数据 =====")
        
        total_sent = 0
        
        # 和风天气采集
        try:
            logger.info("开始和风天气采集...")
            qweather_data = self.qweather.collect_all_cities()
            
            if qweather_data:
                # 分离实时数据和预警数据
                realtime_data = [d for d in qweather_data if 'temperature' in d]
                alert_data = [d for d in qweather_data if 'alert_type' in d]
                
                # 发送实时数据
                if realtime_data:
                    count = self.kafka_producer.send_batch(realtime_data, 'realtime')
                    total_sent += count
                    logger.info(f"和风天气实时数据发送: {count} 条")
                
                # 发送预警数据
                if alert_data:
                    count = self.kafka_producer.send_batch(alert_data, 'alert')
                    total_sent += count
                    logger.info(f"和风天气预警数据发送: {count} 条")
        
        except Exception as e:
            logger.error(f"和风天气采集失败: {str(e)}")
        
        # 刷新缓冲区
        self.kafka_producer.flush()
        
        logger.info(f"===== 实时数据采集完成: 总计发送 {total_sent} 条 =====")
        return total_sent
    
    def run_continuous(self, interval=300):
        """
        持续运行采集服务
        
        Args:
            interval: 采集间隔（秒）
        """
        logger.info(f"天气数据采集服务启动，采集间隔: {interval} 秒")
        
        try:
            while True:
                try:
                    self.collect_and_send_realtime()
                except Exception as e:
                    logger.error(f"采集过程出错: {str(e)}")
                
                # 等待下一次采集
                logger.info(f"等待 {interval} 秒后进行下一次采集...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止采集服务")
        finally:
            self.kafka_producer.close()


if __name__ == "__main__":
    """运行数据采集服务"""
    
    # 配置日志
    logger.add(
        "../logs/kafka_producer_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    print("="*60)
    print("  基于大数据的天气数据分析与可视化系统")
    print("  Kafka 数据采集服务")
    print("="*60)
    
    # 创建采集服务
    service = WeatherDataCollectionService()
    
    # 运行选项
    print("\n请选择运行模式:")
    print("1. 单次采集测试")
    print("2. 持续采集服务 (每5分钟)")
    
    choice = input("\n请输入选项 (1/2): ").strip()
    
    if choice == '1':
        # 单次采集测试
        print("\n开始单次采集测试...")
        count = service.collect_and_send_realtime()
        print(f"\n✅ 采集完成，共发送 {count} 条数据到 Kafka")
        service.kafka_producer.close()
    
    elif choice == '2':
        # 持续采集服务
        print("\n启动持续采集服务...")
        print("按 Ctrl+C 停止服务\n")
        service.run_continuous(interval=300)  # 5分钟
    
    else:
        print("❌ 无效选项")


