import logging
from logging.handlers import RotatingFileHandler
from os.path import expanduser, join, isdir
from os import mkdir
from project import ProjectManager


# from jobcli.job.plugin import PluginManager

class BaseSubCommand(object):
    """A base command."""

    # logger = None

    def __init__(self, cli_options, *args, **kwargs):
        # self.cli_options = cli_options
        import plugins
        self.args = args
        self.kwargs = kwargs
        self.cli_options = cli_options
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # set options for ProjectManager from cli_options
        # project = {'project': cli_options['project'], 
        #            'episode': '$EP', 
        #            'group': 'user', 
        #            'asset': cli_options['asset']}
        self.set_logger()
        # self.logger.set_logger(level=self.get_log_level_from_options(), filename="app.log")
        # self.manager = ProjectManager(project)
       

    def set_manager(self, project):
        """ """
        self.manager = ProjectManager(project)


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

    def get_log_level_from_options(self):
        """ """
        import logging

        log_level = logging.INFO
        # This is ugly, subcommand should extend list of options (like plugin)
        # not rely on bin/job to provide corrent switches.
        # _opt = self.cli_options
        if self.cli_options:
            _opt = self.options
        if _opt["log_level"]:
            try:
                log_level = getattr(logging, _opt["log_level"])
            except:
                pass
        return log_level

    def run(self):
        raise NotImplementedError("You must implement the run() method yourself!")
