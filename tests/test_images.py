import unittest
import json
from io import BytesIO

from biaoqingbao import db, Image, Group, Tag
from tests import test_app


def fake_groups(n):
    for i in range(1, n + 1):
        group = Group(
            name=f'testGroup{i}',
        )
        img1 = Image(
            data=b'fake binary data',
            type='jpeg',
            tags=[Tag(text='aTag'), Tag(text='bTag')]
        )
        img2 = Image(
            data=b'fake binary data',
            type='jpeg',
            tags=[Tag(text='aTag'), Tag(text='bTag')]
        )
        group.images = [img1, img2]
        db.session.add(group)
    db.session.commit()


def fake_images(n):
    for i in range(n):
        img = Image(
            data=b'fake binary data',
            type='jpeg',
            tags=[Tag(text='aTag'), Tag(text='bTag')]
        )
        db.session.add(img)
    db.session.commit()


class TestShowImageList(unittest.TestCase):
    url = '/api/images/'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_images(20)
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_default(self):
        client = test_app.test_client()
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)
    
    def test_pagination(self):
        client = test_app.test_client()
        resp = client.get(self.url, query_string={
            'page': 2,
            'per_page': 10,
        })
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)
        self.assertIn('pagination', json_data)
        self.assertEqual(len(json_data['data']), 10)


class TestShowImage(unittest.TestCase):
    url = '/api/images/{id}'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_images(1)
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_show_one_images_data(self):
        client = test_app.test_client()
        resp = client.get(
            self.url.format(id=1),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'image/jpeg')
        self.assertEqual(resp.headers.get('Content-Type'), 'image/jpeg')


class TestSearchImage(unittest.TestCase):
    url = '/api/images/'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            group = Group(
                name=f'testGroup',
            )
            img1 = Image(
                data=b'fake binary data',
                type='jpeg',
                tags=[Tag(text='aTag')],
            )
            img2 = Image(
                data=b'fake binary data',
                type='jpeg',
                tags=[Tag(text='bTag')],
            )
            group.images = [img1, img2]
            db.session.add(group)
            img3 = Image(
                data=b'fake binary data',
                type='jpeg',
                tags=[Tag(text='cTag')],
            )
            db.session.add(img3)
            db.session.commit()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()
    
    def test_search_tag(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            query_string={'tag': 'aTag'}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)
        self.assertEqual(len(json_data['data']), 1)
    
    def test_search_part_tag(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            query_string={'tag': 'aT'}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)
        self.assertEqual(len(json_data['data']), 1)

    def test_search_group(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            query_string={'group': 'testGroup'}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)
        self.assertEqual(len(json_data['data']), 2)
    
    def test_search_tag_within_group(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            query_string={
                'group': 'testGroup',
                'tag': 'aTag',
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('data', json_data)
        self.assertEqual(len(json_data['data']), 1)


class TestAddImage(unittest.TestCase):
    url = '/api/images/add'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()
    
    def test_blank_tags(self):
        client = test_app.test_client()
        resp = client.post(
            self.url,
            data={
                'image': (BytesIO(b'added image data'), 'test_image.jpeg'),
                'metadata': json.dumps({
                    'type': 'jpeg',
                    'tags': [],
                })
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            record = Image.query.get(1)
            self.assertTrue(record)
            self.assertEqual(record.tags, [])

    def test_with_tags(self):
        client = test_app.test_client()
        resp = client.post(
            self.url,
            data={
                'image': (BytesIO(b'added image data'), 'test_image.jpeg'),
                'metadata': json.dumps({
                    'type': 'jpeg',
                    'tags': ['aTag', 'bTag'],
                })
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            self.assertTrue(Image.query.get(1))
    
    def test_with_group(self):
        # setup
        with test_app.app_context():
            group = Group(
                id=1,
                name='testGroup',
            )
            db.session.add(group)
            db.session.commit()
        
        # test
        client = test_app.test_client()
        resp = client.post(
            self.url,
            data={
                'image': (BytesIO(b'added image data'), 'test_image.jpeg'),
                'metadata': json.dumps({
                    'type': 'jpeg',
                    'tags': ['aTag', 'bTag'],
                    'group_id': 1,
                })
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证已插入数据库
        with test_app.app_context():
            image = Image.query.get(1)
            self.assertTrue(image)
            self.assertEqual(image.group_id, 1)


class TestDeleteImage(unittest.TestCase):
    url = '/api/images/delete'

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_images(1)
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            json={'id': 1}
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        # 验证数据库中已删除
        with test_app.app_context():
            self.assertFalse(Image.query.get(1))
    
    def test_delete_not_exists_image(self):
        client = test_app.test_client()
        resp = client.get(
            self.url,
            json={'id': 10000}
        )
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn('error', json_data)


class TestUpdateImage(unittest.TestCase):
    url = '/api/images/update'

    data = {
        'id': 1,
        'group_id': 1,
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_images(1)
            fake_groups(1)
    
    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_move_to_another_group_normal(self):
        client = test_app.test_client()
        body = self.data.copy()
        resp = client.post(
            self.url,
            json=body
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        with test_app.app_context():
            self.assertEqual(
                Image.query.get(1).group_id,
                1,
            )

    def test_move_to_not_exists_group(self):
        client = test_app.test_client()
        body = self.data.copy()
        body['group_id'] = 10000
        resp = client.post(
            self.url,
            json=body
        )
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn('error', json_data)
    
    def test_move_to_all(self):
        client = test_app.test_client()
        resp = client.post(
            self.url,
            json={
                'id': 2,
                'group_id': None,
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn('msg', json_data)
        with test_app.app_context():
            self.assertIs(
                Image.query.get(2).group_id,
                None,
            )
