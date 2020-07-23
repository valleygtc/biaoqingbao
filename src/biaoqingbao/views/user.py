import io
import zipfile
from uuid import uuid4

from flask import Blueprint, json, jsonify, request, Response, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import Image, Group, Tag, User

bp_user = Blueprint('bp_user', __name__)


# user
"""
POST {
    "email": [String],
    "password": [String]
}
resp:
- 200, { "msg": "注册成功" }
- 409, { "error": "此邮箱已被使用" }
"""
@bp_user.route('/api/register', methods=['POST'])
def handle_register():
    data = request.get_json()
    u = User.query.filter_by(email=data['email']).first()
    if u:
        return jsonify({
            'error': '此邮箱已被使用',
        }), 409

    user = User(
        email=data['email'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'msg': '注册成功'
    })


"""
POST {
    "email": [String],
    "password": [String]
}
resp:
- if ok: 200, body: {"msg": [String]}
- else: 401 Unauthorized，body: {"error": [String]}
"""
@bp_user.route('/api/login', methods=['POST'])
def handle_login():
    if session.get('login'):
        return jsonify({
            'msg': '用户已登录'
        })
    
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({
            'error': '账号或密码错误',
        }), 401
    
    ok = check_password_hash(user.password, data['password'])
    if ok:
        session['login'] = True
        session['user_id'] = user.id
        return jsonify({
            'msg': '登陆成功'
        })
    else:
        return jsonify({
            'error': '账号或密码错误',
        }), 401


"""
GET
resp:
- if ok: 200, body: {"msg": [String]}
- else: 401 Unauthorized，body: {"error": [String]}
"""
@bp_user.route('/api/logout')
def handle_logout():
    if not session.get('login'):
        return jsonify({
        'error': '用户未登录',
        }), 401

    session.pop('login')
    session.pop('user_id')
    return jsonify({
        'msg': '注销成功'
    })
