# -*- coding: utf-8 -*-

##########################################################################
#
#  Copyright (c) 2017, Human Ark Animation Studio. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Human Ark Animation Studio nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

from jobcli.commands.base import BaseSubCommand
import logging
import argparse
import plugins
import re
from jobcli.job.plugin import PluginManager

def asset_range(value):
    match = re.match(r'asset\[(\d+)-(\d+)\]', value)
    if match:
        return list(map(int, match.groups()))
    else:
        return value

def setup_cli():
    parser = argparse.ArgumentParser(description='Create a new job project')
    parser.add_argument('project', default=None, help='Project name')
    # parser.add_argument('type', nargs='?', default=None, help='Type of the project [optional]')
    parser.add_argument('asset', type=asset_range, help='Asset for the project in the alternative range format asset[x-y]')
    parser.add_argument('--log-level', default='INFO', help='Log level of subcommands (INFO | DEBUG) [default: INFO]')
    # parser.add_argument('--root', default='prefix', help='Overrides root directory (for debugging)')
    # parser.add_argument('--no-local-schema', action='store_true', help='Disable saving/loading local copy of schema on "create"')
    parser.add_argument('--fromdb', action='store_true')
    # parser.add_argument('--sanitize', action='store_true', help='Convert external names (from Shotgun i.e.)')
    parser.set_defaults(command=lambda args: CreateJobTemplate(cli_options=vars(args)).run())
    return parser



class CreateJobTemplate(BaseSubCommand):
    """Sub command which performs creation of disk directories
    based on schemas.
    """

    def __init__(self, cli_options, *args, **kwargs):
        from job.plugin import PluginManager
        self.plg_manager = PluginManager()
        print("CreateJobTemplate", cli_options)
        super().__init__(cli_options, *args, **kwargs)
    

    def create_job_asset_range(self, job_asset_name, number_mult=10, zeros=4):
        """Generates a list of asset names from asset name expression:
        asset_name[1-10]

        Params:
            asset_name = 'shot[1-10]' ('shot0010' which won't be expanded.)

        Returns:
            list = [base0010, base0020, ....]
        """

        def parse_asset_name(name):
            """Parse asset name or asset group for patterns asset[1-2]"""
            import re

            expression = re.compile("\[([0-9]+)-([0-9]+)\]$")
            sequence = expression.findall(name)
            if sequence:
                return [int(x) for x in list(sequence[0])]
            return []

        job_asset_name_list = []
        job_asset_range = parse_asset_name(job_asset_name)
        assert not job_asset_range or len(job_asset_range) == 2

        # !!! inclusive
        if len(job_asset_range) == 2:
            job_asset_range[1] += 1  # !!!

        if job_asset_range:
            job_asset_base = job_asset_name.split("[")[0]  # Correct assumption?
            for asset_num in range(*job_asset_range):
                # Should we allow to customize it? Place for preferences?
                asset_num *= number_mult
                new_job_asset_name = job_asset_base + str(asset_num).zfill(zeros)
                job_asset_name_list += [new_job_asset_name]

        else:
            job_asset_name_list += [job_asset_name]

        return job_asset_name_list

    def create_job(
        self, project, dry_run=False
    ):
        """Creates a number of insances of JobTemplates, and executes
        its create() command to render disk locations.
        Allows for bulk execution of expression based asset names.

        Params:
            project, type, asset, root: to pass to JobTemplate class.
        """
        
        from copy import deepcopy
        from job.template import JobTemplate
        # from os import environ
        
        # Pack arguments so we can ommit None one (like root):
        # Should we standarize it with some class?
        # kwargs = {}
        # kwargs["job_current"] = project
        # kwargs["job_asset_type"] = type_
        # kwargs["job_asset_name"] = asset
        # kwargs["log_level"] = log_level
        # if root and root != "prefix":
        #     kwargs["root"] = root

       
        self.set_manager(project)
        targets = self.manager.dry_load(str(self.manager.project)).get_all_directories()
        prefered_devices = self.manager.eval_element('development_variables/DeviceDriver') 
        prefered_devices_list = []
        prefered_devices_list.append(prefered_devices)
        device = self.plg_manager.get_first_maching_plugin(prefered_devices_list)
        if not device:
            self.logger.exception("Can't find prefered device %s", prefered_devices_list)
            return        
        # print("Device", device)
        # Create root asset just in case (project/project/project)
        job_root_path = self.manager.get_job_root_path()

        if device.is_dir(job_root_path):
            self.logger.warning(
                "Job already exists. Needs update?"
            )
            return

        device.logger.debug("Selecting device driver %s", device)
    

        for path in targets:
            if not dry_run:
                device.make_dir(path)
                # create_link(path, targets)
                device.remove_write_permissions(path)
                device.add_write_permissions(path, {'user': 'read', 'group': 'write'})
                device.set_ownership(path)
        print("Done")
        


    def run(self):
        """Entry point create job command."""
        from copy import deepcopy
        import logging
        from jobcli.job.logger import LoggerFactory
        # from os.path import join

        # type_range = self.create_job_asset_range(type_, number_mult=1, zeros=2)
        # no_local = self.cli_options["no_local_schema"]
        # sanitize = self.cli_options["sanitize"]
      
        # # Usual path without database pull.
        for cli_option in self.cli_options:
            print(cli_option, self.cli_options[cli_option])

        if not self.cli_options["fromdb"]:
            asset = self.cli_options["asset"]
            asset_range = self.create_job_asset_range(asset)
            # type_ = self.cli_options["type"]
        
             # Assets may contain range expression which we might want to expand:
            for asset in asset_range:
                print(f"Creating asset {asset}")
                project = {'project': self.cli_options['project'], 
                    'episode': '$EP', 
                    'group': 'user', 
                    'asset': asset}
                self.create_job(project)
            

        # else:
        #     # This is database path
        #     self.db_driver = self.plg_manager.get_plugin_by_name("ShotgunReader")
        #     project_items = self.db_driver.get_project_items(project, sanitize=sanitize)
        #     job = self.create_job(
        #         project, project, project, root, no_local, log_lev, dry_run=True
        #     )

        #     if not job.exists():
        #         job.create()
        #         if not no_local:
        #             job.dump_local_templates()

        #     for item in project_items:
        #         if not item["job_asset_name"] or not item["job_asset_type"]:
        #             self.logger.warning(
        #                 "Database item missing data, can't create it: %s", str(item)
        #             )
        #             continue
        #         type_ = item["job_asset_type"]
        #         asset = item["job_asset_name"]
        #         job = self.create_job(project, type_, asset, root, no_local, log_lev)
