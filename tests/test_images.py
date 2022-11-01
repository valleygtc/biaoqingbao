import json
import unittest
from io import BytesIO

from werkzeug.security import generate_password_hash

from biaoqingbao import Group, Image, Tag, User, db
from tests import create_login_client, test_app


class TestShowImageList(unittest.TestCase):
    url = "/api/images/"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            for _ in range(20):
                img = Image(
                    data=b"fake binary data",
                    type="jpeg",
                    tags=[Tag(text="aTag", user=user), Tag(text="bTag", user=user)],
                )
                user.images.append(img)
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_default(self):
        client = create_login_client(user_id=1)
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)

    def test_pagination(self):
        client = create_login_client(user_id=1)
        resp = client.get(
            self.url,
            query_string={
                "page": 2,
                "per_page": 10,
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)
        self.assertIn("pagination", json_data)
        self.assertEqual(len(json_data["data"]), 10)


class TestSearchImage(unittest.TestCase):
    url = "/api/images/"

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

            img3 = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="cTag", user=user)],
                user=user,
            )
            db.session.add(img3)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_search_tag(self):
        client = create_login_client(user_id=1)
        resp = client.get(self.url, query_string={"tag": "aTag"})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)
        self.assertEqual(len(json_data["data"]), 1)

    def test_search_part_tag(self):
        client = create_login_client(user_id=1)
        resp = client.get(self.url, query_string={"tag": "aT"})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)
        self.assertEqual(len(json_data["data"]), 1)

    def test_search_group(self):
        client = create_login_client(user_id=1)
        resp = client.get(self.url, query_string={"groupId": 1})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)
        self.assertEqual(len(json_data["data"]), 2)

    def test_search_tag_within_group(self):
        client = create_login_client(user_id=1)
        resp = client.get(
            self.url,
            query_string={
                "groupId": 1,
                "tag": "aTag",
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("data", json_data)
        self.assertEqual(len(json_data["data"]), 1)


class TestShowImage(unittest.TestCase):
    url = "/api/images/{id}"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            img = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="aTag", user=user)],
            )
            user.images.append(img)
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.get(
            self.url.format(id=1),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "image/jpeg")
        self.assertEqual(resp.headers.get("Content-Type"), "image/jpeg")

    def test_fetch_other_users_image(self):
        client = create_login_client(user_id=2)
        resp = client.get(
            self.url.format(id=1),
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)


class TestAddImage(unittest.TestCase):
    url = "/api/images/add"

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
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_blank_tags(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            data={
                "image": (BytesIO(b"added image data"), "test_image.jpeg"),
                "metadata": json.dumps(
                    {
                        "type": "jpeg",
                        "tags": [],
                    }
                ),
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("id", json_data)
        # 验证已插入数据库
        with test_app.app_context():
            record = Image.query.get(1)
            self.assertTrue(record)
            self.assertEqual(record.tags, [])

    def test_with_tags(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            data={
                "image": (BytesIO(b"added image data"), "test_image.jpeg"),
                "metadata": json.dumps(
                    {
                        "type": "jpeg",
                        "tags": ["aTag", "bTag"],
                    }
                ),
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("id", json_data)
        # 验证已插入数据库
        with test_app.app_context():
            self.assertTrue(Image.query.get(1))

    def test_add_to_group(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            data={
                "image": (BytesIO(b"added image data"), "test_image.jpeg"),
                "metadata": json.dumps(
                    {
                        "type": "jpeg",
                        "tags": ["aTag", "bTag"],
                        "group_id": 1,
                    }
                ),
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("id", json_data)
        # 验证已插入数据库
        with test_app.app_context():
            image = Image.query.get(1)
            self.assertTrue(image)
            self.assertEqual(image.group_id, 1)

    def test_add_to_not_exists_group(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            data={
                "image": (BytesIO(b"added image data"), "test_image.jpeg"),
                "metadata": json.dumps(
                    {
                        "type": "jpeg",
                        "tags": ["aTag", "bTag"],
                        "group_id": 1000,
                    }
                ),
            },
        )
        self.assertEqual(resp.status_code, 400)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_add_to_other_users_group(self):
        # setup
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password1"),
            )
            db.session.add(user)
            db.session.commit()

        # test
        client = create_login_client(user_id=2)
        resp = client.post(
            self.url,
            data={
                "image": (BytesIO(b"added image data"), "test_image.jpeg"),
                "metadata": json.dumps(
                    {
                        "type": "jpeg",
                        "tags": ["aTag", "bTag"],
                        "group_id": 1,
                    }
                ),
            },
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)


class TestDeleteImage(unittest.TestCase):
    url = "/api/images/delete"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            img = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="aTag", user=user)],
            )
            user.images.append(img)
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        client = create_login_client(user_id=1)
        resp = client.post(self.url, json={"id": 1})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("msg", json_data)
        # 验证数据库中已删除
        with test_app.app_context():
            self.assertFalse(Image.query.get(1))

    def test_delete_not_exists_image(self):
        client = create_login_client(user_id=1)
        resp = client.post(self.url, json={"id": 10000})
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_delete_other_users_image(self):
        # setup
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password1"),
            )
            db.session.add(user)
            db.session.commit()

        client = create_login_client(user_id=2)
        resp = client.post(self.url, json={"id": 1})
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)


