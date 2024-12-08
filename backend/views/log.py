import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.utils.logging_config import loguru_logger as logger,LOGS_DIR, LOGIN_LOG_FILE  # 引入配置

log_blueprint = Blueprint('log', __name__)

@log_blueprint.route('/logs', methods=['GET'])
def get_logs():
    log_level = request.args.get('level', 'ALL').upper()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    include_details = request.args.get('include_details', 'true').lower() == 'true'
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    filtered_logs = []

    # 遍历日志文件夹中的所有日志文件
    try:
        for log_file in os.listdir(LOGS_DIR):
            log_file_path = os.path.join(LOGS_DIR, log_file)

            if not os.path.isfile(log_file_path):
                continue

            log_date_str = log_file.replace('app_', '').replace('.log', '')
            log_date = datetime.strptime(log_date_str, '%Y-%m-%d')

            # 检查日志文件是否在查询日期范围内
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if not (start_dt <= log_date <= end_dt):
                    continue

            with open(log_file_path, 'r') as file:
                for line in file:
                    if log_level != 'ALL' and f"| {log_level} |" not in line:
                        continue

                    if not include_details:
                        parts = line.split(" - ", 1)
                        if len(parts) == 2:
                            main_info = parts[0].split(" | ")[:2]
                            line = " | ".join(main_info) + " | " + parts[1].strip()

                    filtered_logs.append(line)
    except Exception as e:
        return jsonify({"error": f"读取日志时出现错误: {e}"}), 500

    filtered_logs.sort(reverse=True)

    total_logs = len(filtered_logs)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_logs = filtered_logs[start_index:end_index]

    return jsonify({
        'logs': paginated_logs,
        'total': total_logs,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_logs + page_size - 1) // page_size
    })

@log_blueprint.route('/login_logs', methods=['GET'])
def get_login_logs():
    logs = []

    if os.path.exists(LOGIN_LOG_FILE):
        try:
            with open(LOGIN_LOG_FILE, 'r') as file:
                logs = file.readlines()
        except Exception as e:
            return jsonify({"error": f"读取登录日志时出现错误: {e}"}), 500

    logs.reverse()

    unique_logs = {}
    for line in logs:
        try:
            parts = line.strip().split(" | ")
            if len(parts) == 3:
                raw_time = parts[0]
                username = parts[1].split(": ")[1]
                ip_address = parts[2].split(": ")[1]

                utc_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S.%f%z")
                local_time = utc_time.astimezone()
                formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

                unique_logs[ip_address] = {
                    "time": formatted_time,
                    "ip_address": ip_address,
                    "username": username
                }
        except IndexError as e:
            logger.error(f"解析失败: {line.strip()}, 错误: {e}")

    return jsonify({"logs": list(unique_logs.values())})
