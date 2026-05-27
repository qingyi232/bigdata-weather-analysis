"""
天气预测 API 路由
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from loguru import logger

bp = Blueprint('prediction', __name__)


@bp.route('/temperature', methods=['POST'])
@jwt_required()
def predict_temperature():
    """
    预测未来温度
    
    Request Body:
        - station_id: 站点ID
        - hours: 预测小时数（1-72）
    """
    try:
        data = request.get_json()
        station_id = data.get('station_id')
        hours = data.get('hours', 3)
        
        if not station_id:
            return jsonify({
                'code': 400,
                'message': '缺少参数: station_id'
            }), 400
        
        # TODO: 调用 LSTM 预测模型
        mock_prediction = {
            'station_id': station_id,
            'prediction_hours': hours,
            'predicted_temperature': 26.5,
            'confidence': 0.85,
            'model': 'LSTM',
            'prediction_time': '2024-01-01T12:00:00'
        }
        
        return jsonify({
            'code': 200,
            'message': '预测成功',
            'data': mock_prediction
        })
        
    except Exception as e:
        logger.error(f"温度预测失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'预测失败: {str(e)}'
        }), 500


@bp.route('/precipitation', methods=['POST'])
@jwt_required()
def predict_precipitation():
    """
    预测未来降水
    
    Request Body:
        - station_id: 站点ID
        - hours: 预测小时数（1-72）
    """
    try:
        data = request.get_json()
        station_id = data.get('station_id')
        hours = data.get('hours', 3)
        
        # TODO: 调用 LSTM 预测模型
        mock_prediction = {
            'station_id': station_id,
            'prediction_hours': hours,
            'predicted_precipitation': 5.2,
            'confidence': 0.78,
            'model': 'LSTM'
        }
        
        return jsonify({
            'code': 200,
            'message': '预测成功',
            'data': mock_prediction
        })
        
    except Exception as e:
        logger.error(f"降水预测失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'预测失败: {str(e)}'
        }), 500


