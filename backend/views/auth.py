import jwt
import bcrypt
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from backend.core.config import SECRET_KEY, REFRESH_WINDOW, users
from backend.utils.logging_config import loguru_logger as logger

# 创建蓝图实例
auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/auth/login', methods=['POST'])
def login():
    """处理用户登录并生成 JWT"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 检查用户是否存在
    if username not in users:
        return jsonify({"message": "用户名或密码错误"}), 401

    # 检查密码是否正确
    stored_password_hash = users[username]
    if not bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
        return jsonify({"message": "用户名或密码错误"}), 401

    # 生成 JWT Token
    token = generate_token(username)

    ip_address = request.remote_addr  # 获取 IP 地址
    
    # 在登录成功后记录日志
    logger.bind(username=username, ip_address=ip_address).info("登录成功")

    return jsonify({"token": token}), 200

@auth_blueprint.route('/auth/refresh', methods=['POST'])
def refresh_token():
    token = request.headers.get('Authorization')
    if not token or not token.startswith("Bearer "):
        return jsonify({"message": "Token is missing or invalid!"}), 401

    token = token.split(" ")[1]
    try:
        # 解码 Token，忽略过期时间
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})

        # 检查是否包含 iat 字段
        if 'iat' not in data:
            return jsonify({"message": "Token is invalid: missing 'iat'!"}), 401

        # 使用 iat 检查刷新窗口
        issued_at = datetime.fromtimestamp(data['iat'], timezone.utc)
        now = datetime.now(timezone.utc)
        if now - issued_at > REFRESH_WINDOW:
            return jsonify({"message": "Token refresh window has expired!"}), 401

        # 生成新 Token
        new_token = generate_token(data['username'])
        return jsonify({"token": new_token}), 200
    except jwt.InvalidTokenError as e:
        return jsonify({"message": "Invalid token!"}), 401
    
def generate_token(username):
    """生成 JWT Token"""
    return jwt.encode(
        {
            "username": username,
            "iat": datetime.now(timezone.utc),  # 添加签发时间
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)  # 使用 UTC 时间
        },
        SECRET_KEY,
        algorithm="HS256"
    )
