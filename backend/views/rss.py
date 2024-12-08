from flask import Blueprint, current_app, request, jsonify
from backend.services import rss_service 

rss_blueprint = Blueprint('rss', __name__)

# 查询
@rss_blueprint.route('/rss', methods=['GET'])
async def get_all_rss_feeds():
    """
    获得全部RSS订阅数据
    """
    feeds = await rss_service.get_all_rss_feeds()
    if feeds is None:
        return jsonify({"error": "Failed to fetch RSS feeds"}), 500

    return jsonify([{
        "id": feed.id,
        "name": feed.name,
        "url": feed.url,
        "last_updated": feed.last_updated,
        "should_update": feed.should_update
    } for feed in feeds])

@rss_blueprint.route('/rss/<int:rss_id>', methods=['GET'])
async def get_rss_feed_by_id(rss_id):
    """
    根据 rss_id 获取特定的 RSS 订阅数据
    """
    feed = await rss_service.get_rss_feed_by_id(rss_id)
    if feed is None:
        return jsonify({"error": "RSS feed not found"}), 404

    return jsonify({
        "id": feed.id,
        "name": feed.name,
        "url": feed.url,
        "last_updated": feed.last_updated,
        "should_update": feed.should_update
    })

# 添加rss
@rss_blueprint.route('/rss', methods=['POST'])
async def create_rss_feed():
    """
    添加rss订阅
    """
    data = request.json
    if 'name' not in data or 'url' not in data:
        return jsonify({"error": "Missing 'name' or 'url' in request data"}), 400

    # 使用服务层函数来创建 RSS 订阅
    new_feed = await rss_service.create_rss_feed(data['name'], data['url'])
    
    if new_feed is None:
        return jsonify({"error": "Failed to create RSS feed"}), 500

    return jsonify({"message": "RSS feed created successfully!", "feed_id": new_feed.id}), 201

# 修改

@rss_blueprint.route('/rss/<int:rss_id>', methods=['PUT'])
async def update_rss_feed(rss_id):
    """
    修改rss数据
    """
    data = request.json
    success, error = await rss_service.update_rss_feed(rss_id, data)

    if success:
        return jsonify({"message": "RSS feed updated successfully!"})
    elif error == "RSS feed not found":
        return jsonify({"error": error}), 404
    else:
        return jsonify({"error": error}), 500

@rss_blueprint.route('/rss/<int:rss_id>', methods=['PATCH'])
async def patch_rss_feed(rss_id):
    """
    通用 PATCH 方法，用于更新 RSS 源的部分字段。
    """
    data = request.json

    # 定义允许更新的字段，避免不安全的字段更新
    allowed_keys = {'name', 'url', 'should_update'}

    # 过滤出被允许更新的字段
    update_data = {key: value for key, value in data.items() if key in allowed_keys}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    # 使用通用的 patch 方法更新字段
    success = await rss_service.patch_rss_feed(rss_id, update_data)

    if not success:
        return jsonify({"error": "Failed to update RSS feed"}), 404

    return jsonify({"message": "RSS feed updated successfully."})

@rss_blueprint.route('/rss/<int:rss_id>/rename', methods=['PATCH'])
async def rename_rss_feed(rss_id):
    """
    更新 RSS 名称并同时更新网盘文件夹名称。
    """
    data = request.json

    # 获取旧的和新的 RSS 名称
    old_name = data.get('old_name')
    new_name = data.get('new_name')

    if not old_name or not new_name:
        return jsonify({"error": "Missing old_name or new_name"}), 400

    if old_name == new_name:
        return jsonify({"message": "Old name and new name are the same, no changes needed."}), 200

    # 使用 Alist API 更新文件夹名称
    directory_manager = current_app.config['DIRECTORY_MANAGER']
    root_save_path = current_app.config['ROOT_SAVE_PATH']
    try:
        success = await directory_manager.rename_directory(f"{root_save_path}/{old_name}", new_name)
        if not success:
            return jsonify({"error": "Failed to rename folder on cloud storage"}), 500
    except Exception as e:
        return jsonify({"error": f"Error while renaming folder: {str(e)}"}), 500

    # 更新数据库中的 RSS 名称
    success = await rss_service.patch_rss_feed(rss_id, {"name": new_name})

    if not success:
        return jsonify({"error": "Failed to update RSS feed in database"}), 404

    return jsonify({"message": "RSS feed and folder name updated successfully."})

# 根据id删除rss
@rss_blueprint.route('/rss/<int:rss_id>', methods=['DELETE'])
async def delete_rss_feed(rss_id):
    response, status_code = await rss_service.delete_rss_feed(rss_id)
    return jsonify(response), status_code

# 刷新全部 RSS 订阅
@rss_blueprint.route('/rss/refresh', methods=['POST'])
async def refresh_all_rss_feeds():
    """
    刷新全部打勾的 RSS 订阅
    """
    success, message = await rss_service.refresh_all_rss_feeds()
    if not success:
        return jsonify({"error": message}), 500
    return jsonify({"message": message})
        
# 刷新指定的 RSS 订阅
@rss_blueprint.route('/rss/<int:rss_id>/refresh', methods=['POST'])
async def refresh_rss_feed(rss_id):
    """
    刷新指定的 RSS 订阅
    """
    success, message = await rss_service.refresh_rss_feed(rss_id)
    if not success:
        return jsonify({"error": message}), 404 if "not found" in message else 500
    return jsonify({"message": message})
