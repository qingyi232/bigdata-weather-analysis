"""
LSTM 时间序列预测模型
用于预测未来天气（温度、降水量等）
"""

import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from loguru import logger
import yaml
import os
import joblib
from datetime import datetime, timedelta


class LSTMWeatherPredictor:
    """LSTM 天气预测器"""
    
    def __init__(self, config_path=None, model_type='temperature'):
        """
        初始化 LSTM 预测器
        
        Args:
            config_path: 配置文件路径
            model_type: 模型类型 (temperature/precipitation)
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.model_type = model_type
        self.config = config['machine_learning']['lstm'][model_type]
        
        # 模型参数
        self.sequence_length = self.config['sequence_length']
        self.prediction_hours = self.config['prediction_hours']
        self.hidden_units = self.config['hidden_units']
        self.input_features = self.config['input_features']
        self.output_feature = self.config['output_feature']
        
        # 数据标准化器
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        
        # 模型
        self.model = None
        self.model_path = self.config['model_path']
        
        logger.info(f"LSTM {model_type} 预测器初始化成功")
    
    def prepare_data(self, df, target_column):
        """
        准备训练数据
        
        Args:
            df: pandas DataFrame (包含时间序列数据)
            target_column: 目标列名
            
        Returns:
            X_train, y_train, X_test, y_test
        """
        logger.info(f"准备训练数据: {len(df)} 条记录")
        
        # 选择特征列
        feature_columns = [col for col in self.input_features if col in df.columns]
        
        if target_column not in df.columns:
            logger.error(f"目标列 {target_column} 不存在")
            return None, None, None, None
        
        # 提取特征和目标
        X_data = df[feature_columns].values
        y_data = df[[target_column]].values
        
        # 标准化
        X_scaled = self.scaler_X.fit_transform(X_data)
        y_scaled = self.scaler_y.fit_transform(y_data)
        
        # 创建时间序列样本
        X, y = [], []
        
        for i in range(len(X_scaled) - self.sequence_length - self.prediction_hours + 1):
            # 输入序列：过去 sequence_length 小时的数据
            X.append(X_scaled[i:i + self.sequence_length])
            
            # 输出：未来 prediction_hours 小时后的值
            y.append(y_scaled[i + self.sequence_length + self.prediction_hours - 1])
        
        X = np.array(X)
        y = np.array(y)
        
        # 划分训练集和测试集
        split_idx = int(len(X) * 0.8)
        
        X_train = X[:split_idx]
        y_train = y[:split_idx]
        X_test = X[split_idx:]
        y_test = y[split_idx:]
        
        logger.info(
            f"数据准备完成: "
            f"训练集 {len(X_train)} 样本, "
            f"测试集 {len(X_test)} 样本, "
            f"特征维度 {X_train.shape}"
        )
        
        return X_train, y_train, X_test, y_test
    
    def build_model(self, input_shape):
        """
        构建 LSTM 模型
        
        Args:
            input_shape: 输入形状 (sequence_length, n_features)
            
        Returns:
            Keras 模型
        """
        logger.info(f"构建 LSTM 模型: 输入形状 {input_shape}")
        
        model = Sequential([
            # 第一层 LSTM
            LSTM(
                units=self.hidden_units,
                return_sequences=True,
                input_shape=input_shape
            ),
            Dropout(0.2),
            
            # 第二层 LSTM
            LSTM(
                units=self.hidden_units // 2,
                return_sequences=False
            ),
            Dropout(0.2),
            
            # 全连接层
            Dense(units=32, activation='relu'),
            Dropout(0.2),
            
            # 输出层
            Dense(units=1)
        ])
        
        # 编译模型
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("LSTM 模型构建完成")
        logger.info(f"模型参数量: {model.count_params():,}")
        
        return model
    
    def train(self, X_train, y_train, X_val, y_val):
        """
        训练模型
        
        Args:
            X_train: 训练集特征
            y_train: 训练集标签
            X_val: 验证集特征
            y_val: 验证集标签
            
        Returns:
            训练历史
        """
        logger.info("开始训练 LSTM 模型...")
        
        # 构建模型
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self.build_model(input_shape)
        
        # 回调函数
        callbacks = [
            # 早停
            EarlyStopping(
                monitor='val_loss',
                patience=self.config.get('early_stopping_patience', 10),
                restore_best_weights=True,
                verbose=1
            ),
            
            # 保存最佳模型
            ModelCheckpoint(
                filepath=self.model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # 训练
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config['epochs'],
            batch_size=self.config['batch_size'],
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("LSTM 模型训练完成")
        
        return history
    
    def evaluate(self, X_test, y_test):
        """
        评估模型
        
        Args:
            X_test: 测试集特征
            y_test: 测试集标签
            
        Returns:
            评估指标字典
        """
        logger.info("评估模型性能...")
        
        if self.model is None:
            logger.error("模型未训练或加载")
            return None
        
        # 预测
        y_pred_scaled = self.model.predict(X_test, verbose=0)
        
        # 反标准化
        y_test_original = self.scaler_y.inverse_transform(y_test)
        y_pred_original = self.scaler_y.inverse_transform(y_pred_scaled)
        
        # 计算指标
        mae = mean_absolute_error(y_test_original, y_pred_original)
        mse = mean_squared_error(y_test_original, y_pred_original)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test_original, y_pred_original)
        
        # 计算准确率（在一定误差范围内）
        tolerance = 2.0  # 容忍误差 ±2°C 或 ±2mm
        accuracy = np.mean(np.abs(y_test_original - y_pred_original) <= tolerance) * 100
        
        metrics = {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'r2': float(r2),
            'accuracy': float(accuracy),
            'tolerance': tolerance
        }
        
        logger.info(
            f"模型评估完成: "
            f"MAE={mae:.3f}, "
            f"RMSE={rmse:.3f}, "
            f"R²={r2:.3f}, "
            f"准确率={accuracy:.2f}%"
        )
        
        return metrics
    
    def predict(self, recent_data):
        """
        预测未来天气
        
        Args:
            recent_data: 最近的数据 DataFrame (至少 sequence_length 条)
            
        Returns:
            预测值（原始尺度）
        """
        if self.model is None:
            logger.error("模型未训练或加载")
            return None
        
        # 提取特征
        feature_columns = [col for col in self.input_features if col in recent_data.columns]
        X_recent = recent_data[feature_columns].tail(self.sequence_length).values
        
        if len(X_recent) < self.sequence_length:
            logger.error(f"数据不足：需要 {self.sequence_length} 条，实际 {len(X_recent)} 条")
            return None
        
        # 标准化
        X_scaled = self.scaler_X.transform(X_recent)
        X_input = X_scaled.reshape(1, self.sequence_length, -1)
        
        # 预测
        y_pred_scaled = self.model.predict(X_input, verbose=0)
        
        # 反标准化
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled)
        
        prediction_value = float(y_pred[0, 0])
        
        logger.info(f"预测完成: {self.output_feature} = {prediction_value:.2f}")
        
        return prediction_value
    
    def save_model(self, path=None):
        """保存模型和标准化器"""
        if path is None:
            path = self.model_path
        
        try:
            # 保存 Keras 模型
            self.model.save(path)
            
            # 保存标准化器
            scaler_path = path.replace('.h5', '_scalers.pkl')
            joblib.dump({
                'scaler_X': self.scaler_X,
                'scaler_y': self.scaler_y
            }, scaler_path)
            
            logger.info(f"模型保存成功: {path}")
            return True
            
        except Exception as e:
            logger.error(f"模型保存失败: {str(e)}")
            return False
    
    def load_model(self, path=None):
        """加载模型和标准化器"""
        if path is None:
            path = self.model_path
        
        try:
            # 加载 Keras 模型
            self.model = load_model(path)
            
            # 加载标准化器
            scaler_path = path.replace('.h5', '_scalers.pkl')
            scalers = joblib.load(scaler_path)
            self.scaler_X = scalers['scaler_X']
            self.scaler_y = scalers['scaler_y']
            
            logger.info(f"模型加载成功: {path}")
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            return False


def generate_sample_data(n_samples=1000):
    """生成模拟天气数据用于测试"""
    dates = pd.date_range(start='2023-01-01', periods=n_samples, freq='H')
    
    # 生成带有季节性的温度数据
    t = np.arange(n_samples)
    temperature = 15 + 10 * np.sin(2 * np.pi * t / (24 * 365)) + np.random.normal(0, 2, n_samples)
    humidity = 50 + 20 * np.sin(2 * np.pi * t / (24 * 180)) + np.random.normal(0, 5, n_samples)
    pressure = 1013 + 10 * np.sin(2 * np.pi * t / (24 * 90)) + np.random.normal(0, 3, n_samples)
    wind_speed = 5 + 3 * np.abs(np.sin(2 * np.pi * t / (24 * 30))) + np.random.normal(0, 1, n_samples)
    precipitation = np.maximum(0, np.random.exponential(2, n_samples))
    
    df = pd.DataFrame({
        'observation_time': dates,
        'temperature': temperature,
        'humidity': humidity,
        'pressure': pressure,
        'wind_speed': wind_speed,
        'precipitation': precipitation
    })
    
    return df


if __name__ == "__main__":
    """测试 LSTM 预测器"""
    
    # 配置日志
    logger.add(
        "../logs/lstm_model.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    print("="*60)
    print("  LSTM 天气预测模型测试")
    print("="*60)
    
    # 生成测试数据
    print("\n📊 生成模拟数据...")
    df = generate_sample_data(n_samples=2000)
    print(f"✅ 生成 {len(df)} 条数据")
    
    # 创建预测器
    print("\n🤖 创建 LSTM 温度预测器...")
    predictor = LSTMWeatherPredictor(model_type='temperature')
    
    # 准备数据
    print("\n📦 准备训练数据...")
    X_train, y_train, X_test, y_test = predictor.prepare_data(df, 'temperature')
    
    # 训练模型
    print("\n🚀 开始训练模型...")
    history = predictor.train(X_train, y_train, X_test, y_test)
    
    # 评估模型
    print("\n📈 评估模型...")
    metrics = predictor.evaluate(X_test, y_test)
    print(f"\n模型评估结果:")
    print(f"  - MAE: {metrics['mae']:.3f}")
    print(f"  - RMSE: {metrics['rmse']:.3f}")
    print(f"  - R²: {metrics['r2']:.3f}")
    print(f"  - 准确率: {metrics['accuracy']:.2f}% (误差 ±{metrics['tolerance']}°C)")
    
    # 测试预测
    print("\n🔮 测试预测...")
    recent_data = df.tail(24)  # 最近24小时数据
    prediction = predictor.predict(recent_data)
    print(f"✅ 预测未来{predictor.prediction_hours}小时温度: {prediction:.2f}°C")
    
    # 保存模型
    print("\n💾 保存模型...")
    predictor.save_model()
    
    print("\n✅ LSTM 预测模型测试完成")


