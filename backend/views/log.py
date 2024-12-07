import os
from flask import Blueprint, request, jsonify
from datetime import datetime

log_blueprint = Blueprint('log', __name__)

@log_blueprint.route('/logs', methods=['GET'])
def get_logs():
    log_level = request.args.get('level', 'ALL').upper()  # 获取日志级别
    start_date = request.args.get('start_date')  # 获取开始日期
    end_date = request.args.get('end_date')  # 获取结束日期
    include_details = request.args.get('include_details', 'true').lower() == 'true'
    page = int(request.args.get('page', 1))  # 获取页码，默认第一页
    page_size = int(request.args.get('page_size', 20))  # 获取页大小，默认每页 20 条

    logs_directory = 'logs/'
    filtered_logs = []

    # 遍历日志文件夹中的所有日志文件
    for log_file in os.listdir(logs_directory):
        log_file_path = os.path.join(logs_directory, log_file)

        # 检查是否为文件
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

        log_file_path = os.path.join(logs_directory, log_file)
        try:
            with open(log_file_path, 'r') as file:
                for line in file:
                    # 检查日志级别
                    if log_level != 'ALL' and f"| {log_level} |" not in line:
                        continue

                    # 如果选择不显示详细信息，仅去掉文件名、函数名、行号等
                    if not include_details:
                        # 日志格式为：{time} | {level} | {file}:{function}:{line} - {message}
                        parts = line.split(" - ", 1)
                        if len(parts) == 2:
                            main_info = parts[0].split(" | ")[:2]  # 保留时间和日志级别
                            line = " | ".join(main_info) + " | " + parts[1].strip()  # 拼接主信息和日志内容

                    filtered_logs.append(line)
        except FileNotFoundError:
            continue

    # 将日志按照从新到旧的顺序排列
    filtered_logs.sort(reverse=True)

    # 实现分页
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
    log_file_path = "logs/login/login.log"
    logs = []

    # 检查日志文件是否存在
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as file:
            logs = file.readlines()

    # 按时间倒序处理日志（最新的在前）
    logs.reverse()

    # 只保留每个 IP 的最新记录
    unique_logs = {}
    for line in logs:
        try:
            parts = line.strip().split(" | ")
            if len(parts) == 3:  # 确保日志有 3 部分
                raw_time = parts[0]  # 获取时间戳
                username = parts[1].split(": ")[1]
                ip_address = parts[2].split(": ")[1]

                # 将时间戳转换为本地时间
                utc_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S.%f%z")
                local_time = utc_time.astimezone()  # 转为本地时区
                formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

                # 记录最新的 IP 登录信息
                unique_logs[ip_address] = {
                    "time": formatted_time,  # 格式化后的时间
                    "ip_address": ip_address,
                    "username": username
                }
        except IndexError as e:
            print(f"解析失败: {line.strip()}, 错误: {e}")

    # 转换为列表返回
    return jsonify({"logs": list(unique_logs.values())})