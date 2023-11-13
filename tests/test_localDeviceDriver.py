import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from plugins.localDeviceDriver import LocalDevicePython
import stat

class TestLocalDevicePython(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.driver = LocalDevicePython(log_level="DEBUG")

    def tearDown(self):
        print("Removing {}".format(self.tmp))
        shutil.rmtree(self.tmp)

    def test_is_dir(self):
        self.assertTrue(self.driver.is_dir(self.tmp))
        self.assertFalse(self.driver.is_dir(os.path.join(self.tmp, "nonexistent")))

    def test_make_dir(self):
        new_dir = os.path.join(self.tmp, "new_dir")
        self.assertTrue(self.driver.make_dir(new_dir))
        self.assertTrue(os.path.exists(new_dir))
        self.assertFalse(self.driver.make_dir(new_dir))

    def test_copy_file(self):
        source_file = os.path.join(self.tmp, "source_file")
        target_file = os.path.join(self.tmp, "target_file")
        with open(source_file, "w") as f:
            f.write("test")
        self.assertTrue(self.driver.copy_file(source_file, target_file))
        self.assertTrue(os.path.exists(target_file))
        self.assertFalse(self.driver.copy_file(source_file, target_file))

    def test_make_link(self):
        path = os.path.join(self.tmp, "path")
        link_path = os.path.join(self.tmp, "link_path")
        with open(path, "w") as f:
            f.write("test")
        self.assertTrue(self.driver.make_link(path, link_path))
        self.assertTrue(os.path.islink(link_path))
        self.assertFalse(self.driver.make_link(path, link_path))


    def test_remove_write_permissions(self):
        path = os.path.join(self.tmp, "path")
        with open(path, "w") as f:
            f.write("test")
        os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
        self.driver.remove_write_permissions(path)
        self.assertEqual(os.stat(path).st_mode & stat.S_IWUSR, 0)

    def test_add_write_permissions(self):
        path = os.path.join(self.tmp, "path")
        with open(path, "w") as f:
            f.write("test")
        os.chmod(path, 0o222)
        self.driver.add_write_permissions(path)
        self.assertEqual(os.stat(path).st_mode & 0o222, 0o222)

    @patch("os.chown")
    @patch("plugins.localDeviceDriver.getgrnam")
    @patch("plugins.localDeviceDriver.getpwnam")
    def test_set_ownership(self, mock_getpwnam, mock_getgrnam, mock_chown):
        path = os.path.join(self.tmp, "path")
        mock_getpwnam.return_value = MagicMock(pw_uid=1000)
        mock_getgrnam.return_value = MagicMock(gr_gid=1000)
        self.assertTrue(self.driver.set_ownership(path, user="testuser", group="testgroup"))
        mock_getpwnam.assert_called_once_with("testuser")
        mock_getgrnam.assert_called_once_with("testgroup")
        mock_chown.assert_called_once_with(path, 1000, 1000)





