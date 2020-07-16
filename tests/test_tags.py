import unittest
import json
from io import BytesIO

from biaoqingbao import db, Image, Tag
from tests import test_app


def fake_image():
    img = Image(
        data=b'abcdefggggggg',
        type='jpeg',
        tags=[Tag(text='aTag'), Tag(text='bTag')],
    )
    db.session.add(img)
    db.session.commit()


class TestShowTags(unittest.TestCase):
    url = '/api/tags/'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_image()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()
    
    def test_show_all(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)

    def test_show_image_tags(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            query_string={'image_id': 1}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)


class TestAddTags(unittest.TestCase):
    url = '/api/tags/add'

    data = {
        'image_id': 1,
        'tags': ['addedTag1', 'addedTag2']
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_image()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_default(self):
        client = test_app.test_client()
        body = self.data.copy()
        resp = client.post(self.url, json=body)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            image = Image.query.get(1)
            tags = (t.text for t in image.tags)
            self.assertIn('addedTag1', tags)
            self.assertIn('addedTag2', tags)


class TestDeleteTag(unittest.TestCase):
    url = '/api/tags/delete'

    data = {
        'id': 1,
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_image()
    
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
        # 验证数据库中已删除
        with test_app.app_context():
            tag = Tag.query.get(1)
            self.assertIs(tag, None)
