from smtplib import SMTPException
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import User, Passcode, ResetAttempt
from ..utils import generate_passcode
from ..service import send_email

bp_user = Blueprint('bp_user', __name__)


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


def get_legal_passcodes(user_id):
    expire_datetime = datetime.now() - timedelta(0, 600) # 10 分钟
    return Passcode.query\
        .filter_by(user_id=user_id)\
        .filter(Passcode.create_at > expire_datetime)\
        .all()


"""
POST {
    "email": [String]
}
resp:
- 200, { "msg": "验证码已发送至电子邮箱" }
- 403, { "error": "发送验证码过于频繁" }
- 500, { "error": "发送邮件失败" }
"""
@bp_user.route('/api/send-passcode', methods=['POST'])
def handle_send_passcode():
    data = request.get_json()
    email = data['email']
    user = User.query.filter_by(email=email).first()
    if not user:
        # TODO：发送邮件通知有人输入此邮箱。http://www.ruanyifeng.com/blog/2019/02/password.html
        return jsonify({
            'msg': '验证码已发送至电子邮箱',
        }), 200

    legal_codes = get_legal_passcodes(user.id)
    if len(legal_codes) >= 5:
        return jsonify({
            'error': '已发送过多验证码',
        }), 403

    passcode = generate_passcode()
    record = Passcode(content=passcode, user_id=user.id)
    db.session.add(record)
    db.session.commit()

    try:
        send_email(email, '重设您的“表情宝”账号密码', f'你此次重置密码的验证码为：{passcode}，请在 10 分钟内输入验证码进行下一步操作。 如非你本人操作，请忽略此邮件。')
    except SMTPException as e:
        return jsonify({
            'error': '发送邮件失败'
        }), 500

    return jsonify({
        'msg': '验证码已发送至电子邮箱'
    })


"""
POST {
    "email": [String],
    "passcode": [String],
    "password": [String]
}
resp:
- 200, { "msg": "重置密码成功" }
- 404, { "error": "用户不存在" }
- 403, { "error": "重置尝试次数过于频繁" }
- 403, { "error": "验证码错误" }
"""
@bp_user.route('/api/reset-password', methods=['POST'])
def handle_reset_password():
    data = request.get_json()
    email = data['email']
    passcode = data['passcode']
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            'error': '用户不存在',
        }), 404

    expire_datetime = datetime.now() - timedelta(0, 600) # 10 分钟
    attempts = ResetAttempt.query\
        .filter_by(user_id=user.id)\
        .filter(ResetAttempt.create_at > expire_datetime)\
        .all()
    if len(attempts) >= 5:
        return jsonify({
            'error': ''
        }), 403

    a = ResetAttempt(user_id=user.id)
    db.session.add(a)
    legal_codes = get_legal_passcodes(user.id)
    if passcode in [r.content for r in legal_codes]:
        user.password = generate_password_hash(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'msg': '重置密码成功'
        })
    else:
        return jsonify({
            'error': '验证码错误'
        }), 403
