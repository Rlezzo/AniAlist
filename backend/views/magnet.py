from sqlalchemy.exc import SQLAlchemyError
from backend.services import magnet_service
from flask import Blueprint, request, jsonify
from backend.utils.logging_config import loguru_logger as logger
from backend.utils.dependency_manager import dependency_manager, DependencyKeys

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
        logger.error(f"获得全部 magnet 错误: {str(e)}")
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
        logger.error(f"通过 ID 获得 magnet 错误，未找到 magnet {magnet_id}")
        return jsonify({"error": "magnet not found"}), 404
    except SQLAlchemyError as e:
        logger.error("通过 ID 获得 magnet 错误")
        return jsonify({"error": str(e)}), 500

# 创建 magnet
@magnet_blueprint.route('/magnets', methods=['POST'])
async def create_magnet():
    data = request.json
    try:
        await magnet_service.create_magnet(data)
        return jsonify({"message": "magnet created successfully!"}), 201
    except SQLAlchemyError as e:
        logger.error(f"创建 magnet 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 修改 magnet
@magnet_blueprint.route('/magnets/<int:magnet_id>', methods=['PUT'])
async def update_magnet(magnet_id):
    data = request.json
    try:
        updated = await magnet_service.update_magnet(magnet_id, data)
        if updated:
            return jsonify({"message": "magnet updated successfully!"})
        logger.error(f"通过 ID 修改 magnet 错误，未找到 magnet {magnet_id}")
        return jsonify({"error": "magnet not found"}), 404
    except SQLAlchemyError as e:
        logger.error(f"通过 ID 获得 magnet 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 删除 magnet
@magnet_blueprint.route('/magnets/<int:magnet_id>', methods=['DELETE'])
async def delete_magnet(magnet_id):
    try:
        deleted = await magnet_service.delete_magnet(magnet_id)
        if deleted:
            return jsonify({"message": "magnet deleted successfully!"})
        logger.error(f"通过 ID 删除 magnet 错误，未找到 magnet {magnet_id}")
        return jsonify({"error": "magnet not found"}), 404
    except SQLAlchemyError as e:
        logger.error(f"通过 ID 删除 magnet 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 重试
@magnet_blueprint.route('/magnets/<int:magnet_id>/retry', methods=['POST'])
async def retry_magnet(magnet_id):
    """
    重试下载任务，直接接受一个任务对象。
    """
    try:
        magnet = await magnet_service.get_magnet_by_id(magnet_id)
        if not magnet:
            logger.error(f"通过 ID 重试 magnet 错误，未找到 magnet {magnet_id}")
            return jsonify({"error": f"Magnet with id {magnet_id} not found"}), 404

        update_success = await magnet_service.update_magnet(magnet_id, {'status': False})
        if not update_success:
            logger.error(f"通过 ID 重试 magnet 错误，无法修改 magnet {magnet_id} 完成状态")
            return jsonify({"error": "Failed to update magnet status"}), 500
        
    except SQLAlchemyError as e:
        logger.error(f"通过 ID 重试 magnet 错误，Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    # 上面改成接受id，然后顺便把status改成未完成
    magnet_queue_manager = dependency_manager.get(DependencyKeys.MAGNET_QUEUE_MANAGER)
    try:
        await magnet_queue_manager.interrupt_and_retry_task(magnet)
        return jsonify({"message": "任务重试成功"}), 200
    except Exception as e:
        logger.error(f"通过 ID 重试 magnet 错误: {str(e)}")
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
            logger.error(f"通过 magnet 获得 rssID 错误: No magnets found for the given RSS feed")
            return jsonify({"message": "No magnets found for the given RSS feed"}), 404
    except SQLAlchemyError as e:
        logger.error(f"通过 magnet 获得 rssID 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@magnet_blueprint.route('/magnets/queue/start', methods=['POST'])
async def start_magnet_queue():
    """
    启动任务队列处理。
    """
    magnet_queue_manager = dependency_manager.get(DependencyKeys.MAGNET_QUEUE_MANAGER)

    # 从数据库中获取未完成的任务
    pending_magnets = await magnet_service.get_pending_magnets()
    await magnet_queue_manager.add_magnets_to_queue(pending_magnets)

    # 逐个处理队列中的任务
    try:
        # 如果没有正在进行的任务，尝试处理任务
        if not magnet_queue_manager.current_magnet:
            await magnet_queue_manager.process_magnet_queue()
            return jsonify({"message": f"开始任务处理，当前任务为 {magnet_queue_manager.current_magnet.name}"}), 200
        else:
            return jsonify({"message": f"任务队列进行中！当前任务为 {magnet_queue_manager.current_magnet.name}"}), 200
    except Exception as e:
        logger.error(f"启动任务队列错误: {str(e)}")
        return jsonify({"error": str(e)}), 500