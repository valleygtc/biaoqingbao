import unittest
import json

from biaoqingbao import db, Image, Group, Tag
from tests import test_app


def fake_records(n):
    for i in range(1, n + 1):
        group = Group(
            name=f'testGroup{i}',
        )
        img1 = Image(
            data=b'abcdefggggggg',
            type='jpeg',
            tags=[Tag(text='aTag'), Tag(text='bTag')]
        )
        img2 = Image(
            data=b'abcdefggggggg',
            type='jpeg',
            tags=[Tag(text='aTag'), Tag(text='bTag')]
        )
        group.images = [img1, img2]
        db.session.add(group)
    db.session.commit()


class TestShowGroups(unittest.TestCase):
    url = '/api/groups/'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_records(3)
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = test_app.test_client()
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)


class TestAddGroup(unittest.TestCase):
    url = '/api/groups/add'

    data = {
        'name': 'addedGroup'
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = test_app.test_client()
        body = self.data.copy()
        resp = client.post(
            self.url,
            json=body
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('id', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            self.assertTrue(Group.query.get(1))


class TestDeleteGroup(unittest.TestCase):
    url = '/api/groups/delete'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_records(2)
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = test_app.test_client()
        resp = client.post(
            self.url,
            json={'ids': [1, 2]}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证数据库中已删除
        with test_app.app_context():
            self.assertFalse(Group.query.get(1))
            # 验证 cascade delete：
            self.assertFalse(Image.query.get(1))
            self.assertFalse(Image.query.get(2))
            self.assertFalse(Group.query.get(2))
            # 验证 cascade delete：
            self.assertFalse(Image.query.get(3))
            self.assertFalse(Image.query.get(4))
    
    def test_delete_not_exists_group(self):
        client = test_app.test_client()
        resp = client.post(
            self.url,
            json={'ids': [10000]}
        )
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn('error', json_data)


class TestUpdateGroup(unittest.TestCase):
    url = '/api/groups/update'

    data = {
        'id': 1,
        'name': 'updatedGroup',
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
        body = self.data.copy()
        resp = client.post(
            self.url,
            json=body
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证数据库中确实已经更新
        with test_app.app_context():
            record = Group.query.get(1)
            self.assertEqual(record.name, body['name'])
