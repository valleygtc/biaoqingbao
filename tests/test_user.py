import unittest
import json

from flask import session
from werkzeug.security import generate_password_hash

from biaoqingbao import db, User
from tests import test_app, create_login_client


def fake_records(n):
    for i in range(1, n + 1):
        user = User(
            email=f'{i}@foo.com',
            password=generate_password_hash(f'password{i}'),
        )
        db.session.add(user)
    db.session.commit()


class TestRegister(unittest.TestCase):
    url = '/api/register'

    data = {
        'email': 'newuser@foo.com',
        'password': 'foopassword',
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_records(1)

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = test_app.test_client()
        resp = client.post(
            self.url,
            json=self.data,
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            self.assertTrue(User.query.get(2))

    def test_conflict_email(self):
        client = test_app.test_client()
        body = self.data.copy()
        body['email'] = '1@foo.com'
        resp = client.post(
            self.url,
            json=body
        )
        self.assertEqual(resp.status_code, 409)
        json_data = resp.get_json()
        self.assertIn('error', json_data)


class TestLogin(unittest.TestCase):
    url = '/api/login'

    data = {
        'email': '1@foo.com',
        'password': 'password1',
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_records(1)

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_login_success(self):
        with test_app.test_client() as client:
            resp = client.post(
                self.url,
                json=self.data,
            )
            self.assertEqual(resp.status_code, 200)
            json_data = resp.get_json()
            self.assertIn('msg', json_data)

            self.assertTrue(session['login'])
            self.assertEqual(session['user_id'], 1)

    def test_not_exist_email(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body['email'] = 'not_exit_email@foo.com'
            resp = client.post(
                self.url,
                json=body,
            )
            self.assertEqual(resp.status_code, 401)
            json_data = resp.get_json()
            self.assertIn('error', json_data)

            self.assertFalse(session.get('login'))
            self.assertIsNone(session.get('user_id'))

    def test_password_wrong(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body['password'] = 'wrongpassword'
            resp = client.post(
                self.url,
                json=body,
            )
            self.assertEqual(resp.status_code, 401)
            json_data = resp.get_json()
            self.assertIn('error', json_data)

            self.assertFalse(session.get('login'))
            self.assertIsNone(session.get('user_id'))


class TestLogout(unittest.TestCase):
    url = '/api/logout'

    data = {
        'email': '1@foo.com',
        'password': 'password1',
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_records(1)

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_logout_success(self):
        with create_login_client(user_id=1) as client:
            resp = client.get(self.url)
            self.assertEqual(resp.status_code, 200)
            json_data = resp.get_json()
            self.assertIn('msg', json_data)

            self.assertFalse(session.get('login'))
            self.assertFalse(session.get('user_id'))
