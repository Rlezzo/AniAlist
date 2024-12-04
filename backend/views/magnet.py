from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from anime2.backend.services import magnet_service
from backend.database.models import Magnet

magnet_blueprint = Blueprint('magnet', __name__)

# 获取全部 magnet
@magnet_blueprint.route('/magnets', methods=['GET'])
async def get_all_magnets():
    try:
        magnets = await magnet_service.get_all_magnets()
        return jsonify([{
            "id": magnet.id,
            "rss_feed_id": magnet.rss_feed_id,
            "title": magnet.title,
            "name": magnet.name,
            "magnet_link": magnet.magnet_link,
            "status": magnet.status,
            "timestamp": magnet.timestamp
        } for magnet in magnets])
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# 根据 ID 获取 magnet
@magnet_blueprint.route('/magnets/<int:magnet_id>', methods=['GET'])
async def get_magnet(magnet_id):
    try:
        magnet = await magnet_service.get_magnet_by_id(magnet_id)
        if magnet:
            return jsonify({
                "id": magnet.id,
                "rss_feed_id": magnet.rss_feed_id,
                "title": magnet.title,
                "name": magnet.name,
                "magnet_link": magnet.magnet_link,
                "status": magnet.status,
                "timestamp": magnet.timestamp
            })
        return jsonify({"error": "magnet not found"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# 创建 magnet
@magnet_blueprint.route('/magnets', methods=['POST'])
async def create_magnet():
    data = request.json
    try:
        await magnet_service.create_magnet(data)
        return jsonify({"message": "magnet created successfully!"}), 201
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# 修改 magnet
@magnet_blueprint.route('/magnets/<int:magnet_id>', methods=['PUT'])
async def update_magnet(magnet_id):
    data = request.json
    try:
        updated = await magnet_service.update_magnet(magnet_id, data)
        if updated:
            return jsonify({"message": "magnet updated successfully!"})
        return jsonify({"error": "magnet not found"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# 删除 magnet
@magnet_blueprint.route('/magnets/<int:magnet_id>', methods=['DELETE'])
async def delete_magnet(magnet_id):
    try:
        deleted = await magnet_service.delete_magnet(magnet_id)
        if deleted:
            return jsonify({"message": "magnet deleted successfully!"})
        return jsonify({"error": "magnet not found"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# 重试
@magnet_blueprint.route('/magnets/retry', methods=['POST'])
async def retry_magnet():
    """
    重试下载任务，直接接受一个任务对象。
    """
    data = request.json
    magnet_data = data.get('magnet')

    if not magnet_data:
        return jsonify({"error": "Invalid request data, magnet is required"}), 400

    # 创建 magnet 对象
    magnet = Magnet(
        rss_feed_id=magnet_data.get('rss_feed_id'),
        title=magnet_data.get('title'),
        magnet_link=magnet_data.get('magnet_link'),
        name=magnet_data.get('name', magnet_data.get('title')),
        status=magnet_data.get('status', False)
    )

    # 调用 execute_magnet 方法执行任务
    magnet_queue_manager = current_app.config['MAGNET_QUEUE_MANAGER']
    try:
        await magnet_queue_manager.interrupt_and_retry_task(magnet)
        return jsonify({"message": "任务重试成功"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@magnet_blueprint.route('/magnets/rss/<int:rss_id>', methods=['GET'])
async def get_magnets_by_rss(rss_id):
    """
    获取特定 RSS 订阅源的所有任务。
    :param rss_id: RSS 源的 ID
    :return: 包含任务列表的 JSON 响应
    """
    try:
        magnets = await magnet_service.get_magnets_by_rss(rss_id)
        if magnets:
            return jsonify([{
                "id": magnet.id,
                "rss_feed_id": magnet.rss_feed_id,
                "title": magnet.title,
                "name": magnet.name,
                "magnet_link": magnet.magnet_link,
                "status": magnet.status,
                "timestamp": magnet.timestamp
            } for magnet in magnets])
        else:
            return jsonify({"message": "No magnets found for the given RSS feed"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    
@magnet_blueprint.route('/magnets/queue/start', methods=['POST'])
async def start_magnet_queue():
    """
    启动任务队列处理。
    """
    magnet_queue_manager = current_app.config['MAGNET_QUEUE_MANAGER']

    # 从数据库中获取未完成的任务
    pending_magnets = await magnet_service.get_pending_magnets()
    await magnet_queue_manager.add_magnets_to_queue(pending_magnets)

    # 逐个处理队列中的任务
    try:
        # 如果没有正在进行的任务，尝试处理任务
        if not magnet_queue_manager.self.current_magnet:
            await magnet_queue_manager.process_magnet_queue()
        return jsonify({"message": "所有任务已处理完毕"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500