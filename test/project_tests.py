#TO RUN: joey2 project_operation_tests.py

import sys
import os
import unittest
import shutil

sys.path.append('../')
import lib.config as config
import lib.mm_util as util
import test_helper as helper
from lib.mm_connection import MavensMatePluginConnection
from lib.mm_client import MavensMateClient

class TestProject(unittest.TestCase):

    # FYI: overriding this constructor is apparently not recommended, so we should find a better way to init test data
    def __init__(self, *args, **kwargs): 
        super(TestProject, self).__init__(*args, **kwargs) 
        self.project_name = 'MavensMateUnitTestProject'
        self.username = 'mm@force.com'
        self.password = 'force'
        self.org_type = 'developer' 

    def setUp(self):
        config.connection = MavensMatePluginConnection(client='Sublime Text',project_name='p41')

    def test_index_project(self):
        config.connection.project.index_metadata()

    def do_test_assumptions(self):
        pass

    def tearDown(self):
        try:
            pass
            #shutil.rmtree(config.connection.workspace+"/MavensMateUnitTestProject")
        except:
            pass

if __name__ == '__main__':
    unittest.main()