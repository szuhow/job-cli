import unittest
import os, sys, tempfile, logging

# Get modules
job_root_path = os.path.dirname(os.path.realpath(__file__))
job_root_path = os.path.dirname(job_root_path)
sys.path = [job_root_path] + sys.path
sys.path += [os.path.join(job_root_path, "external/docopt")]
sys.path += [os.path.join(job_root_path, "external/schematics")]



class CreateJobTemplateTest(unittest.TestCase):
    def setUp(self):
        from commands.create import CreateJobTemplate
        self.tmp = tempfile.mkdtemp()
        self.cli_options = {}
        self.cli_options['PROJECT'] = 'testproject'
        self.cli_options['TYPE'] = 'testtype'
        self.cli_options['ASSET'] = 'testasset'
        self.cli_options['--log-level'] = 'debug'
        self.cli_options['--no-local-schema'] = False
        self.cli_options['--root'] = self.tmp
        self.cli_options['--sanitize'] = False
        self.creator = CreateJobTemplate(self.cli_options)

    def test_get_log_level(self):
        level = self.creator.get_log_level_from_options()
        self.assertEqual(level, getattr(logging, self.cli_options['--log-level']))

    def test_create_job_asset_range(self):
        shots = ['sh0010', 'sh0020', 'sh0030', 'sh0040']
        result = self.creator.create_job_asset_range('sh[1-4]', 10, 4)
        shots = ['sh00100', 'sh00200', 'sh00300', 'sh00400']
        result = self.creator.create_job_asset_range('sh[1-4]', 100, 5)
        self.assertEqual(shots, result)
        # self.assertTrue('FOO'.isupper())
        # self.assertFalse('Foo'.isupper())

    def test_create_job(self):
        from job.template import JobTemplate
        project = self.cli_options['PROJECT']
        type_ = self.cli_options['TYPE']
        asset = self.cli_options['ASSET']
        root = self.tmp
        no_local_schema = self.cli_options['--no-local-schema']
        log_level = self.cli_options['--log-level']
        job = self.creator.create_job(project, project, project,
                                      root, no_local_schema, log_level, dry_run=False)
        # job = self.creator.create_job(project, type_, asset, 
        #     root, no_local_schema, log_level, dry_run=False)

        self.assertTrue(isinstance(job, JobTemplate))

        path = "/".join([project, project, project])
        path = os.path.join(self.tmp, path)
        self.assertTrue(os.path.exists(path))

        # check that s.split fails when the separator is not a string
        # with self.assertRaises(TypeError):
        #     s.split(2)




suite = unittest.TestLoader().loadTestsFromTestCase(CreateJobTemplateTest)
unittest.TextTestRunner(verbosity=3).run(suite)
if __name__ == '__main__':
    unittest.main()