import unittest
import json
from io import BytesIO

from werkzeug.security import generate_password_hash

from biaoqingbao import db, Image, Tag, User
from tests import test_app, create_login_client


class TestShowTags(unittest.TestCase):
    url = '/api/tags/'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email='1@foo.com',
                password=generate_password_hash('password1'),
            )
            img = Image(
                data=b'abcdefggggggg',
                type='jpeg',
                tags=[Tag(text='aTag', user=user), Tag(text='bTag', user=user)],
            )
            user.images = [img]
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()
    
    def test_show_all(self):
        client = create_login_client(user_id=1)
        resp = client.get(
            self.url,
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)

    def test_show_image_tags(self):
        client = create_login_client(user_id=1)
        resp = client.get(
            self.url,
            query_string={'image_id': 1}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)


class TestAddTags(unittest.TestCase):
    url = '/api/tags/add'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email='1@foo.com',
                password=generate_password_hash('password1'),
            )
            img = Image(
                data=b'abcdefggggggg',
                type='jpeg',
            )
            user.images = [img]
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_default(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                'image_id': 1,
                'text': 'addedTag1'
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('id', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            tag = Tag.query.get(json_data['id'])
            self.assertIsNotNone(tag)
            self.assertEqual(tag.text, 'addedTag1')
    
    def test_tag_other_users_image(self):
        # setup
        with test_app.app_context():
            user = User(
                email='2@foo.com',
                password=generate_password_hash('password2'),
            )
            db.session.add(user)
            db.session.commit()
        
        # test
        client = create_login_client(user_id=2)
        resp = client.post(self.url, json={
            'image_id': 1,
            'text': 'addedTag1'
        })
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn('error', json_data)


class TestDeleteTag(unittest.TestCase):
    url = '/api/tags/delete'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email='1@foo.com',
                password=generate_password_hash('password1'),
            )
            img = Image(
                data=b'abcdefggggggg',
                type='jpeg',
                tags=[Tag(text='aTag', user=user)],
            )
            user.images = [img]
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                'id': 1,
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证数据库中已删除
        with test_app.app_context():
            tag = Tag.query.get(1)
            self.assertIs(tag, None)
    
    def test_delete_other_users_tag(self):
        # setup
        with test_app.app_context():
            user = User(
                email='2@foo.com',
                password=generate_password_hash('password2'),
            )
            db.session.add(user)
            db.session.commit()
        
        # test
        client = create_login_client(user_id=2)
        resp = client.post(
            self.url,
            json={
                'id': 1,
            }
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn('error', json_data)


class TestUpdateTag(unittest.TestCase):
    url = '/api/tags/update'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email='1@foo.com',
                password=generate_password_hash('password1'),
            )
            img = Image(
                data=b'abcdefggggggg',
                type='jpeg',
                tags=[Tag(text='aTag', user=user)],
            )
            user.images = [img]
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                'id': 1,
                'text': 'updatedTag'
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证数据库中已修改
        with test_app.app_context():
            tag = Tag.query.get(1)
            self.assertEqual(tag.text, 'updatedTag')
    
    def test_update_other_users_tag(self):
        # setup
        with test_app.app_context():
            user = User(
                email='2@foo.com',
                password=generate_password_hash('password2'),
            )
            db.session.add(user)
            db.session.commit()
        
        # test
        client = create_login_client(user_id=2)
        resp = client.post(
            self.url,
            json={
                'id': 1,
                'text': 'updatedTag'
            }
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn('error', json_data)