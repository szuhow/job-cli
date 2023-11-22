from job.plugin import PluginManager, PluginType, DeviceDriver
from logging import INFO
import os, stat
from grp import getgrnam
from pwd import getpwnam, getpwuid
from getpass import getuser
from subprocess import Popen, PIPE
from job.utils import get_log_level_from_options
import logging
from logging.handlers import RotatingFileHandler
from os.path import expanduser, join, isdir
from os import mkdir
# TODO: remove
USE_SUDO = False


class LocalDevicePython(DeviceDriver, PluginManager):
    name = "LocalDevicePython"
    type = PluginType.DeviceDriver
    logger = None

    def __init__(self, log_level = INFO, **kwargs):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.kwargs = kwargs    
        name = self.__class__.__name__
        self.set_logger(level=log_level, filename=str(log_level) + ".log")



    def set_logger(self, level="DEBUG", filename="app.log"):
        """Set up basic logging configuration."""
        
        
        self.logger.setLevel(level)
        self.logger.propagate = False
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        home = expanduser("~")
        path = join(home, ".job")
        if not isdir(path) and isdir(home):
            mkdir(path)

        path = join(path, filename)
        # Create a file handler
        file_handler = RotatingFileHandler(path)
        file_handler.setLevel(level)

        # Create a formatter and add it to the handlers
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add the handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)


    def register_signals(self):
        return True

    def is_dir(self, path):
        """ """
        from os.path import isdir

        return isdir(path)

    def make_dir(self, path):
        """Uses standard Python facility to create a directory tree."""
        # TODO: How to process errors,
        # TODO: How to implement more sofisticated error treatment
        # like: If path exists, and it's a link do A, if it's not a link do B?
        if os.path.exists(path):
            self.logger.warning("Path exists, can't proceed %s", path)
            return False
        # same as above.
        try:
            os.makedirs(path)
            self.logger.info("Making %s", path)
            return True
        except OSError as e:
            self.logger.exception("Couldn't make %s", path)
            raise OSError

    def copy_file(self, source, target):
        """Uses standard Python facility to copy file."""
        from shutil import copyfile

        if not os.path.exists(source):
            self.logger.warning("File doesn't exists %s", source)
            return False

        if os.path.exists(target):
            self.logger.warning("File exists, can't copy %s", target)
            return False

        try:
            path, file = os.path.split(source)
            if not os.path.isdir(path):
                os.makedirs(path)
            copyfile(source, target)

            self.logger.info("Copying %s to %s", source, target)
            return True
        except IOError as e:
            self.logger.exception("Couldn't copy %s", source)
            raise IOError

    def make_link(self, path, link_path):
        # print(f"Path {path} and {link_path}")
        if os.path.exists(link_path):
            if os.path.islink(link_path):
                self.logger.warning("Link exists %s", link_path)
            else:
                self.logger.warning(
                    "Path exists, so I can't make a link here %s", link_path
                )
            return False

        try:
            os.symlink(path, link_path)
            self.logger.info("Making symlink %s %s", path, link_path)
            return True
        except:
            self.logger.exception("Can't make a link %s %s", path, link_path)
            raise OSError

    # http://stackoverflow.com/questions/16249440/changing-file-permission-in-python
    def remove_write_permissions(self, path):
        """Remove write permissions from this path, while keeping all other permissions intact.

        Params:
            path:  The path whose permissions to alter.
        """

        NO_USER_WRITING = ~stat.S_IWUSR
        NO_GROUP_WRITING = ~stat.S_IWGRP
        NO_OTHER_WRITING = ~stat.S_IWOTH
        NO_WRITING = NO_USER_WRITING & NO_GROUP_WRITING & NO_OTHER_WRITING

        current_permissions = stat.S_IMODE(os.lstat(path).st_mode)
        try:
            os.chmod(path, current_permissions & NO_WRITING)
        except:
            self.logger.exception("Can't remove write permission from %s", path)
            raise OSError

        self.logger.debug(
            "remove_write_permissions: %s (%s)", path, current_permissions & NO_WRITING
        )

    def add_write_permissions(self, path, group=True, others=False):
        """Set permissions flags according to provided params.

        Params:
            path:          The path to set permissions for.
            group, others: Permissions masks.
        """

        WRITING = stat.S_IWUSR
        if group:
            WRITING = WRITING | stat.S_IWGRP
        if others:
            WRITING = WRITING | stat.S_IWOTH

        current_permissions = stat.S_IMODE(os.lstat(path).st_mode)

        try:
            os.chmod(path, current_permissions | WRITING)
        except:
            self.logger.exception("Can't add write permission for %s", path)
            raise OSError

        self.logger.debug(
            "add_write_permissions: %s (%s)", path, current_permissions | WRITING
        )

    def set_ownership(self, path, user=None, group=None):
        """Sets the ownership of a path.

        Params:
            user:  User string (None means no change)
            group: Group string (None means no change)
        """


        def get_user_id(path, user):
            """ """
            if not user:
                return os.stat(path).st_uid
            try:
                return getpwnam(user).pw_uid
            except:
                self.logger.exception("Can't find specified user %s", user)
                raise OSError

        def get_group_id(path, group):
            """"""
            if not group:
                return os.stat(path).st_gid
            try:
                return getgrnam(group).gr_gid
            except:
                self.logger.exception("Can't find specified group %s", group)
                raise OSError

        # This may happen due to 'upper' logic...
        if not user and not group:
            return False
        #
        uid = get_user_id(path, user)
        gid = get_group_id(path, group)
        #
        try:
            os.chown(path, uid, gid)
        except:
            self.logger.exception("Can't change ownership for %s", path)
            raise OSError

        self.logger.debug("set_ownership: %s (%s, %s)", path, uid, gid)
        return True


