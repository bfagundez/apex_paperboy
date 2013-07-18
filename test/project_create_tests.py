#TO RUN: joey2 project_create_tests.py
# OR TO RUN SPECIFIC METHODS: 
# joey2 -m unittest project_tests.TestProjectCreate.test_create_project_via_package_xml_file
# joey2 -m unittest project_tests.TestProjectCreate.test_create_project_via_package_dict

import sys
import os
import unittest
import shutil

sys.path.append('../')
import lib.config as config
import lib.mm_util as util
from lib.mm_connection import MavensMatePluginConnection

class TestProjectCreate(unittest.TestCase):

    # FYI: overriding this constructor is apparently not recommended, so we should find a better way to init test data
    def __init__(self, *args, **kwargs): 
        super(TestProjectCreate, self).__init__(*args, **kwargs) 
        self.project_name = 'MavensMateUnitTestProject'
        self.username = 'mm@force.com'
        self.password = 'force'
        self.org_type = 'developer' 
        

    def setUp(self):
        config.connection = MavensMatePluginConnection(client='Sublime Text')

    def test_create_project_via_package_xml_file(self):
        config.connection.new_project({
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "vc_username"     : None,
            "vc_password"     : None,    
            "vc_url"          : None,
            "vc_type"         : None,
            "vc_branch"       : None,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        }, action='new')
        #self.do_project_assumptions()
        config.connection.project.index_metadata()

    # def test_create_project_via_json_manifest(self):
    #     config.connection.new_project(
    #         manifest = config.base_path+'/test/resources/manifest_project_create.json' #=>
    #     )
    #     self.do_project_assumptions()

    # def test_create_project_via_package_dict(self):
    #     # package = {
    #     #     'unpackaged' : {
    #     #         'types' : [
    #     #             {
    #     #                 "members": "*", 
    #     #                 "name": "ApexClass"
    #     #             }
    #     #         ]
    #     #     }
    #     # }
    #     package = {
    #         'unpackaged' : {
    #             'types' : [
    #                 {
    #                     "members": ["MultiselectControllerTest", "MultiselectController"],
    #                     "name": "ApexClass"
    #                 }
    #             ]
    #         }
    #     }

    #     config.connection.new_project(
    #         project_name    = self.project_name,
    #         username        = self.username,
    #         password        = self.password,
    #         org_type        = self.org_type,
    #         vc_username     = None,
    #         vc_password     = None,    
    #         vc_url          = None,
    #         vc_type         = None,
    #         vc_branch       = None,
    #         package         = package #=> this should be a dict of package contents or the location of a package.xml
    #     )
    #     self.do_project_assumptions()

    def do_project_assumptions(self):
        project_directory = config.connection.workspace+"/"+self.project_name
        self.assertTrue(os.path.isdir(project_directory))
        self.assertTrue(os.path.isdir(project_directory+"/config"))
        self.assertTrue(os.path.isdir(project_directory+"/src"))
        self.assertTrue(util.get_password_by_project_name(self.project_name) == self.password)

    def tearDown(self):
        #shutil.rmtree(config.connection.workspace+"/MavensMateUnitTestProject")
        pass
        
if __name__ == '__main__':
    unittest.main()