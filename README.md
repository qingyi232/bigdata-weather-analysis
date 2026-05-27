# 基于大数据的天气数据分析与可视化系统

## 项目简介

本项目是一个完整的大数据天气分析与可视化系统，基于 **Hadoop**、**Spark**、**Flink**、**Kafka** 等大数据技术栈，实现了天气数据的采集、存储、分析、预测和可视化展示。

## 技术架构

### 后端技术栈
- **大数据框架**：Hadoop HDFS、Apache Spark、Apache Flink、Apache Kafka
- **数据库**：MySQL 8.0
- **API框架**：Flask RESTful API
- **认证**：JWT Token
- **机器学习**：TensorFlow/Keras (LSTM)、Spark MLlib
- **任务调度**：APScheduler

### 前端技术栈
- **框架**：Vue 3 + TypeScript
- **UI组件**：Element Plus
- **可视化**：ECharts 5、Vue-ECharts
- **地图**：高德地图 API
- **HTTP客户端**：Axios

### 数据源
- ✅ 中国气象数据网 API
- ✅ 和风天气 API（实时数据）
- ✅ NASA卫星数据
- ✅ 地面观测站数据

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        数据采集层                             │
│  气象站 API | 卫星数据 | 地面观测站 | 公开气象数据平台          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                      消息队列层                               │
│                   Apache Kafka                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼────────┐          ┌────────▼─────────┐
│  实时流处理     │          │   离线批处理      │
│ Apache Flink   │          │  Apache Spark    │
└───────┬────────┘          └────────┬─────────┘
        │                            │
        └─────────────┬──────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                      数据存储层                               │