class LocalDeviceShell(DeviceDriver, PluginManager):
    """The purpose of this class is to all sudo commands on local device.
    In time we would like to implement ssh access to a storage.
    """

    name = "LocalDeviceShell"
    type = PluginType.DeviceDriver
    logger = None

    def __init__(self, log_level=INFO, **kwargs):
        name = self.__class__
        from job.logger import LoggerFactory

        name = self.__class__.__name__
        self.logger = LoggerFactory().get_logger(name, level=log_level)

    def register_signals(self):
        return True

    def is_dir(self, path):
        """ """
        from os.path import isdir

        return isdir(path)

    def make_dir(self, path, sudo=USE_SUDO):
        """Uses Linux shell facility to create a directory tree."""
        from subprocess import Popen, PIPE

        command = []
        if os.path.exists(path):
            self.logger.warning("Path exists %s", path)
            return False
        try:
            if sudo:
                command += ["sudo"]

            command += ["mkdir", "-p", path]
            out, err = Popen(
                command, shell=False, stdout=PIPE, stderr=PIPE
            ).communicate()
            if not err:
                self.logger.debug("Making %s", path)
                return True
            else:
                # print(err)
                self.logger.exception(str(err))
                raise OSError
        except OSError as e:
            self.logger.exception("Couldn't make %s", path)
            raise OSError

    def copy_file(self, source, target, sudo=USE_SUDO):
        """Uses Linux shell facility to create a directory tree."""
        from subprocess import Popen, PIPE

        command = []

        if not os.path.exists(source):
            self.logger.warning("File doesn't exist %s", source)
            return False

        if os.path.exists(target):
            self.logger.warning("File exists %s", target)
            return False

        try:
            if sudo:
                command += ["sudo"]

            command += ["cp", "-p", source, target]
            out, err = Popen(
                command, shell=False, stdout=PIPE, stderr=PIPE
            ).communicate()
            if not err:
                self.logger.debug("Copying %s to %s", source, target)
                return True
            else:
                self.logger.exception(err)
                raise IOError
        except IOError as e:
            self.logger.exception("Couldn't copy %s", source)
            raise IOError

    def make_link(self, path, link_path, sudo=USE_SUDO):
        from subprocess import Popen, PIPE
        
        command = []
        if os.path.exists(link_path):
            if os.path.islink(link_path):
                self.logger.warning("Link exists %s", link_path)
            else:
                self.logger.warning(
                    "Path exists, so I can't make a link here %s", link_path
                )
            return False

        try:
            if sudo:
                command += ["sudo"]

            command += ["ln", "-s", path, link_path]
            out, err = Popen(
                command, shell=False, stdout=PIPE, stderr=PIPE
            ).communicate()
            if not err:
                self.logger.debug("Making symlink %s %s", path, link_path)
                return True
            else:
                self.logger.exception(err)
                raise OSError
        except:
            self.logger.exception("Can't make a link %s %s", path, link_path)
            raise OSError

    def set_permissions(self, path, user=None, group=None, others=None, sudo=USE_SUDO):
        """Set permissions flags according to provided params.

        Params:
            path:          The path to set permissions for.
            group, others, user: Permissions masks.
        """
        from subprocess import Popen, PIPE

        USER = 0
        GROUP = 1
        OTHERS = 2
        command = []

        if sudo:
            command += ["sudo"]

        command += ["chmod", "-v"]
        permission_bits = [6, 4, 4]

        if not user:
            permission_bits[USER] = 4

        if group:
            permission_bits[GROUP] = 6

        if others:
            permission_bits[OTHERS] = 6

        permission_str = "".join([str(x) for x in permission_bits])
        command += [permission_str]
        command += [path]

        try:
            out, error = Popen(
                command, shell=False, stderr=PIPE, stdout=PIPE
            ).communicate()
        except:
            raise OSError

        if error:
            self.logger.exception("%s, %s", error, path)
            raise OSError

        self.logger.debug("%s (%s)", " ".join(command), "out")

    def set_ownership(self, path, user=None, group=None, sudo=USE_SUDO):
        """Sets the ownership of a path.

        Params:
            user:  User string (None means no change)
            group: Group string (None means no change)
        """


        def get_user_id(path, user):
            """ """
            if not user:
                return os.stat(path).st_uid
            try:
                return getpwnam(user).pw_uid
            except:
                self.logger.exception("Can't find specified user %s", user)
                raise OSError

        def get_group_id(path, group):
            """"""
            if not group:
                return os.stat(path).st_gid
            try:
                return getgrnam(group).gr_gid
            except:
                self.logger.exception("Can't find specified group %s", group)
                raise OSError

        # This may happen due to 'upper' logic...
        if not user and not group:
            return False

        uid = get_user_id(path, user)
        gid = get_group_id(path, group)

        command = []
        if sudo:
            command += ["sudo"]

        if group:
            command += ["chgrp", group, path]
            out, err = Popen(
                command, shell=False, stdout=PIPE, stderr=PIPE
            ).communicate()
            if err:
                self.logger.exception("Can't change ownership for %s", path)
                raise OSError

        command = []
        if sudo:
            command += ["sudo"]

        if user:
            command += ["chown", user, path]
            out, err = Popen(
                command, shell=False, stdout=PIPE, stderr=PIPE
            ).communicate()
            if err:
                self.logger.exception("Can't change ownership for %s", path)
                raise OSError

        self.logger.debug("set_ownership: %s (%s, %s)", path, user, group)
        return True
