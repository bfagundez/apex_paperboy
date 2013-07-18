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

class TestUtils(unittest.TestCase):

    # FYI: overriding this constructor is apparently not recommended, so we should find a better way to init test data
    def __init__(self, *args, **kwargs): 
        super(TestUtils, self).__init__(*args, **kwargs) 

    def setUp(self):
        config.connection = MavensMatePluginConnection(client='Sublime Text')

    def get_metadata_hash(self):
        print util.get_metadata_hash(
            ['/Users/josephferraro/Development/st/p17/src/classes/foo.cls']
        )

        print util.get_metadata_hash([
                '/Users/josephferraro/Development/st/p17/src/classes/foo.cls',
                '/Users/josephferraro/Development/st/p17/src/classes/foo2.cls',
                '/Users/josephferraro/Development/st/p17/src/pages/foo3.page'
            ]
        )

    def do_test_assumptions(self):
        pass

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()