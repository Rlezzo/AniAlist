import jwt
from flask import request, jsonify
from backend.core.config import SECRET_KEY
from backend.utils.logging_config import loguru_logger as logger

def token_required_middleware(blueprints):
    def middleware():
        # 跳过预检请求
        if request.method == 'OPTIONS':
            return None  # 允许预检请求通过

        token = request.headers.get('Authorization')  # 安全获取 Authorization
        if not token or not token.startswith("Bearer "):
            logger.warning("Token not found or invalid format in Authorization header.")
            return jsonify({"message": "Token is missing or invalid!"}), 401

        token = token.split(" ")[1]  # 提取 Token
        try:
            # 解码 Token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            logger.debug(f"Decoded Token: {data}")  # 打印解码结果
            request.current_user = data['username']  # 将用户信息存储到 request 上
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired.")
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid Token: {e}")
            return jsonify({"message": "Invalid token!"}), 401

    # 注册中间件到蓝图
    for blueprint in blueprints:
        blueprint.before_request(middleware)


