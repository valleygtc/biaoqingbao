import unittest

from biaoqingbao.service import send_email


class TestShowImageList(unittest.TestCase):
    def test_default(self):
        send_email("gutianci@qq.com", "测试邮件", "test test")
