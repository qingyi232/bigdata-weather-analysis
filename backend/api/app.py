"""
Flask RESTful API 主应用
基于大数据的天气数据分析与可视化系统
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from loguru import logger
import yaml
import os
from datetime import datetime, timedelta

# 导入路由
from routes import weather_routes, analysis_routes, prediction_routes, user_routes

# 创建 Flask 应用
app = Flask(__name__)

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Flask 配置
app.config['SECRET_KEY'] = config['app']['secret_key']
app.config['JWT_SECRET_KEY'] = config['jwt']['secret_key']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=config['jwt']['access_token_expires'])

# 启用 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": config['api']['cors']['origins'],
        "methods": config['api']['cors']['methods']
    }
})

# 初始化 JWT
jwt = JWTManager(app)

# 注册蓝图（路由）
app.register_blueprint(weather_routes.bp, url_prefix='/api/v1/weather')
app.register_blueprint(analysis_routes.bp, url_prefix='/api/v1/analysis')
app.register_blueprint(prediction_routes.bp, url_prefix='/api/v1/prediction')
app.register_blueprint(user_routes.bp, url_prefix='/api/v1/user')


# ========== 基础路由 ==========

@app.route('/')
def index():
    """首页"""
    return jsonify({
        'message': '基于大数据的天气数据分析与可视化系统 API',
        'version': config['app']['version'],
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'api': 'running',
            'database': 'connected',  # TODO: 实际检查数据库连接
            'kafka': 'connected',  # TODO: 实际检查 Kafka 连接
            'hdfs': 'connected'  # TODO: 实际检查 HDFS 连接
        }
    })


@app.route('/api/v1/stats')
@jwt_required()
def system_stats():
    """系统统计信息（需要认证）"""
    # TODO: 从数据库获取实际统计信息
    return jsonify({
        'total_stations': 100,
        'total_records': 1000000,
        'realtime_data_rate': '100 records/minute',
        'storage_used': '50 GB',
        'last_update': datetime.now().isoformat()
    })


# ========== 错误处理 ==========

@app.errorhandler(400)
def bad_request(error):
    """400 错误处理"""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error),
        'code': 400
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    """401 错误处理"""
    return jsonify({
        'error': 'Unauthorized',
        'message': '未授权访问，请先登录',
        'code': 401
    }), 401


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        'error': 'Not Found',
        'message': '请求的资源不存在',
        'code': 404
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    """500 错误处理"""
    logger.error(f"Internal Server Error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': '服务器内部错误',
        'code': 500
    }), 500


# ========== 请求钩子 ==========

@app.before_request
def before_request():
    """请求前处理"""
    # 记录请求日志
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")


@app.after_request
def after_request(response):
    """请求后处理"""
    # 添加响应头
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response


# ========== JWT 回调 ==========

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """JWT 过期处理"""
    return jsonify({
        'error': 'Token Expired',
        'message': '令牌已过期，请重新登录',
        'code': 401
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """JWT 无效处理"""
    return jsonify({
        'error': 'Invalid Token',
        'message': '无效的令牌',
        'code': 401
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """缺少 JWT 处理"""
    return jsonify({
        'error': 'Missing Token',
        'message': '缺少认证令牌',
        'code': 401
    }), 401


# ========== 启动应用 ==========

if __name__ == '__main__':
    # 配置日志
    logger.add(
        "../logs/api_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    logger.info("="*60)
    logger.info("  基于大数据的天气数据分析与可视化系统")
    logger.info("  Flask API 服务")
    logger.info("="*60)
    logger.info(f"版本: {config['app']['version']}")
    logger.info(f"主机: {config['app']['host']}")
    logger.info(f"端口: {config['app']['port']}")
    logger.info(f"调试模式: {config['app']['debug']}")
    logger.info("="*60)
    
    # 启动应用
    app.run(
        host=config['app']['host'],
        port=config['app']['port'],
        debug=config['app']['debug']
    )