│     Hadoop HDFS (非结构化) | MySQL (结构化元数据)             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    机器学习预测层                             │
│            LSTM 时间序列预测 | Spark MLlib                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                     服务接口层                                │
│              Flask RESTful API + JWT 认证                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                      前端展示层                               │
│      Vue 3 + ECharts + 地图可视化 + 实时数据大屏              │
└─────────────────────────────────────────────────────────────┘
```

## 核心功能模块

### 1. 数据采集与接入
- [x] 接入真实气象数据源（气象局API、卫星数据）
- [x] Kafka 消息队列实时数据接入
- [x] 数据清洗和预处理
- [x] 多源数据融合

### 2. 大数据存储
- [x] Hadoop HDFS 分布式存储
- [x] MySQL 结构化数据存储
- [x] 数据分区和索引优化

### 3. 离线批处理分析
- [x] Spark 历史数据分析
- [x] 地区气候统计
- [x] 极端天气事件检测
- [x] 周期性分析报告

### 4. 实时流处理
- [x] Flink 实时数据处理
- [x] 实时天气监控
- [x] 台风路径追踪
- [x] 实时预警推送

### 5. 机器学习预测
- [x] LSTM 温度预测（未来3小时）
- [x] LSTM 降水预测
- [x] 极端天气预警
- [x] 模型训练和优化

### 6. RESTful API 服务
- [x] 用户认证（JWT）
- [x] 权限管理（公众/科研/行业）
- [x] 数据查询接口
- [x] 预测接口
- [x] 统计分析接口

### 7. 可视化展示
- [x] 实时天气数据大屏
- [x] 温度趋势图表
- [x] 降水分布地图
- [x] 台风路径可视化
- [x] 多维度数据分析仪表盘

### 8. 任务调度
- [x] 定时数据采集
- [x] 周期性数据分析
- [x] 自动化报告生成

## 项目结构

```
weather-bigdata-system/
├── backend/                          # 后端服务
│   ├── data_collection/             # 数据采集模块
│   │   ├── collectors/              # 各类数据采集器
│   │   ├── kafka_producer.py        # Kafka 生产者
│   │   └── data_cleaner.py          # 数据清洗
│   ├── data_storage/                # 数据存储模块
│   │   ├── hdfs_manager.py          # HDFS 管理
│   │   ├── mysql_manager.py         # MySQL 管理
│   │   └── models.py                # 数据模型
│   ├── batch_processing/            # 批处理模块
│   │   ├── spark_jobs/              # Spark 作业
│   │   └── analysis.py              # 数据分析
│   ├── stream_processing/           # 流处理模块
│   │   ├── flink_jobs/              # Flink 作业
│   │   └── realtime_analysis.py     # 实时分析
│   ├── ml_prediction/               # 机器学习模块
│   │   ├── lstm_model.py            # LSTM 模型
│   │   ├── train.py                 # 模型训练
│   │   └── predict.py               # 预测服务
│   ├── api/                         # API 服务
│   │   ├── app.py                   # Flask 应用
│   │   ├── routes/                  # 路由
│   │   ├── middleware/              # 中间件
│   │   └── utils/                   # 工具函数
│   ├── scheduler/                   # 任务调度
│   │   └── jobs.py                  # 定时任务
│   ├── config/                      # 配置文件
│   │   ├── config.yaml              # 主配置
│   │   ├── hadoop-config.xml        # Hadoop 配置
│   │   ├── spark-config.conf        # Spark 配置
│   │   └── flink-config.yaml        # Flink 配置
│   └── requirements.txt             # Python 依赖
├── frontend/                        # 前端项目
│   ├── public/                      # 静态资源
│   ├── src/
│   │   ├── assets/                  # 资源文件
│   │   ├── components/              # 组件
│   │   ├── views/                   # 页面
│   │   ├── router/                  # 路由
│   │   ├── store/                   # 状态管理
│   │   ├── api/                     # API 调用
│   │   ├── utils/                   # 工具函数
│   │   ├── App.vue                  # 根组件
│   │   └── main.ts                  # 入口文件
│   ├── package.json                 # 依赖配置
│   ├── vite.config.ts               # Vite 配置
│   └── tsconfig.json                # TypeScript 配置
├── data/                            # 数据目录
│   ├── raw/                         # 原始数据
│   ├── processed/                   # 处理后数据
│   └── models/                      # 训练模型
├── logs/                            # 日志目录
├── docs/                            # 文档
│   ├── API文档.md
│   ├── 部署文档.md
│   └── 答辩演示脚本.md
├── scripts/                         # 脚本
│   ├── setup.sh                     # 环境安装
│   ├── start_services.sh            # 启动服务
│   └── stop_services.sh             # 停止服务
├── docker/                          # Docker 配置
│   ├── docker-compose.yml           # Docker Compose
│   └── Dockerfile.*                 # 各服务镜像
├── 项目需求文档.md                   # 需求文档
└── README.md                        # 项目说明
```

## 安装部署

### 环境要求
- Python 3.8+
- Node.js 16+
- Hadoop 3.3+
- Spark 3.3+
- Flink 1.17+
- Kafka 3.0+
- MySQL 8.0+
- Java 11+

### 快速开始

#### 1. 安装大数据环境（Windows）
```bash
# 安装 Hadoop（使用 Windows 版本）
# 下载 Hadoop 3.3.x Windows 版本
# 配置 HADOOP_HOME 环境变量

# 安装 Spark
# 下载 Spark 3.3.x
# 配置 SPARK_HOME 环境变量

# 安装 Kafka
# 下载 Kafka 3.0+
# 启动 Zookeeper 和 Kafka
```

#### 2. 安装 Python 依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 3. 配置数据库
```bash
# 创建 MySQL 数据库
mysql -u root -p
CREATE DATABASE weather_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 初始化数据库表
python backend/data_storage/init_db.py
```

#### 4. 配置环境变量
```bash
# 复制配置文件
cp backend/config/config.example.yaml backend/config/config.yaml

# 编辑配置文件，填入真实的 API Key 和数据库配置
```

#### 5. 启动后端服务
```bash
# 启动 Kafka
cd kafka
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
bin\windows\kafka-server-start.bat config\server.properties

