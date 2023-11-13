import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from commands.set import JobEnvironment

class TestJobEnvironment(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"}, log_level="DEBUG")

    def tearDown(self):
        print("Removing {}".format(self.tmp))
        shutil.rmtree(self.tmp)

    def test_init(self):
        self.assertEqual(self.env.cli_options["PROJECT"], "test_project")
        self.assertEqual(self.env.cli_options["TYPE"], "test_type")
        self.assertEqual(self.env.cli_options["ASSET"], "test_asset")
        self.assertEqual(self.env.log_level, "DEBUG")
        self.assertIsNotNone(self.env.logger)
        self.assertIsNotNone(self.env.plg_manager)
        self.assertIsNotNone(self.env.backend)

    def test_init_no_cli_options(self):
        env = JobEnvironment(log_level="DEBUG")
        self.assertIsNone(env.cli_options)
        self.assertEqual(env.log_level, "DEBUG")
        self.assertIsNotNone(env.logger)
        self.assertIsNotNone(env.plg_manager)
        self.assertIsNotNone(env.backend)

    def test_init_no_job_directory(self):
        with patch("os.path.isdir", return_value=False):
            with patch("os.mkdir") as mock_mkdir:
                env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"}, log_level="DEBUG")
                mock_mkdir.assert_called_once_with(os.path.join(os.path.expanduser("~"), ".job"))

    def test_init_no_backend(self):
        with patch("commands.set.PluginManager.get_plugin_by_name", return_value=None):
            with self.assertRaises(commands.set.NoJobEnvironmentBackend):
                env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"}, log_level="DEBUG")

    def test_init_with_root(self):
        env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--root": "/test/root"}, log_level="DEBUG")
        self.assertEqual(env.root, "/test/root")

    def test_init_with_no_local_schema(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=[]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--no-local-schema": True}, log_level="DEBUG")
                mock_load_schemas.assert_not_called()

    def test_init_with_local_schema(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=["/test/schema"]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--no-local-schema": False}, log_level="DEBUG")
                mock_load_schemas.assert_called_once_with(["/test/schema"])

    def test_init_with_local_schema_and_init(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=["/test/schema"]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--no-local-schema": False}, log_level="DEBUG", history=False)
                mock_load_schemas.assert_called_once_with(["/test/schema"])
                self.assertIsNotNone(env.job_template)

    def test_init_with_local_schema_and_history(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=["/test/schema"]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                with patch("commands.set.JobTemplate.expand_path_template", return_value="/test/job/path"):
                    with patch("commands.set.JobEnvironment.backend") as mock_backend:
                        with patch("commands.set.JobEnvironment.find_job_context", return_value="test_context"):
                            env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--no-local-schema": False}, log_level="DEBUG", history=True)
                            mock_load_schemas.assert_called_once_with(["/test/schema"])
                            self.assertIsNotNone(env.job_template)
                            self.assertEqual(env.job_path, "/test/job/path")
                            mock_backend.assert_called_once_with(env.job_template)
                            mock_backend().find_context.assert_called_once_with(env.job_template, path=env.package_path)

    def test_init_with_local_schema_and_history_no_job_current(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=["/test/schema"]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                with patch("commands.set.JobTemplate.expand_path_template", return_value="/test/job/path"):
                    with patch("commands.set.JobEnvironment.backend") as mock_backend:
                        with patch("commands.set.JobEnvironment.find_job_context", return_value="test_context"):
                            env = JobEnvironment(cli_options={}, log_level="DEBUG", history=True)
                            mock_load_schemas.assert_called_once_with(["/test/schema"])
                            self.assertIsNotNone(env.job_template)
                            self.assertEqual(env.job_path, "/test/job/path")
                            mock_backend.assert_called_once_with(env.job_template)
                            mock_backend().find_context.assert_not_called()

    def test_init_with_local_schema_and_history_no_history_file(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=["/test/schema"]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                with patch("commands.set.JobTemplate.expand_path_template", return_value="/test/job/path"):
                    with patch("commands.set.JobEnvironment.backend") as mock_backend:
                        with patch("commands.set.JobEnvironment.find_job_context", return_value="test_context"):
                            with patch("os.path.isfile", return_value=False):
                                env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--no-local-schema": False}, log_level="DEBUG", history=True)
                                mock_load_schemas.assert_called_once_with(["/test/schema"])
                                self.assertIsNotNone(env.job_template)
                                self.assertEqual(env.job_path, "/test/job/path")
                                mock_backend.assert_called_once_with(env.job_template)
                                mock_backend().find_context.assert_not_called()

    def test_init_with_local_schema_and_history_cant_read_history_file(self):
        with patch("commands.set.JobTemplate.get_local_schema_path", return_value=["/test/schema"]):
            with patch("commands.set.JobTemplate.load_schemas") as mock_load_schemas:
                with patch("commands.set.JobTemplate.expand_path_template", return_value="/test/job/path"):
                    with patch("commands.set.JobEnvironment.backend") as mock_backend:
                        with patch("commands.set.JobEnvironment.find_job_context", return_value="test_context"):
                            with patch("os.path.isfile", return_value=True):
                                with patch("builtins.open", side_effect=IOError("test error")):
                                    env = JobEnvironment(cli_options={"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset", "--no-local-schema": False}, log_level="DEBUG", history=True)
                                    mock_load_schemas.assert_called_once_with(["/test/schema"])
                                    self.assertIsNotNone(env.job_template)
                                    self.assertEqual(env.job_path, "/test/job/path")
                                    mock_backend.assert_called_once_with(env.job_template)
                                    mock_backend().find_context.assert_not_called()

    def test_create_user_dirs(self):
        with patch("commands.set.JobTemplate.render", return_value={"/test/path": {"user_dirs": True}}):
            with patch("commands.set.JobTemplate.create", return_value=True) as mock_create:
                self.assertTrue(self.env.create_user_dirs())
                mock_create.assert_called_once_with(targets={"/test/path/test_user": {"/test/path": {"user_dirs": True}}})

    def test_create_user_dirs_with_user(self):
        with patch("commands.set.JobTemplate.render", return_value={"/test/path": {"user_dirs": True}}):
            with patch("commands.set.JobTemplate.create", return_value=True) as mock_create:
                self.assertTrue(self.env.create_user_dirs(user="test_user"))
                mock_create.assert_called_once_with(targets={"/test/path/test_user": {"/test/path": {"user_dirs": True}}})

    def test_get_history_from_file(self):
        with patch("os.path.isfile", return_value=True):
            with patch("builtins.open", mock_open(read_data='{"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"}')):
                cli_options = self.env.get_history_from_file({"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"})
                self.assertIsNotNone(cli_options)
                self.assertEqual(cli_options["PROJECT"], "test_project")
                self.assertEqual(cli_options["TYPE"], "test_type")
                self.assertEqual(cli_options["ASSET"], "test_asset")

    def test_get_history_from_file_no_history_file(self):
        with patch("os.path.isfile", return_value=False):
            cli_options = self.env.get_history_from_file({"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"})
            self.assertIsNone(cli_options)

    def test_get_history_from_file_cant_read_history_file(self):
        with patch("os.path.isfile", return_value=True):
            with patch("builtins.open", side_effect=IOError("test error")):
                cli_options = self.env.get_history_from_file({"PROJECT": "test_project", "TYPE": "test_type", "ASSET": "test_asset"})
                self.assertIsNone(cli_options)