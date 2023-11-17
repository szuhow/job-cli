from job.plugin import PluginManager, PluginType


class samplePlugin(PluginManager):
    name = "samplePlugin"
    type = PluginType.Sample

    def register_signals(self):
        # self.logger.debug("%s registering as %s", self.name, self.type)
        return True

    def __call__(self):
        print("Hello from samplePlugin")
