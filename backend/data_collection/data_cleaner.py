"""
数据清洗模块
处理异常值、缺失值、数据验证等
"""

import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime, timedelta


class WeatherDataCleaner:
    """天气数据清洗器"""
    
    def __init__(self):
        """初始化数据清洗器"""
        # 数据范围阈值
        self.thresholds = {
            'temperature': {'min': -60, 'max': 60},  # 温度范围 (℃)
            'humidity': {'min': 0, 'max': 100},  # 湿度范围 (%)
            'pressure': {'min': 800, 'max': 1100},  # 气压范围 (hPa)
            'wind_speed': {'min': 0, 'max': 100},  # 风速范围 (m/s)
            'precipitation': {'min': 0, 'max': 1000},  # 降水范围 (mm)
            'visibility': {'min': 0, 'max': 50},  # 能见度范围 (km)
            'cloud_cover': {'min': 0, 'max': 100}  # 云量范围 (%)
        }
        
        logger.info("数据清洗器初始化成功")
    
    def validate_value(self, field, value):
        """
        验证单个字段值是否在合理范围内
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            是否有效
        """
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return False
        
        if field in self.thresholds:
            threshold = self.thresholds[field]
            if value < threshold['min'] or value > threshold['max']:
                logger.warning(
                    f"数据异常: {field}={value}, "
                    f"有效范围: [{threshold['min']}, {threshold['max']}]"
                )
                return False
        
        return True
    
    def clean_weather_data(self, data_dict):
        """
        清洗单条天气数据
        
        Args:
            data_dict: 天气数据字典
            
        Returns:
            清洗后的数据字典
        """
        cleaned_data = data_dict.copy()
        quality_score = 100
        issues = []
        
        # 验证必需字段
        required_fields = ['station_id', 'observation_time']
        for field in required_fields:
            if field not in cleaned_data or cleaned_data[field] is None:
                logger.error(f"缺少必需字段: {field}")
                cleaned_data['data_quality'] = 'missing'
                return cleaned_data
        
        # 验证和清洗各个字段
        numeric_fields = [
            'temperature', 'feels_like', 'temperature_max', 'temperature_min',
            'humidity', 'pressure', 'wind_speed', 'precipitation',
            'visibility', 'cloud_cover'
        ]
        
        for field in numeric_fields:
            if field in cleaned_data and cleaned_data[field] is not None:
                value = cleaned_data[field]
                
                # 类型转换
                try:
                    value = float(value)
                    cleaned_data[field] = value
                except (ValueError, TypeError):
                    logger.warning(f"字段 {field} 无法转换为数字: {value}")
                    cleaned_data[field] = None
                    quality_score -= 5
                    issues.append(f"{field}_invalid_type")
                    continue
                
                # 范围验证
                if not self.validate_value(field, value):
                    quality_score -= 10
                    issues.append(f"{field}_out_of_range")
                    
                    # 异常值处理：设为None，后续可用插值法填充
                    cleaned_data[field] = None
        
        # 逻辑验证
        if cleaned_data.get('temperature_max') and cleaned_data.get('temperature_min'):
            if cleaned_data['temperature_max'] < cleaned_data['temperature_min']:
                logger.warning("最高温度小于最低温度，数据异常")
                quality_score -= 15
                issues.append("temperature_logic_error")
        
        # 设置数据质量等级
        if quality_score >= 90:
            cleaned_data['data_quality'] = 'good'
        elif quality_score >= 70:
            cleaned_data['data_quality'] = 'medium'
        elif quality_score >= 50:
            cleaned_data['data_quality'] = 'poor'
        else:
            cleaned_data['data_quality'] = 'bad'
        
        # 记录质量分数和问题
        cleaned_data['quality_score'] = quality_score
        cleaned_data['quality_issues'] = ','.join(issues) if issues else None
        
        return cleaned_data
    
    def clean_dataframe(self, df):
        """
        清洗 DataFrame 格式的天气数据
        
        Args:
            df: pandas DataFrame
            
        Returns:
            清洗后的 DataFrame
        """
        logger.info(f"开始清洗 DataFrame 数据，共 {len(df)} 条")
        
        # 去除完全重复的行
        df_cleaned = df.drop_duplicates()
        if len(df_cleaned) < len(df):
            logger.info(f"删除 {len(df) - len(df_cleaned)} 条重复数据")
        
        # 处理时间字段
        if 'observation_time' in df_cleaned.columns:
            df_cleaned['observation_time'] = pd.to_datetime(
                df_cleaned['observation_time'], 
                errors='coerce'
            )
            
            # 删除时间无效的行
            invalid_time = df_cleaned['observation_time'].isna().sum()
            if invalid_time > 0:
                logger.warning(f"发现 {invalid_time} 条时间无效的数据")
                df_cleaned = df_cleaned.dropna(subset=['observation_time'])
        
        # 按字段验证和处理
        numeric_fields = {
            'temperature': (-60, 60),
            'humidity': (0, 100),
            'pressure': (800, 1100),
            'wind_speed': (0, 100),
            'precipitation': (0, 1000)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in df_cleaned.columns:
                # 转换为数值类型
                df_cleaned[field] = pd.to_numeric(df_cleaned[field], errors='coerce')
                
                # 标记异常值
                mask_outliers = (
                    (df_cleaned[field] < min_val) | 
                    (df_cleaned[field] > max_val)
                )
                
                outlier_count = mask_outliers.sum()
                if outlier_count > 0:
                    logger.warning(f"字段 {field} 发现 {outlier_count} 个异常值")
                    
                    # 异常值替换为 NaN
                    df_cleaned.loc[mask_outliers, field] = np.nan
        
        # 填充缺失值（使用插值法）
        interpolation_fields = ['temperature', 'humidity', 'pressure']
        
        for field in interpolation_fields:
            if field in df_cleaned.columns:
                missing_count = df_cleaned[field].isna().sum()
                
                if missing_count > 0:
                    logger.info(f"字段 {field} 有 {missing_count} 个缺失值，进行插值填充")
                    
                    # 按站点分组进行时间序列插值
                    if 'station_id' in df_cleaned.columns:
                        df_cleaned[field] = df_cleaned.groupby('station_id')[field].transform(
                            lambda x: x.interpolate(method='linear', limit_direction='both')
                        )
                    else:
                        df_cleaned[field] = df_cleaned[field].interpolate(
                            method='linear', 
                            limit_direction='both'
                        )
        
        logger.info(f"数据清洗完成，剩余 {len(df_cleaned)} 条有效数据")
        return df_cleaned
    
    def detect_anomalies(self, df, field='temperature', method='zscore', threshold=3):
        """
        检测异常值
        
        Args:
            df: DataFrame
            field: 要检测的字段
            method: 检测方法 (zscore/iqr)
            threshold: 阈值
            
        Returns:
            异常值的索引列表
        """
        if field not in df.columns:
            logger.error(f"字段 {field} 不存在")
            return []
        
        if method == 'zscore':
            # Z-Score 方法
            mean = df[field].mean()
            std = df[field].std()
            z_scores = np.abs((df[field] - mean) / std)
            anomalies = df[z_scores > threshold].index.tolist()
            
        elif method == 'iqr':
            # IQR 方法
            Q1 = df[field].quantile(0.25)
            Q3 = df[field].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            anomalies = df[
                (df[field] < lower_bound) | (df[field] > upper_bound)
            ].index.tolist()
        
        else:
            logger.error(f"未知的检测方法: {method}")
            return []
        
        logger.info(f"字段 {field} 检测到 {len(anomalies)} 个异常值")
        return anomalies
    
    def aggregate_to_hourly(self, df):
        """
        将多条数据聚合为小时数据
        
        Args:
            df: DataFrame（包含 observation_time 列）
            
        Returns:
            聚合后的 DataFrame
        """
        if 'observation_time' not in df.columns:
            logger.error("缺少 observation_time 字段")
            return df
        
        # 设置时间索引
        df_copy = df.copy()
        df_copy['hour'] = df_copy['observation_time'].dt.floor('H')
        
        # 按站点和小时分组聚合
        agg_rules = {
            'temperature': 'mean',
            'humidity': 'mean',
            'pressure': 'mean',
            'wind_speed': 'mean',
            'precipitation': 'sum',  # 降水量求和
            'visibility': 'mean',
            'cloud_cover': 'mean'
        }
        
        # 只聚合存在的字段
        agg_rules = {k: v for k, v in agg_rules.items() if k in df_copy.columns}
        
        if 'station_id' in df_copy.columns:
            df_hourly = df_copy.groupby(['station_id', 'hour']).agg(agg_rules).reset_index()
            df_hourly.rename(columns={'hour': 'observation_time'}, inplace=True)
        else:
            df_hourly = df_copy.groupby('hour').agg(agg_rules).reset_index()
            df_hourly.rename(columns={'hour': 'observation_time'}, inplace=True)
        
        logger.info(f"数据聚合完成: {len(df)} 条 -> {len(df_hourly)} 条小时数据")
        return df_hourly


if __name__ == "__main__":
    """测试数据清洗器"""
    
    # 配置日志
    logger.add(
        "../logs/data_cleaner.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    # 创建清洗器
    cleaner = WeatherDataCleaner()
    
    # 测试单条数据清洗
    print("\n测试单条数据清洗:")
    test_data = {
        'station_id': 'test_001',
        'observation_time': datetime.now(),
        'temperature': 25.5,
        'humidity': 60,
        'pressure': 1013,
        'wind_speed': 5.5,
        'precipitation': 0.5
    }
    
    cleaned = cleaner.clean_weather_data(test_data)
    print(f"数据质量: {cleaned['data_quality']}")
    print(f"质量分数: {cleaned['quality_score']}")
    
    # 测试异常数据
    print("\n测试异常数据清洗:")
    bad_data = {
        'station_id': 'test_002',
        'observation_time': datetime.now(),
        'temperature': 150,  # 异常温度
        'humidity': -10,  # 异常湿度
        'pressure': 1013
    }
    
    cleaned_bad = cleaner.clean_weather_data(bad_data)
    print(f"数据质量: {cleaned_bad['data_quality']}")
    print(f"质量分数: {cleaned_bad['quality_score']}")
    print(f"问题: {cleaned_bad.get('quality_issues', 'None')}")
    
    print("\n✅ 数据清洗器测试完成")


