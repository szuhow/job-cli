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
def setup_cli():
    parser = argparse.ArgumentParser(description='Create a new job project')
    parser.add_argument('project', default=None, help='Project name')
    # parser.add_argument('type', nargs='?', default=None, help='Type of the project [optional]')
    parser.add_argument('asset', nargs='?', help='Asset for the project [optional]')
    parser.add_argument('--log-level', default='INFO', help='Log level of subcommands (INFO | DEBUG) [default: INFO]')
    parser.add_argument('--root', default='prefix', help='Overrides root directory (for debugging)')
    parser.add_argument('--no-local-schema', action='store_true', help='Disable saving/loading local copy of schema on "create"')
    parser.add_argument('--fromdb', action='store_true')
    parser.add_argument('--sanitize', action='store_true', help='Convert external names (from Shotgun i.e.)')
    parser.set_defaults(command=lambda args: CreateJobTemplate(cli_options=vars(args)).run())
    return parser





class CreateJobTemplate(BaseSubCommand):
    """Sub command which performs creation of disk directories
    based on schemas.
    """

    def __init__(self, cli_options, *args, **kwargs):
        from job.plugin import PluginManager
        self.plg_manager = PluginManager()
        print(f"Plugin Manager from create: {self.plg_manager.plugins}")
        super().__init__(cli_options, *args, **kwargs)


    def exists(self, ):
        """Check if project defined by job_template exists in a path
        using preferenced device plugin.
        """
        # prefered_devices = self.__preferences["plugin"]["DeviceDriver"]
        prefered_devices = self.manager.eval_element('development_variables/DeviceDriver') 
        #  add prefered_devices to list
        prefered_devices_list = []
        prefered_devices_list.append(prefered_devices)
        device = self.plg_manager.get_first_maching_plugin(prefered_devices_list)
        if not device:
            self.logger.exception("Can't find prefered device %s", prefered_devices)
            raise IOError
        # device.logger.debug("Selecting device driver %s", device)

        project_path = job_template.expand_path_template()

        if device.is_dir(project_path) and device.is_dir(local_templ):
            return True
        return False
    
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
        self, project, type_, asset, root, no_local_schema, log_level, dry_run=False
    ):
        """Creates a number of insances of JobTemplates, and executes
        its create() command to render disk locations.
        Allows for bulk execution of expression based asset names.

        Params:
            project, type, asset, root: to pass to JobTemplate class.
        """
        
        from copy import deepcopy
        from job.template import JobTemplate
        from os import environ

        # Pack arguments so we can ommit None one (like root):
        # Should we standarize it with some class?
        job = None
        # kwargs = {}
        # kwargs["job_current"] = project
        # kwargs["job_asset_type"] = type_
        # kwargs["job_asset_name"] = asset
        # kwargs["log_level"] = log_level
        # if root and root != "prefix":
        #     kwargs["root"] = root

        # Assets may contain range expression which we might want to expand:
        type_range = self.create_job_asset_range(type_, number_mult=1, zeros=2)
        asset_range = self.create_job_asset_range(asset)

        # for group in type_range:
        #     kwargs["job_asset_type"] = group
        #     for asset in asset_range:
        #         kwargs["job_asset_name"] = asset
                
        #         job = JobTemplate(**kwargs)

        #         # We need to reinitialize Job() to find local schemas:
        #         # This is contr-intuitive as this is most common case, not exeption.
        #         if not no_local_schema:
        #             local_schema_path = job.get_local_schema_path()
        #             # print(f"Loading local schema from {local_schema_path}")
        #             job.load_schemas(local_schema_path)
        #             super(JobTemplate, job).__init__(job.schema, "job", **kwargs)
        #         # We may want to create jobtemplate without executing it.
        #         if not dry_run and not job.exists():
        #             job.create()
        # # self.logger.warning("PO")
        return job


    def run(self):
        """Entry point create job command."""
        from copy import deepcopy
        # from jobcli import plugins
        import logging
        from jobcli.job.logger import LoggerFactory
        from jobcli.job.plugin import PluginManager
        from os.path import join
        log_level = self.cli_options["log_level"] 
        # self.set_logger(level=log_level, filename=log_level + ".log")
        # if not self.logger.handlers:
        #     self.set_logger(level=log_level, filename=log_level + ".log")
       
        # self.logger = LoggerFactory().get_logger("CreateJobTemplate", level=log_level)
       
        # self.plg_manager = PluginManager(self.cli_options["log_level"])

        # project = self.cli_options["project"]
        # type_ = self.cli_options["type"]
        # asset = self.cli_options["asset"]
        # log_lev = self.cli_options["log_level"]
        # no_local = self.cli_options["no_local_schema"]
        # root = self.cli_options["root"]
        # sanitize = self.cli_options["sanitize"]

       

        # device.logger.debug("Selecting device driver %s", device)

        # targets = manager.get_all_directories()
        targets = self.manager.dry_load(str(self.manager.project)).get_all_directories()

        prefered_devices = self.manager.eval_element('development_variables/DeviceDriver') 
        prefered_devices_list = []
        prefered_devices_list.append(prefered_devices)
        device = self.plg_manager.get_first_maching_plugin(prefered_devices_list)
        print(f"Device: {device}")
        if not device:
            self.logger.exception("Can't find prefered device %s", prefered_devices_list)
            return
            # raise IOError
        
        job_root_path = self.manager.get_job_root_path()

        if device.is_dir(job_root_path):
            self.logger.warning(
                    "Job already exists. Needs update?"
                )
            return
            # raise IOError

        for path in targets:
            device.make_dir(path)
            # create_link(path, targets)

            # Commented as lack of attrs
            # Cosmetics:
            device.remove_write_permissions(path)
            device.add_write_permissions(path, {'user': 'read', 'group': 'write'})
            device.set_ownership(path)
        
        # Usual path without database pull.
        # if not self.cli_options["fromdb"]:
        #     # Create root asset just in case (project/project/project)
        #     print("Creating root asset")
        #     job = self.create_job(
        #         project, project, project, root, no_local, log_lev, dry_run=True
        #     )
            
        #     if not job.exists():
        #         job.create()
        #         if not no_local:
        #             job.dump_local_templates()
        #     else:
        #         #  get logger from base class
                
        #         self.logger.warning(
        #             "Job already exists. Needs update? %s",
        #             "/".join([project, project, project]),
        #         )
    
        #     # Proceed with assets if specified in cli (asset and type_ may contain range expressions)
        #     print(type_, asset)
        #     if type_ and asset:
        #         print("Creating asset")
        #         job = self.create_job(project, type_, asset, root, no_local, log_lev)

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
