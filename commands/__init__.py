from .create import *
from .set import *
from .read import *
from .write import *
import jobcli

# from .samplecommand import *

#!/usr/bin/python
# -*- encoding: utf-8 -*-

# import os
# import glob

# all_list = list()
# for f in glob.glob(os.path.dirname(__file__)+"/*.py"):
#     if os.path.isfile(f) and not os.path.basename(f).startswith('_'):
#         all_list.append(os.path.basename(f)[:-3])
# __all__ = all_list
# from . import *


# import click

# @click.group()
# @click.version_option()
# def cli():
#     pass #Entry Point