"""
用户认证 API 路由
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from loguru import logger
from datetime import timedelta

bp = Blueprint('user', __name__)


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    Request Body:
        - username: 用户名
        - password: 密码
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名或密码不能为空'
            }), 400
        
        # TODO: 验证用户名和密码
        # 这里使用模拟验证
        if username == 'admin' and password == 'admin123':
            # 创建访问令牌
            access_token = create_access_token(
                identity=username,
                expires_delta=timedelta(hours=24)
            )
            
            return jsonify({
                'code': 200,
                'message': '登录成功',
                'data': {
                    'access_token': access_token,
                    'token_type': 'Bearer',
                    'expires_in': 86400,  # 24小时
                    'user': {
                        'username': username,
                        'role': 'admin'
                    }
                }
            })
        else:
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误'
            }), 401
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'登录失败: {str(e)}'
        }), 500


@bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    
    Request Body:
        - username: 用户名
        - password: 密码
        - email: 邮箱
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({
                'code': 400,
                'message': '请填写完整信息'
            }), 400
        
        # TODO: 保存用户到数据库
        
        return jsonify({
            'code': 200,
            'message': '注册成功'
        })
        
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'注册失败: {str(e)}'
        }), 500


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息（需要认证）"""
    try:
        current_user = get_jwt_identity()
        
        # TODO: 从数据库获取用户信息
        user_info = {
            'username': current_user,
            'email': 'user@example.com',
            'role': 'researcher',
            'created_at': '2024-01-01T00:00:00'
        }
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': user_info
        })
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}'
        }), 500


