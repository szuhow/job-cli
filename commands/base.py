class BaseSubCommand(object):
    """A base command."""

    logger = None

    def __init__(self, cli_options, *args, **kwargs):
        # self.cli_options = cli_options
        self.args = args
        self.kwargs = kwargs
        self.cli_options = cli_options

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
