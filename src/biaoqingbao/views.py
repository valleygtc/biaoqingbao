from flask import Blueprint, json, jsonify, request, Response

from . import db
from .models import Image, Group, Tag

bp_main = Blueprint('bp_main', __name__)


# images
"""
GET
搜索：后端实现，使用 url 参数，可搜索项：tag。
- tag: [str]
- groupId: [int]
分页：后端实现，使用url参数?page=[int]&per_page=[int]
- page: 可选，默认为 1。
- per_page：可选，默认为 20。

resp: 200, body:
{
    "data": [
        {
            "id": [Number],
            "url": [String],
            "type": [String],
            "tags": [Array[Object]], // {"id": 1, "text": "xxx"}
            "group_id": [Number] or null,
            "create_at": [String]
        },
        ...
    ]
    "pagination": {
        'pages': [Number], # 总页数
        'page': [Number], # 当前页码
        'per_page': [Number], # 每页条数（行数）
        'total': [Number] # 总条数（行数）
    }
}
"""
@bp_main.route('/api/images/', methods=['GET'])
def show_images():
    # apply search
    groupId = request.args.get('groupId')
    tag = request.args.get('tag')
    if groupId and tag:
        query = Image.query\
            .join(Image.group)\
            .join(Image.tags)\
            .filter(Group.id == groupId)\
            .filter(Tag.text.contains(tag))
    elif groupId:
        query = Image.query\
            .join(Image.group)\
            .filter(Group.id == groupId)
    elif tag:
        query = Image.query\
            .join(Image.tags)\
            .filter(Tag.text.contains(tag))
    else:
        query = Image.query

    # apply pagination
    DEFAULT_PER_PAGE = 20
    page = int(request.args.get('page', default=1))
    per_page = int(request.args.get('per_page', default=DEFAULT_PER_PAGE))
    paginate = query.order_by(Image.create_at)\
                    .paginate(page=page, per_page=per_page)
    data = [
        {
            'id': record.id,
            'url': f'/api/images/{record.id}',
            'type': record.type,
            'tags': [{'id': t.id, 'text': t.text} for t in record.tags],
            'group_id': record.group_id,
        }
            for record in paginate.items
    ]
    resp = {
        'data': data,
        'pagination': {
            'pages': paginate.pages,
            'page': paginate.page,
            'per_page': paginate.per_page,
            'total': paginate.total,
        }
    }
    return jsonify(resp)


"""
GET ?id=[int]
resp: 200, content-type: image/<type>
body: 图片二进制数据
"""
@bp_main.route('/api/images/<int:image_id>', methods=['GET'])
def show_image(image_id):
    image = Image.query.get(image_id)
    resp = Response(image.data, mimetype=f'image/{image.type}')
    return resp
        

