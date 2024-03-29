import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from biaoqingbao import Passcode, ResetAttempt, User, db
from tests import create_login_client, get_cookies, test_app


def fake_records(n):
    for i in range(1, n + 1):
        user = User(
            email=f"{i}@foo.com",
            password=generate_password_hash(f"password{i}"),
        )
        db.session.add(user)
    db.session.commit()


class TestRegister(unittest.TestCase):
    url = "/api/register"

    data = {
        "email": "newuser@foo.com",
        "password": "foopassword",
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
        self.assertIn("msg", json_data)
        # 验证已插入数据库
        with test_app.app_context():
            self.assertTrue(User.query.get(2))

    def test_email_already_exists(self):
        client = test_app.test_client()
        body = self.data.copy()
        body["email"] = "1@foo.com"
        resp = client.post(self.url, json=body)
        self.assertEqual(resp.status_code, 409)
        json_data = resp.get_json()
        self.assertIn("error", json_data)


class TestLogin(unittest.TestCase):
    url = "/api/login"

    data = {
        "email": "1@foo.com",
        "password": "password1",
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
            self.assertIn("msg", json_data)
            cookies = get_cookies(client)
            self.assertIn("token", cookies)

    def test_user_not_exists(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body["email"] = "not_exit_email@foo.com"
            resp = client.post(
                self.url,
                json=body,
            )
            self.assertEqual(resp.status_code, 401)
            json_data = resp.get_json()
            self.assertIn("error", json_data)
            cookies = get_cookies(client)
            self.assertNotIn("token", cookies)

    def test_password_wrong(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body["password"] = "wrongpassword"
            resp = client.post(
                self.url,
                json=body,
            )
            self.assertEqual(resp.status_code, 401)
            json_data = resp.get_json()
            self.assertIn("error", json_data)
            cookies = get_cookies(client)
            self.assertNotIn("token", cookies)


class TestLogout(unittest.TestCase):
    url = "/api/logout"

    data = {
        "email": "1@foo.com",
        "password": "password1",
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
            self.assertIn("msg", json_data)
            cookies = get_cookies(client)
            self.assertTrue("token" not in cookies or cookies["token"].is_expired())


class TestSendPasscode(unittest.TestCase):
    url = "/api/send-passcode"

    data = {
        "email": "1@foo.com",
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            fake_records(1)

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        with test_app.test_client() as client:
            with patch("biaoqingbao.views.user.send_email") as mock_send_email:
                resp = client.post(self.url, json=self.data)
                mock_send_email.assert_called_once()

            self.assertEqual(resp.status_code, 200)
            json_data = resp.get_json()
            self.assertIn("msg", json_data)

    def test_user_not_exists(self):
        with test_app.test_client() as client:
            resp = client.post(self.url, json={"email": "xxxx@foo.com"})
            self.assertEqual(resp.status_code, 200)
            json_data = resp.get_json()
            self.assertIn("msg", json_data)

    def test_send_passcode_too_frequently(self):
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password2"),
            )
            user.passcodes = [
                Passcode(content="1234"),
                Passcode(content="2234"),
                Passcode(content="3234"),
                Passcode(content="4234"),
                Passcode(content="5234"),
            ]
            db.session.add(user)
            db.session.commit()
        with test_app.test_client() as client:
            with patch("biaoqingbao.views.user.send_email") as mock_send_email:
                resp = client.post(self.url, json={"email": "2@foo.com"})
                mock_send_email.assert_not_called()

            self.assertEqual(resp.status_code, 403)
            json_data = resp.get_json()
            self.assertIn("error", json_data)


class TestResetPassword(unittest.TestCase):
    url = "/api/reset-password"

    data = {
        "email": "1@foo.com",
        "passcode": "1234",
        "password": "newpassword1",
    }

    def setUp(self):
        with test_app.app_context():
            db.create_all()
            user = User(
                email="1@foo.com",
                password=generate_password_hash("password1"),
            )
            normal_passcode = Passcode(content="1234")
            expired_passcode = Passcode(
                content="2234", create_at=datetime.now() - timedelta(0, 601)
            )
            user.passcodes = [normal_passcode, expired_passcode]
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with test_app.app_context():
            db.drop_all()

    def test_normal(self):
        with test_app.test_client() as client:
            resp = client.post(self.url, json=self.data)
            self.assertEqual(resp.status_code, 200)
            json_data = resp.get_json()
            self.assertIn("msg", json_data)

        with test_app.app_context():
            self.assertTrue(
                check_password_hash(
                    User.query.get(1).password,
                    self.data["password"],
                )
            )

    def test_user_not_found(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body["email"] = "xxx@foo.com"
            resp = client.post(self.url, json=body)
            self.assertEqual(resp.status_code, 404)
            json_data = resp.get_json()
            self.assertIn("error", json_data)

    def test_passcode_not_found(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body["passcode"] = "1235"
            resp = client.post(self.url, json=body)
            self.assertEqual(resp.status_code, 403)
            json_data = resp.get_json()
            self.assertIn("error", json_data)

    def test_passcode_expire(self):
        with test_app.test_client() as client:
            body = self.data.copy()
            body["passcode"] = "2234"
            resp = client.post(self.url, json=body)
            self.assertEqual(resp.status_code, 403)
            json_data = resp.get_json()
            self.assertIn("error", json_data)

    def test_reset_too_frequently(self):
        with test_app.app_context():
            user = User(
                email="2@foo.com",
                password=generate_password_hash("password2"),
            )
            user.reset_attempts = [
                ResetAttempt(),
                ResetAttempt(),
                ResetAttempt(),
                ResetAttempt(),
                ResetAttempt(),
            ]
            db.session.add(user)
            db.session.commit()
        with test_app.test_client() as client:
            body = self.data.copy()
            body["email"] = "2@foo.com"
            resp = client.post(self.url, json=body)
            self.assertEqual(resp.status_code, 403)
            json_data = resp.get_json()
            self.assertIn("error", json_data)
