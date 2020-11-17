import unittest
import os, sys, tempfile, logging
from logging import INFO


# Get modules
job_root_path = os.path.dirname(os.path.realpath(__file__))
job_root_path = os.path.dirname(job_root_path)
sys.path = [job_root_path] + sys.path
sys.path += [os.path.join(job_root_path, "external/docopt")]
sys.path += [os.path.join(job_root_path, "external/schematics")]
sys.path += [os.path.join(job_root_path, "plugins")]


class LocalDeviceShellTest(unittest.TestCase):
    def setUp(self):
        from job.plugin import PluginManager 
        self.root = tempfile.mkdtemp()
        from localDeviceDriver import LocalDeviceShell
        self.device = LocalDeviceShell()

    def test_is_dir(self):
        self.assertEqual(self.device.is_dir(self.root), os.path.isdir(self.root))

    def test_make_dir(self):
        target = os.path.join(self.root, 'test')
        self.device.make_dir(target)
        self.assertTrue(os.path.isdir(target))

    def test_copy_file(self):
        source = os.path.join(self.root, 'sourcefile.txt')
        with open(source, 'w') as file:
            file.close()
        target = os.path.join(self.root, 'targetfile.txt')
        self.device.copy_file(source, target)
        self.assertTrue(os.path.isfile(target))

    def test_make_link(self):
        source = os.path.join(self.root, 'sourcefilelink.txt')
        with open(source, 'w') as file:
            file.close()
        target = os.path.join(self.root, 'targetfilelink.txt')
        self.device.make_link(source, target)
        self.assertTrue(os.path.islink(target))

    def test_set_permissions(self):
        import stat
        source = os.path.join(self.root, 'permissions')
        os.mkdir(source)

        self.device.add_write_permissions(source, True, True)
        permissions = os.stat(source)[stat.ST_MODE]
        self.assertTrue(permissions & stat.S_IWGRP)
        self.assertTrue(permissions & stat.S_IWOTH)

        self.device.add_write_permissions(source, False, False)
        permissions = os.stat(source)[stat.ST_MODE]
        self.assertFalse(permissions & stat.S_IWGRP)
        self.assertFalse(permissions & stat.S_IWOTH)

        self.device.add_write_permissions(source, True, False)
        permissions = os.stat(source)[stat.ST_MODE]
        self.assertTrue(permissions & stat.S_IWGRP)
        self.assertFalse(permissions & stat.S_IWOTH)

        self.device.add_write_permissions(source, False, False, False)
        permissions = os.stat(source)[stat.ST_MODE]
        self.assertFalse(permissions & stat.S_IWUSR)
        self.assertFalse(permissions & stat.S_IWGRP)
        self.assertFalse(permissions & stat.S_IWOTH)


    def test_set_ownership(self):
        from getpass import getuser
        source = os.path.join(self.root, 'ownership')
        os.mkdir(source)
        user = getuser()
        group = "artists"
        os.system("ls -la %s" % self.root)
        self.device.set_ownership(source, user, group )
        os.system("ls -la %s" % self.root)


# class LocalDevicePythonTest(LocalDeviceShellTest):
#     def setUp(self):
#         from job.plugin import PluginManager 
#         self.root = tempfile.mkdtemp()
#         from localDeviceDriver import LocalDevicePython
#         self.device = LocalDevicePython()

if __name__ == '__main__':
    unittest.main()