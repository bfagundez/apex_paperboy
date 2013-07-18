#TO RUN: joey2 project_create_tests.py
# OR TO RUN SPECIFIC METHODS: 
# joey2 -m unittest project_tests.TestProjectCreate.test_create_project_via_package_xml_file
# joey2 -m unittest project_tests.TestProjectCreate.test_create_project_via_package_dict

import sys
import os
import unittest
import shutil
import requests

sys.path.append('../')
import lib.config as config
import lib.mm_util as util
import test_helper as helper
from lib.mm_client import MavensMateClient

class TestToolingAPI(unittest.TestCase):

    # FYI: overriding this constructor is apparently not recommended, so we should find a better way to init test data
    def __init__(self, *args, **kwargs): 
        super(TestToolingAPI, self).__init__(*args, **kwargs) 
        self.username = 'mm@force.com'
        self.password = 'force'
        self.org_type = 'developer' 
        self.client = MavensMateClient(credentials={
            "username" : self.username,
            "password" : self.password,
            "org_type" : self.org_type
        })

    def setUp(self):
        pass

    def test_overlay_actions(self):
        payload = {
            "ActionScriptType" : "None",
            "ExecutableEntityId" : "01pd0000001yXtYAAU",
            "IsDumpingHeap" : True,
            "Iteration" : 1,
            "Line" : 3,
            "ScopeId" : "005d0000000xxzsAAA"
        }
        list_result = self.client.get_overlay_actions(id='01pd0000001yXtYAAU')
        print list_result

        create_result = self.client.create_overlay_action(payload)
        print create_result

        list_result = self.client.get_overlay_actions(id='01pd0000001yXtYAAU')
        print list_result

        # delete_result = self.client.remove_overlay_action(id='01pd0000001yXtYAAU', line_number=3)
        # print delete_result

        # list_result = self.client.get_overlay_actions(id='01pd0000001yXtYAAU')
        # print list_result

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()