"""
POST 使用表单提交
Content-Type: multipart/form-data
"image": [bytes-file],
"metadata": [JSON-String] {
    "type": [String],
    "tags": [Array[String]]，
    "group_id" [Optional]: [Number] or null,
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/images/add', methods=['POST'])
def add_image():
    image_file = request.files['image']
    image_data = image_file.read()
    image_file.close()
    metadata = json.loads(request.form['metadata'])
    record = Image(
        data=image_data,
        type=metadata['type'],
        tags=[Tag(text=t) for t in metadata['tags']],
    )
    group_id = metadata.get('group_id')
    if group_id is not None:
        group = Group.query.get(group_id)
        if group is None:
            err = f'组（id={group_id}）不存在。'
            return jsonify({
                'error': err
            }), 400

        record.group = group

    db.session.add(record)
    db.session.commit()
    return jsonify({
        'msg': f'成功添加图片：{record}'
    })


"""
POST {
    "id": [Number]
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/images/delete', methods=['POST'])
def delete_image():
    data = request.get_json()
    image_id = data['id']
    image = Image.query.get(image_id)
    if image is None:
        err = f'图片（id={image_id}）不存在，可能是其已被删除，请刷新页面。'
        return jsonify({
            'error': err
        }), 404
    else:
        db.session.delete(image)
        db.session.commit()
        return jsonify({
            'msg': f'成功删除图片（id={image_id}）'
        })


"""
POST {
    "id": [Number],
    "group_id": [Number] | null
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/images/update', methods=['POST'])
def update_image():
    data = request.get_json()
    image_id = data['id']
    image = Image.query.get(image_id)
    if not image:
        err = f'图片（id={image_id}）不存在，可能是其已被删除，请刷新页面。'
        return jsonify({
            'error': err
        }), 404
    
    group_id = data['group_id']
    if group_id is None:
        image.group_id = None
        db.session.commit()
        return jsonify({
            'msg': f'成功将图片（id={image_id}）移至组“全部”。'
        })
    else:
        group = Group.query.get(group_id)
        if not group:
            err = f'组（id={group_id}）不存在，可能是其已被删除，请刷新页面。'
            return jsonify({
                'error': err
            }), 404

        image.group = group
        db.session.commit()
        return jsonify({
            'msg': f'成功将图片（id={image_id}）移至组“{group.name}”。'
        })


# tags
"""/tags/
GET ?image_id=[int]
resp: 200, body:
{
    "data": [Array[Object]] // {"id": 1, "text": "xxx"}
}
"""
@bp_main.route('/api/tags/', methods=['GET'])
def show_tags():
    image_id = request.args.get('image_id')
    if image_id:
        image = Image.query.get(image_id)
        if image is None:
            err = f'图片（id={image_id}）不存在，可能是其已被删除，请刷新页面。'
            return jsonify({
                'error': err
            }), 404
        tags = image.tags
    else:
        tags = Tag.query.all()

    resp = {
        'data': [{'id': t.id, 'text': t.text} for t in tags],
    }
    return jsonify(resp)


"""/tags/add
POST {
    "image_id": [Number],
    "tags": [Array[String]]
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/tags/add', methods=['POST'])
def add_tags():
    data = request.get_json()
    image_id = data['image_id']
    image = Image.query.get(image_id)
    if image is None:
        err = f'图片（id={image_id}）不存在，可能是其已被删除，请刷新页面。'
        return jsonify({
            'error': err
        }), 404
    
    for t in data['tags']:
        record = Tag(text=t)
        record.image_id=image_id
        db.session.add(record)

    db.session.commit()
    return jsonify({
        'msg': f'成功添加为图片（id={image_id}）添加标签：{data["tags"]}'
    })


"""/tags/delete
POST {
    "id": [Number]
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/tags/delete', methods=['POST'])
def delete_tag():
    data = request.get_json()
    tag_id = data['id']
    tag = Image.query.get(tag_id)
    if tag is None:
        err = f'标签（id={tag_id}）不存在，可能是其已被删除，请刷新页面。'
        return jsonify({
            'error': err
        }), 404
    else:
        db.session.delete(tag)
        db.session.commit()
        return jsonify({
            'msg': f'成功删除标签（id={tag_id}）'
        })


"""
POST {
    "id": [Number],
    "text": [String]
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/tags/update', methods=['POST'])
def update_tag():
    data = request.get_json()
    tag_id = data['id']
    tag = Tag.query.get(tag_id)
    if tag is None:
        err = f'标签（id={tag_id}）不存在，可能是其已被删除，请刷新页面。'
        return jsonify({
            'error': err
        }), 404
    
    tag.text = data['text']
    db.session.commit()

    return jsonify({
        'msg': f'成功将标签（id={tag_id}）重命名为：{data["text"]}'
    })


# group
"""/groups/
GET
resp: 200, body:
{
    "data": [Array[Object]] // {"id": 1, "name": "xxx"}
}
"""
@bp_main.route('/api/groups/', methods=['GET'])
def show_groups():
    groups = Group.query.order_by(Group.name).all()
    resp = {
        'data': [{'id': r.id, 'name': r.name} for r in groups],
    }
    return jsonify(resp)


"""/groups/add
POST {
    "name": [String],
}
resp: 200, body: {"id": [int]}
"""
@bp_main.route('/api/groups/add', methods=['POST'])
def add_group():
    data = request.get_json()
    name = data['name']
    record = Group(name=name)
    db.session.add(record)
    db.session.commit()
    return jsonify({
        'id': record.id,
    })


"""/groups/delete
POST {
    "id": [Number],
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/groups/delete', methods=['POST'])
def delete_group():
    data = request.get_json()
    group_id = data['id']
    group = Group.query.get(group_id)
    if group is None:
        err = f'组（id={group_id}）不存在，可能是其已被删除，请刷新页面。'
        return jsonify({
            'error': err
        }), 404
    else:
        db.session.delete(group)
        db.session.commit()
        return jsonify({
            'msg': f'成功删除组（id={group_id}）'
        })


"""/groups/update
POST {
    "id": [Number],
    "name": [String]
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/groups/update', methods=['POST'])
def update_group():
    data = request.get_json()
    group_id = data['id']
    name = data['name']
    group = Group.query.get(group_id)
    group.name = name
    db.session.commit()
    return jsonify({
        'msg': f'成功更新组：{group}'
    })
