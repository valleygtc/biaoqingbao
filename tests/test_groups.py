import unittest

from werkzeug.security import generate_password_hash

from biaoqingbao import Group, Image, Tag, User, db
from tests import create_login_client, test_app


class TestShowGroups(unittest.TestCase):
    url = "/api/groups/"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            group1 = Group(
                name=f"testGroup1",
            )
            group2 = Group(
                name=f"testGroup1",
            )
            group3 = Group(
                name=f"testGroup1",
            )
            user.groups = [group1, group2, group3]
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)
        self.assertEqual(len(json_data["data"]), 3)


class TestAddGroup(unittest.TestCase):
    url = "/api/groups/add"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.post(self.url, json={"name": "addedGroup"})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("id", json_data)
        # 验证已插入数据库
        with test_app.app_context():
            self.assertTrue(Group.query.get(1))


class TestDeleteGroup(unittest.TestCase):
    url = "/api/groups/delete"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            group = Group(
                name=f"testGroup",
            )
            user.groups.append(group)
            img1 = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="aTag", user=user)],
                user=user,
            )
            img2 = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="bTag", user=user)],
                user=user,
            )
            group.images = [img1, img2]
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.post(self.url, json={"ids": [1]})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("msg", json_data)
        # 验证数据库中已删除
        with test_app.app_context():
            self.assertFalse(Group.query.get(1))
            # 验证 cascade delete：
            self.assertFalse(Image.query.get(1))
            self.assertFalse(Image.query.get(2))

    def test_delete_not_exists_group(self):
        client = create_login_client()
        resp = client.post(self.url, json={"ids": [10000]})
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_delete_other_users_group(self):
        # setup
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password2"),
            )
            db.session.add(user)
            db.session.commit()

        # test
        client = create_login_client(user_id=2)
        resp = client.post(self.url, json={"ids": [1]})
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)


class TestUpdateGroup(unittest.TestCase):
    url = "/api/groups/update"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            group1 = Group(
                name=f"testGroup1",
            )
            user.groups = [group1]
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
                "id": 1,
                "name": "updatedGroup",
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("msg", json_data)
        # 验证数据库中确实已经更新
        with test_app.app_context():
            record = Group.query.get(1)
            self.assertEqual(record.name, "updatedGroup")

    def test_rename_others_group(self):
        # setup
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password2"),
            )
            db.session.add(user)
            db.session.commit()

        # test
        client = create_login_client(user_id=2)
        resp = client.post(
            self.url,
            json={
                "id": 1,
                "name": "updatedGroup",
            },
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)