class TestUpdateImage(unittest.TestCase):
    url = "/api/images/update"

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
            group.images = [img1]
            db.session.add(user)
            db.session.commit()

            img2 = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="cTag", user=user)],
                user=user,
            )
            db.session.add(img2)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_move_image_from_all_to_group(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                "id": 2,
                "group_id": 1,
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("msg", json_data)
        with test_app.app_context():
            self.assertEqual(
                Image.query.get(2).group_id,
                1,
            )

    def test_move_not_exist_image(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                "id": 1000,
                "group_id": 1,
            },
        )
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_move_to_not_exists_group(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                "id": 2,
                "group_id": 1000,
            },
        )
        self.assertEqual(resp.status_code, 404)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_move_image_to_other_users_group(self):
        # setup
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password2"),
            )
            img = Image(
                data=b"fake binary data",
                type="jpeg",
                tags=[Tag(text="aTag", user=user)],
                user=user,
            )
            db.session.add(user)
            db.session.commit()

        # test
        client = create_login_client(user_id=2)
        resp = client.post(
            self.url,
            json={
                "id": 3,
                "group_id": 1,
            },
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_move_other_users_image_to_my_group(self):
        # setup
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password2"),
            )
            group = Group(
                name=f"testGroup",
            )
            user.groups.append(group)
            db.session.add(user)
            db.session.commit()

        # test
        client = create_login_client(user_id=2)
        resp = client.post(
            self.url,
            json={
                "id": 1,
                "group_id": 2,
            },
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("error", json_data)

    def test_move_image_from_group_to_all(self):
        client = create_login_client(user_id=1)
        resp = client.post(
            self.url,
            json={
                "id": 1,
                "group_id": None,
            },
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("msg", json_data)
        with test_app.app_context():
            self.assertIs(
                Image.query.get(1).group_id,
                None,
            )


class TestExportImages(unittest.TestCase):
    url = "/api/images/export"

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            for _ in range(10):
                img = Image(
                    data=b"fake binary data",
                    type="jpeg",
                    tags=[Tag(text="aTag", user=user), Tag(text="bTag", user=user)],
                )
                user.images.append(img)

            group = Group(
                name=f"testGroup",
                user=user,
            )
            for _ in range(5):
                img = Image(
                    data=b"fake binary data",
                    type="jpeg",
                    user=user,
                    group=group,
                    tags=[Tag(text="aTag", user=user), Tag(text="bTag", user=user)],
                )
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_export_all(self):
        client = create_login_client()
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_export_group(self):
        client = create_login_client()
        resp = client.get(
            self.url,
            query_string={
                "group_id": 1,
            },
        )
        self.assertEqual(resp.status_code, 200)