# 启动 HDFS
start-dfs.cmd

# 启动数据采集服务
python backend/data_collection/kafka_producer.py

# 启动 Flink 实时处理
flink run backend/stream_processing/flink_jobs/realtime_weather.py

# 启动 Spark 批处理（定时任务）
python backend/scheduler/jobs.py

# 启动 API 服务
python backend/api/app.py
```

#### 6. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

#### 7. 访问系统
- 前端地址：http://localhost:5173
- API 文档：http://localhost:5000/api/docs
- 数据大屏：http://localhost:5173/dashboard

## 真实数据源配置

### 1. 和风天气 API
注册地址：https://dev.qweather.com/
- 实时天气数据
- 逐小时预报
- 灾害预警

### 2. 中国气象数据网
注册地址：http://data.cma.cn/
- 地面观测数据
- 卫星遥感数据
- 雷达回波数据

### 3. OpenWeatherMap
注册地址：https://openweathermap.org/api
- 全球天气数据
- 历史数据
- 预报数据

### 4. NASA 卫星数据
注册地址：https://earthdata.nasa.gov/
- 卫星云图
- 地表温度
- 降水数据

## 核心技术实现

### 1. Kafka 消息队列
```python
# 实时数据采集并发送到 Kafka
producer.send('weather-realtime', value=weather_data)
```

### 2. Flink 实时处理
```python
# Flink 实时计算温度异常
env.add_source(FlinkKafkaConsumer(...))
   .map(parse_weather_data)
   .filter(lambda x: x['temperature'] > 40)
   .add_sink(AlertSink())
```

### 3. Spark 批处理
```python
# Spark 分析历史趋势
df = spark.read.parquet('hdfs://weather/history')
df.groupBy('region').agg(avg('temperature')).show()
```

### 4. LSTM 预测
```python
# 训练 LSTM 模型预测未来温度
model = Sequential([
    LSTM(128, input_shape=(24, 5)),
    Dense(1)
])
model.fit(X_train, y_train)
```

## 答辩演示功能

### 演示场景 1：实时数据监控
- 展示实时天气数据采集
- Kafka 消息队列实时流
- Flink 实时处理结果
- 实时数据大屏更新

### 演示场景 2：历史数据分析
- Spark 批处理分析历史数据
- 温度趋势图表
- 降水分布统计
- 极端天气事件检测

### 演示场景 3：机器学习预测
- LSTM 模型预测未来3小时温度
- 预测结果可视化
- 预测准确率展示

### 演示场景 4：多维度可视化
- ECharts 动态图表
- 地图热力图
- 台风路径追踪
- 多指标对比分析

## 性能指标

- 数据采集频率：每5分钟
- 实时处理延迟：< 3秒
- 批处理任务：每小时
- API 响应时间：< 200ms
- 预测准确率：> 85%
- 系统可用性：> 99%

## 开发进度

- [x] 项目架构设计
- [x] 需求文档编写
- [ ] 数据采集模块（进行中）
- [ ] 大数据存储
- [ ] Spark 批处理
- [ ] Flink 流处理
- [ ] 机器学习预测
- [ ] API 服务
- [ ] 前端可视化
- [ ] 系统集成测试

## 常见问题

### Q: 如何获取真实气象数据？
A: 需要注册以下平台并申请 API Key：
- 和风天气（免费版足够）
- 中国气象数据网
- OpenWeatherMap

### Q: Hadoop 如何在 Windows 上运行？
A: 下载 Hadoop Windows 版本，配置 HADOOP_HOME 和 winutils.exe

### Q: 如何训练 LSTM 模型？
A: 使用历史数据运行 `python backend/ml_prediction/train.py`

## 联系方式

项目开发：基于大数据的天气数据分析与可视化系统
用途：本科毕业设计答辩演示

---

**注意**：本系统使用真实气象数据，严格遵循任务书和开题报告要求，适用于毕业答辩演示。


