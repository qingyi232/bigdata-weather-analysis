"""
数据库模型定义
基于大数据的天气数据分析与可视化系统
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class WeatherStation(Base):
    """气象站信息表"""
    __tablename__ = 'weather_stations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(50), unique=True, nullable=False, index=True, comment='站点ID')
    station_name = Column(String(100), nullable=False, comment='站点名称')
    province = Column(String(50), nullable=False, comment='省份')
    city = Column(String(50), nullable=False, comment='城市')
    district = Column(String(50), comment='区县')
    longitude = Column(Float, nullable=False, comment='经度')
    latitude = Column(Float, nullable=False, comment='纬度')
    altitude = Column(Float, comment='海拔高度(米)')
    station_type = Column(String(20), comment='站点类型:地面站/卫星/雷达')
    status = Column(String(20), default='active', comment='状态:active/inactive')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    realtime_data = relationship("WeatherRealtime", back_populates="station")
    historical_data = relationship("WeatherHistorical", back_populates="station")
    
    __table_args__ = (
        Index('idx_station_location', 'province', 'city'),
        {'comment': '气象站信息表'}
    )


class WeatherRealtime(Base):
    """实时天气数据表"""
    __tablename__ = 'weather_realtime'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(50), ForeignKey('weather_stations.station_id'), nullable=False, index=True)
    observation_time = Column(DateTime, nullable=False, index=True, comment='观测时间')
    
    # 温度相关
    temperature = Column(Float, comment='温度(℃)')
    temperature_max = Column(Float, comment='最高温度(℃)')
    temperature_min = Column(Float, comment='最低温度(℃)')
    feels_like = Column(Float, comment='体感温度(℃)')
    
    # 湿度和气压
    humidity = Column(Float, comment='相对湿度(%)')
    pressure = Column(Float, comment='气压(hPa)')
    
    # 风力
    wind_speed = Column(Float, comment='风速(m/s)')
    wind_direction = Column(Float, comment='风向(度)')
    wind_direction_text = Column(String(20), comment='风向文字描述')
    wind_scale = Column(String(10), comment='风力等级')
    
    # 降水
    precipitation = Column(Float, comment='降水量(mm)')
    precipitation_1h = Column(Float, comment='1小时降水量(mm)')
    precipitation_24h = Column(Float, comment='24小时降水量(mm)')
    
    # 云量和能见度
    cloud_cover = Column(Float, comment='云量(%)')
    visibility = Column(Float, comment='能见度(km)')
    
    # 天气现象
    weather_code = Column(String(20), comment='天气代码')
    weather_text = Column(String(50), comment='天气文字描述')
    
    # 其他
    dew_point = Column(Float, comment='露点温度(℃)')
    uv_index = Column(Float, comment='紫外线指数')
    
    # 数据来源
    data_source = Column(String(50), comment='数据来源:qweather/openweather/cma')
    data_quality = Column(String(20), default='good', comment='数据质量:good/poor/missing')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    station = relationship("WeatherStation", back_populates="realtime_data")
    
    __table_args__ = (
        Index('idx_realtime_station_time', 'station_id', 'observation_time'),
        {'comment': '实时天气数据表'}
    )


class WeatherHistorical(Base):
    """历史天气数据表"""
    __tablename__ = 'weather_historical'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(50), ForeignKey('weather_stations.station_id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True, comment='日期')
    
    # 温度统计
    temperature_avg = Column(Float, comment='平均温度(℃)')
    temperature_max = Column(Float, comment='最高温度(℃)')
    temperature_min = Column(Float, comment='最低温度(℃)')
    
    # 湿度和气压统计
    humidity_avg = Column(Float, comment='平均湿度(%)')
    pressure_avg = Column(Float, comment='平均气压(hPa)')
    
    # 风力统计
    wind_speed_avg = Column(Float, comment='平均风速(m/s)')
    wind_speed_max = Column(Float, comment='最大风速(m/s)')
    wind_direction_dominant = Column(String(20), comment='主导风向')
    
    # 降水统计
    precipitation_total = Column(Float, comment='总降水量(mm)')
    precipitation_hours = Column(Float, comment='降水时数(小时)')
    
    # 其他统计
    sunshine_hours = Column(Float, comment='日照时数(小时)')
    cloud_cover_avg = Column(Float, comment='平均云量(%)')
    
    # 极端天气标记
    extreme_weather = Column(Boolean, default=False, comment='是否极端天气')
    extreme_type = Column(String(50), comment='极端天气类型')
    
    data_source = Column(String(50), comment='数据来源')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    station = relationship("WeatherStation", back_populates="historical_data")
    
    __table_args__ = (
        Index('idx_historical_station_date', 'station_id', 'date'),
        Index('idx_historical_extreme', 'extreme_weather', 'extreme_type'),
        {'comment': '历史天气数据表'}
    )


class WeatherAlert(Base):
    """天气预警表"""
    __tablename__ = 'weather_alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(100), unique=True, nullable=False, comment='预警ID')
    
    # 预警信息
    alert_type = Column(String(50), nullable=False, comment='预警类型:高温/低温/暴雨/台风/大风等')
    alert_level = Column(String(20), nullable=False, comment='预警等级:蓝色/黄色/橙色/红色')
    alert_title = Column(String(200), nullable=False, comment='预警标题')
    alert_text = Column(Text, comment='预警详情')
    
    # 地理范围
    province = Column(String(50), comment='省份')
    city = Column(String(50), comment='城市')
    affected_areas = Column(Text, comment='影响区域JSON')
    
    # 时间信息
    start_time = Column(DateTime, nullable=False, comment='预警开始时间')
    end_time = Column(DateTime, comment='预警结束时间')
    publish_time = Column(DateTime, default=datetime.now, comment='发布时间')
    update_time = Column(DateTime, comment='更新时间')
    
    # 状态
    status = Column(String(20), default='active', comment='状态:active/expired/cancelled')
    
    # 数据来源
    data_source = Column(String(50), comment='数据来源')
    source_url = Column(String(500), comment='来源链接')
    
    # 是否已推送
    is_pushed = Column(Boolean, default=False, comment='是否已推送')
    push_time = Column(DateTime, comment='推送时间')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_alert_type_level', 'alert_type', 'alert_level'),
        Index('idx_alert_location', 'province', 'city'),
        Index('idx_alert_time', 'start_time', 'end_time'),
        {'comment': '天气预警表'}
    )


class WeatherPrediction(Base):
    """天气预测表"""
    __tablename__ = 'weather_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(50), ForeignKey('weather_stations.station_id'), nullable=False, index=True)
    
    # 预测时间信息
    prediction_time = Column(DateTime, nullable=False, comment='预测生成时间')
    forecast_time = Column(DateTime, nullable=False, index=True, comment='预测目标时间')
    forecast_hours = Column(Integer, comment='预测时长(小时)')
    
    # 预测值
    temperature_predicted = Column(Float, comment='预测温度(℃)')
    precipitation_predicted = Column(Float, comment='预测降水量(mm)')
    humidity_predicted = Column(Float, comment='预测湿度(%)')
    wind_speed_predicted = Column(Float, comment='预测风速(m/s)')
    pressure_predicted = Column(Float, comment='预测气压(hPa)')
    
    # 实际值（用于验证）
    temperature_actual = Column(Float, comment='实际温度(℃)')
    precipitation_actual = Column(Float, comment='实际降水量(mm)')
    
    # 预测准确度
    prediction_accuracy = Column(Float, comment='预测准确度(%)')
    prediction_error = Column(Float, comment='预测误差')
    
    # 模型信息
    model_name = Column(String(50), comment='模型名称:LSTM/MLlib/etc')
    model_version = Column(String(20), comment='模型版本')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_prediction_station_time', 'station_id', 'forecast_time'),
        Index('idx_prediction_model', 'model_name', 'model_version'),
        {'comment': '天气预测表'}
    )


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, index=True, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    
    # 用户信息
    full_name = Column(String(100), comment='真实姓名')
    phone = Column(String(20), comment='手机号')
    organization = Column(String(200), comment='所属机构')
    
    # 角色和权限
    role = Column(String(20), default='public', nullable=False, comment='角色:public/researcher/industry/admin')
    is_active = Column(Boolean, default=True, comment='是否激活')
    is_verified = Column(Boolean, default=False, comment='是否认证')
    
    # API 使用
    api_key = Column(String(100), unique=True, comment='API密钥')
    api_quota_daily = Column(Integer, default=100, comment='每日API配额')
    api_calls_today = Column(Integer, default=0, comment='今日API调用次数')
    last_api_call = Column(DateTime, comment='最后API调用时间')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='注册时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    last_login = Column(DateTime, comment='最后登录时间')
    
    __table_args__ = (
        Index('idx_user_role', 'role', 'is_active'),
        {'comment': '用户表'}
    )


class DataProcessingLog(Base):
    """数据处理日志表"""
    __tablename__ = 'data_processing_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 任务信息
    job_type = Column(String(50), nullable=False, comment='任务类型:collection/batch/stream/prediction')
    job_name = Column(String(100), nullable=False, comment='任务名称')
    job_id = Column(String(100), comment='任务ID')
    
    # 执行信息
    status = Column(String(20), nullable=False, comment='状态:running/success/failed')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration_seconds = Column(Float, comment='执行时长(秒)')
    
    # 处理统计
    records_processed = Column(Integer, comment='处理记录数')
    records_success = Column(Integer, comment='成功记录数')
    records_failed = Column(Integer, comment='失败记录数')
    
    # 错误信息
    error_message = Column(Text, comment='错误信息')
    error_stack = Column(Text, comment='错误堆栈')
    
    # 资源使用
    cpu_usage = Column(Float, comment='CPU使用率(%)')
    memory_usage = Column(Float, comment='内存使用(MB)')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_log_type_status', 'job_type', 'status'),
        Index('idx_log_time', 'start_time', 'end_time'),
        {'comment': '数据处理日志表'}
    )


class SystemMetrics(Base):
    """系统监控指标表"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_time = Column(DateTime, nullable=False, index=True, comment='指标时间')
    
    # 系统资源
    cpu_usage = Column(Float, comment='CPU使用率(%)')
    memory_total = Column(Float, comment='总内存(MB)')
    memory_used = Column(Float, comment='已用内存(MB)')
    memory_usage = Column(Float, comment='内存使用率(%)')
    disk_total = Column(Float, comment='总磁盘(GB)')
    disk_used = Column(Float, comment='已用磁盘(GB)')
    disk_usage = Column(Float, comment='磁盘使用率(%)')
    
    # 应用指标
    api_requests_total = Column(Integer, comment='API请求总数')
    api_requests_success = Column(Integer, comment='API成功请求数')
    api_requests_failed = Column(Integer, comment='API失败请求数')
    api_response_time_avg = Column(Float, comment='API平均响应时间(ms)')
    
    # 数据处理指标
    data_collection_rate = Column(Float, comment='数据采集速率(条/秒)')
    data_processing_rate = Column(Float, comment='数据处理速率(条/秒)')
    kafka_lag = Column(Integer, comment='Kafka消息积压数')
    
    # HDFS 指标
    hdfs_capacity_total = Column(Float, comment='HDFS总容量(GB)')
    hdfs_capacity_used = Column(Float, comment='HDFS已用容量(GB)')
    hdfs_capacity_remaining = Column(Float, comment='HDFS剩余容量(GB)')
    
    # 数据库指标
    mysql_connections = Column(Integer, comment='MySQL连接数')
    mysql_queries_per_second = Column(Float, comment='MySQL查询速率(QPS)')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_metrics_time', 'metric_time'),
        {'comment': '系统监控指标表'}
    )


# 创建所有表的函数
def create_all_tables(engine):
    """创建所有数据库表"""
    Base.metadata.create_all(engine)
    print("所有数据库表创建成功！")


# 删除所有表的函数
def drop_all_tables(engine):
    """删除所有数据库表"""
    Base.metadata.drop_all(engine)
    print("所有数据库表已删除！")


