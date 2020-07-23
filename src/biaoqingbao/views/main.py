import io
import zipfile
from uuid import uuid4

from flask import Blueprint, json, jsonify, request, Response, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import Image, Group, Tag, User

bp_main = Blueprint('bp_main', __name__)


@bp_main.before_request
def handle_authen():
    if not session.get('login') or not session.get('user_id'):
        return jsonify({
            'error': '用户未登录',
        }), 401
    else:
        return


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
@bp_main.route('/api/images/')
def show_images():
    user_id = session['user_id']
    query = Image.query.filter_by(user_id=user_id)

    # apply search
    groupId = request.args.get('groupId')
    tag = request.args.get('tag')
    if groupId and tag:
        query = query\
            .join(Image.group)\
            .join(Image.tags)\
            .filter(Group.id == groupId)\
            .filter(Tag.text.contains(tag))
    elif groupId:
        query = query\
            .join(Image.group)\
            .filter(Group.id == groupId)
    elif tag:
        query = query\
            .join(Image.tags)\
            .filter(Tag.text.contains(tag))

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
@bp_main.route('/api/images/<int:image_id>')
def show_image(image_id):
    image = Image.query.get(image_id)
    if image.user_id != session['user_id']:
        return jsonify({
            'error': '您没有访问此图片的权限'
        }), 403

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
    user_id = session['user_id']
    image_file = request.files['image']
    image_data = image_file.read()
    image_file.close()
    metadata = json.loads(request.form['metadata'])
    image = Image(
        data=image_data,
        type=metadata['type'],
        tags=[Tag(text=t, user_id=user_id) for t in metadata['tags']],
        user_id=user_id
    )
    group_id = metadata.get('group_id')
    if group_id is not None:
        group = Group.query.get(group_id)
        if group is None:
            return jsonify({
                'error': '所选组不存在。'
            }), 400
        elif group.user_id != user_id:
            return jsonify({
                'error': '您没有添加图片至此组的权限'
            }), 403
        else:
            image.group = group

    db.session.add(image)
    db.session.commit()
    return jsonify({
        'id': image.id,
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
        return jsonify({
            'error': '图片不存在，可能是其已被删除，请刷新页面。',
        }), 404
    elif image.user_id != session['user_id']:
        return jsonify({
            'error': '您没有删除此图片的权限',
        }), 403
    else:
        db.session.delete(image)
        db.session.commit()
        return jsonify({
            'msg': '成功删除图片'
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
        return jsonify({
            'error': '图片不存在，可能是其已被删除，请刷新页面。'
        }), 404

    user_id = session['user_id']    
    if image.user_id != user_id:
        return jsonify({
            'error': '您无移动此图片的权限。',
        }), 403
    
    group_id = data['group_id']
    if group_id is None:
        image.group_id = None
        db.session.commit()
        return jsonify({
            'msg': '成功将图片移至组“全部”。'
        })
    else:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({
                'error': '所选组不存在，可能是其已被删除，请刷新页面。'
            }), 404
        elif group.user_id != user_id:
            return jsonify({
                'error': '您无将图片移至此组的权限。'
            }), 403
        else:
            image.group = group
            db.session.commit()
            return jsonify({
                'msg': f'成功将图片移至组“{group.name}”。'
            })


# tags
"""
GET ?image_id=[int]
resp: 200, body:
{
    "data": [Array[Object]] // {"id": 1, "text": "xxx"}
}
"""
@bp_main.route('/api/tags/')
def show_tags():
    image_id = request.args.get('image_id')
    if image_id:
        image = Image.query.get(image_id)
        if image is None:
            return jsonify({
                'error': '目标图片不存在，可能是其已被删除，请刷新页面。'
            }), 404
        tags = image.tags
    else:
        tags = Tag.query.all()

    resp = {
        'data': [{'id': t.id, 'text': t.text} for t in tags],
    }
    return jsonify(resp)


"""
POST {
    "image_id": [Number],
    "text": [String]
}
resp: 200, body: {"id": [Number]}
"""
@bp_main.route('/api/tags/add', methods=['POST'])
def add_tags():
    data = request.get_json()
    image_id = data['image_id']
    image = Image.query.get(image_id)
    if image is None:
        return jsonify({
            'error': '目标图片不存在，可能是其已被删除，请刷新页面。'
        }), 404
    
    record = Tag(text=data['text'])
    record.image_id=image_id
    db.session.add(record)
    db.session.commit()
    return jsonify({
        'id': record.id,
    })


"""
POST {
    "id": [Number]
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/tags/delete', methods=['POST'])
def delete_tag():
    data = request.get_json()
    tag_id = data['id']
    tag = Tag.query.get(tag_id)
    if tag is None:
        return jsonify({
            'error': '目标标签不存在，可能是其已被删除，请刷新页面。'
        }), 404
    else:
        db.session.delete(tag)
        db.session.commit()
        return jsonify({
            'msg': '成功删除标签'
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
        return jsonify({
            'error': '目标标签不存在，可能是其已被删除，请刷新页面。'
        }), 404
    
    tag.text = data['text']
    db.session.commit()

    return jsonify({
        'msg': '成功将目标标签重命名'
    })


# group
"""
GET
resp: 200, body:
{
    "data": [Array[Object]] // {"id": 1, "name": "xxx"}
}
"""
@bp_main.route('/api/groups/')
def show_groups():
    groups = Group.query.filter_by(user_id=session['user_id']).order_by(Group.create_at).all()
    resp = {
        'data': [{'id': r.id, 'name': r.name} for r in groups],
    }
    return jsonify(resp)


"""
POST {
    "name": [String],
}
resp: 200, body: {"id": [int]}
"""
@bp_main.route('/api/groups/add', methods=['POST'])
def add_group():
    data = request.get_json()
    name = data['name']
    record = Group(name=name, user_id=session['user_id'])
    db.session.add(record)
    db.session.commit()
    return jsonify({
        'id': record.id,
    })


"""
POST {
    "ids": [Array[Number]],
}
resp: 200, body: {"msg": [String]}
"""
@bp_main.route('/api/groups/delete', methods=['POST'])
def delete_group():
    data = request.get_json()
    group_ids = data['ids']
    for id in group_ids:
        group = Group.query.get(id)
        if not group:
            err = f'组（id={id}）不存在，可能是其已被删除，请刷新页面。'
            return jsonify({
                'error': err
            }), 404
        elif group.user_id != session['user_id']:
            err = f'您无删除组（id={id}）的权限。'
            return jsonify({
                'error': err
            }), 403
        else:
            db.session.delete(group)

    db.session.commit()
    return jsonify({
        'msg': f'成功删除组（ids={group_ids}）'
    })


"""
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
    if group.user_id == session['user_id']:
        group.name = name
        db.session.commit()
        return jsonify({
            'msg': '成功重命名组。',
        })
    else:
        return jsonify({
            'error': '您无重命名此组的权限。',
        }), 403


"""
GET
resp: 200, body: serve export.zip file.
"""
@bp_main.route('/api/images/export')
def export_images():
    buffer = io.BytesIO()
    images = Image.query.filter_by(user_id=session['user_id']).all()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as fh:
        for image in images:
            fileinfo = zipfile.ZipInfo(
                filename=f'{uuid4()}.{image.type}',
                date_time=image.create_at.timetuple()[:6],
            )
            fh.writestr(fileinfo, image.data)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, attachment_filename='export.zip')
