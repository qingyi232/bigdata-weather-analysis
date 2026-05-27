"""
Spark 批处理分析模块
用于历史数据分析、统计计算、极端天气检测等
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, max as spark_max, min as spark_min, sum as spark_sum, count,
    year, month, dayofmonth, hour, date_format, window, stddev, percentile_approx
)
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType, TimestampType, IntegerType
)
from loguru import logger
import yaml
import os
from datetime import datetime, timedelta


class SparkWeatherAnalyzer:
    """Spark 天气数据分析器"""
    
    def __init__(self, config_path=None):
        """
        初始化 Spark 分析器
        
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
        
        self.spark_config = config['spark']
        
        # 创建 Spark Session
        self.spark = self._create_spark_session()
        
        logger.info("Spark 分析器初始化成功")
    
    def _create_spark_session(self):
        """创建 Spark Session"""
        try:
            spark = SparkSession.builder \
                .appName(self.spark_config['app_name']) \
                .master(self.spark_config['master']) \
                .config('spark.executor.memory', self.spark_config['executor_memory']) \
                .config('spark.driver.memory', self.spark_config['driver_memory']) \
                .config('spark.executor.cores', self.spark_config['executor_cores']) \
                .config('spark.driver.maxResultSize', self.spark_config['max_result_size']) \
                .config('spark.sql.adaptive.enabled', 'true') \
                .config('spark.sql.adaptive.coalescePartitions.enabled', 'true') \
                .getOrCreate()
            
            spark.sparkContext.setLogLevel('WARN')
            
            logger.info(f"Spark Session 创建成功: {self.spark_config['master']}")
            return spark
            
        except Exception as e:
            logger.error(f"Spark Session 创建失败: {str(e)}")
            raise
    
    def load_data_from_mysql(self, table_name, conditions=None):
        """
        从 MySQL 加载数据
        
        Args:
            table_name: 表名
            conditions: WHERE 条件（可选）
            
        Returns:
            Spark DataFrame
        """
        try:
            # 这里需要配置 MySQL 连接
            # 实际使用时需要添加 MySQL JDBC 驱动
            query = f"(SELECT * FROM {table_name}"
            if conditions:
                query += f" WHERE {conditions}"
            query += ") AS tmp"
            
            # 注意：需要下载 MySQL JDBC 驱动并配置
            df = self.spark.read \
                .format('jdbc') \
                .option('url', 'jdbc:mysql://localhost:3306/weather_db') \
                .option('dbtable', query) \
                .option('user', 'root') \
                .option('password', 'password') \
                .option('driver', 'com.mysql.cj.jdbc.Driver') \
                .load()
            
            logger.info(f"从 MySQL 加载数据成功: {table_name}, 行数: {df.count()}")
            return df
            
        except Exception as e:
            logger.error(f"从 MySQL 加载数据失败: {str(e)}")
            return None
    
    def load_data_from_json(self, json_path):
        """
        从 JSON 文件加载数据
        
        Args:
            json_path: JSON 文件路径（本地或 HDFS）
            
        Returns:
            Spark DataFrame
        """
        try:
            df = self.spark.read.json(json_path)
            logger.info(f"从 JSON 加载数据成功: {json_path}, 行数: {df.count()}")
            return df
        except Exception as e:
            logger.error(f"从 JSON 加载数据失败: {str(e)}")
            return None
    
    def analyze_temperature_trend(self, df, group_by='day'):
        """
        分析温度趋势
        
        Args:
            df: Spark DataFrame (包含 observation_time, temperature 列)
            group_by: 分组方式 (hour/day/month/year)
            
        Returns:
            分析结果 DataFrame
        """
        logger.info(f"开始分析温度趋势 (按 {group_by})")
        
        # 提取时间字段
        df = df.withColumn('year', year('observation_time')) \
               .withColumn('month', month('observation_time')) \
               .withColumn('day', dayofmonth('observation_time')) \
               .withColumn('hour', hour('observation_time'))
        
        # 根据分组方式选择字段
        group_cols = {
            'hour': ['year', 'month', 'day', 'hour'],
            'day': ['year', 'month', 'day'],
            'month': ['year', 'month'],
            'year': ['year']
        }.get(group_by, ['year', 'month', 'day'])
        
        # 计算统计指标
        result = df.groupBy(*group_cols) \
            .agg(
                avg('temperature').alias('avg_temperature'),
                spark_max('temperature').alias('max_temperature'),
                spark_min('temperature').alias('min_temperature'),
                stddev('temperature').alias('std_temperature'),
                count('*').alias('data_count')
            ) \
            .orderBy(*group_cols)
        
        logger.info(f"温度趋势分析完成: {result.count()} 条结果")
        return result
    
    def analyze_regional_climate(self, df):
        """
        分析地区气候统计
        
        Args:
            df: Spark DataFrame (包含 station_id, province, city 等)
            
        Returns:
            地区气候统计 DataFrame
        """
        logger.info("开始分析地区气候统计")
        
        result = df.groupBy('province', 'city') \
            .agg(
                avg('temperature').alias('avg_temperature'),
                spark_max('temperature').alias('max_temperature'),
                spark_min('temperature').alias('min_temperature'),
                avg('humidity').alias('avg_humidity'),
                avg('pressure').alias('avg_pressure'),
                avg('wind_speed').alias('avg_wind_speed'),
                spark_sum('precipitation').alias('total_precipitation'),
                count('*').alias('data_count')
            ) \
            .orderBy('province', 'city')
        
        logger.info(f"地区气候统计完成: {result.count()} 个地区")
        return result
    
    def detect_extreme_weather(self, df, thresholds=None):
        """
        检测极端天气事件
        
        Args:
            df: Spark DataFrame
            thresholds: 阈值字典
            
        Returns:
            极端天气事件 DataFrame
        """
        logger.info("开始检测极端天气事件")
        
        if thresholds is None:
            thresholds = {
                'high_temperature': 40,  # 高温预警 ℃
                'low_temperature': -20,  # 低温预警 ℃
                'heavy_rain': 50,  # 暴雨预警 mm
                'strong_wind': 20  # 大风预警 m/s
            }
        
        # 高温事件
        extreme_high_temp = df.filter(
            col('temperature') >= thresholds['high_temperature']
        ).withColumn('extreme_type', lit('高温'))
        
        # 低温事件
        extreme_low_temp = df.filter(
            col('temperature') <= thresholds['low_temperature']
        ).withColumn('extreme_type', lit('低温'))
        
        # 暴雨事件
        extreme_rain = df.filter(
            col('precipitation') >= thresholds['heavy_rain']
        ).withColumn('extreme_type', lit('暴雨'))
        
        # 大风事件
        extreme_wind = df.filter(
            col('wind_speed') >= thresholds['strong_wind']
        ).withColumn('extreme_type', lit('大风'))
        
        # 合并所有极端事件
        result = extreme_high_temp.union(extreme_low_temp) \
                                  .union(extreme_rain) \
                                  .union(extreme_wind) \
                                  .select(
                                      'station_id',
                                      'observation_time',
                                      'extreme_type',
                                      'temperature',
                                      'precipitation',
                                      'wind_speed'
                                  ) \
                                  .orderBy('observation_time')
        
        logger.info(f"极端天气检测完成: 发现 {result.count()} 个事件")
        return result
    
    def calculate_monthly_report(self, df, year, month):
        """
        生成月度分析报告
        
        Args:
            df: Spark DataFrame
            year: 年份
            month: 月份
            
        Returns:
            月度报告字典
        """
        logger.info(f"生成月度报告: {year}年{month}月")
        
        # 筛选指定月份数据
        monthly_data = df.filter(
            (year('observation_time') == year) &
            (month('observation_time') == month)
        )
        
        # 统计指标
        stats = monthly_data.agg(
            avg('temperature').alias('avg_temp'),
            spark_max('temperature').alias('max_temp'),
            spark_min('temperature').alias('min_temp'),
            avg('humidity').alias('avg_humidity'),
            avg('pressure').alias('avg_pressure'),
            spark_sum('precipitation').alias('total_precipitation'),
            avg('wind_speed').alias('avg_wind_speed'),
            count('*').alias('total_records')
        ).collect()[0]
        
        report = {
            'year': year,
            'month': month,
            'avg_temperature': float(stats['avg_temp']) if stats['avg_temp'] else None,
            'max_temperature': float(stats['max_temp']) if stats['max_temp'] else None,
            'min_temperature': float(stats['min_temp']) if stats['min_temp'] else None,
            'avg_humidity': float(stats['avg_humidity']) if stats['avg_humidity'] else None,
            'avg_pressure': float(stats['avg_pressure']) if stats['avg_pressure'] else None,
            'total_precipitation': float(stats['total_precipitation']) if stats['total_precipitation'] else None,
            'avg_wind_speed': float(stats['avg_wind_speed']) if stats['avg_wind_speed'] else None,
            'total_records': int(stats['total_records']),
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"月度报告生成完成: 平均温度 {report['avg_temperature']}℃")
        return report
    
    def save_results_to_mysql(self, df, table_name, mode='append'):
        """
        保存结果到 MySQL
        
        Args:
            df: Spark DataFrame
            table_name: 表名
            mode: 保存模式 (append/overwrite)
            
        Returns:
            是否成功
        """
        try:
            df.write \
                .format('jdbc') \
                .option('url', 'jdbc:mysql://localhost:3306/weather_db') \
                .option('dbtable', table_name) \
                .option('user', 'root') \
                .option('password', 'password') \
                .option('driver', 'com.mysql.cj.jdbc.Driver') \
                .mode(mode) \
                .save()
            
            logger.info(f"保存到 MySQL 成功: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"保存到 MySQL 失败: {str(e)}")
            return False
    
    def stop(self):
        """停止 Spark Session"""
        if self.spark:
            self.spark.stop()
            logger.info("Spark Session 已停止")


# 导入缺失的函数
from pyspark.sql.functions import lit


if __name__ == "__main__":
    """测试 Spark 分析器"""
    
    # 配置日志
    logger.add(
        "../logs/spark_analysis.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    print("="*60)
    print("  Spark 天气数据分析器测试")
    print("="*60)
    
    # 创建分析器
    analyzer = SparkWeatherAnalyzer()
    
    # 创建测试数据
    from datetime import datetime, timedelta
    
    test_data = []
    base_time = datetime(2024, 1, 1)
    
    for i in range(100):
        test_data.append({
            'station_id': f'station_{i % 10}',
            'observation_time': base_time + timedelta(hours=i),
            'temperature': 20 + (i % 20) - 10,
            'humidity': 50 + (i % 40),
            'pressure': 1000 + (i % 30),
            'wind_speed': 5 + (i % 15),
            'precipitation': (i % 5) * 2
        })
    
    # 创建 DataFrame
    df = analyzer.spark.createDataFrame(test_data)
    
    print(f"\n✅ 创建测试数据: {df.count()} 条")
    
    # 测试温度趋势分析
    print("\n📊 温度趋势分析 (按天):")
    trend = analyzer.analyze_temperature_trend(df, group_by='day')
    trend.show(5)
    
    # 测试极端天气检测
    print("\n⚠️  极端天气检测:")
    extreme = analyzer.detect_extreme_weather(df, {
        'high_temperature': 25,
        'low_temperature': 5,
        'heavy_rain': 8,
        'strong_wind': 15
    })
    
    print(f"发现 {extreme.count()} 个极端天气事件")
    extreme.show(5)
    
    # 停止 Spark
    analyzer.stop()
    
    print("\n✅ Spark 分析器测试完成")


