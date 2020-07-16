import unittest
from pathlib import Path

from click.testing import CliRunner

from biaoqingbao import cli
from biaoqingbao import __version__


class TestGeneralOptions(unittest.TestCase):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(__version__, result.output)
