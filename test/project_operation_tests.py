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

class TestProjectOperations(unittest.TestCase):

    RunInitialDelete = True

    # FYI: overriding this constructor is apparently not recommended, so we should find a better way to init test data
    def __init__(self, *args, **kwargs): 
        super(TestProjectOperations, self).__init__(*args, **kwargs) 
        self.project_name = 'MavensMateUnitTestProject'
        self.username = 'mm@force.com'
        self.password = 'force'
        self.org_type = 'developer' 

    def setUp(self):
        config.connection = MavensMatePluginConnection(client='Sublime Text')
        if os.path.exists(config.connection.workspace+"/MavensMateUnitTestProject"):
            shutil.rmtree(config.connection.workspace+"/MavensMateUnitTestProject")
        temp_client = MavensMateClient(credentials={"username":self.username, "password":self.password})
        if self.RunInitialDelete:
            helper.delete_metadata(
                temp_client, 
                {
                    'ApexClass'     :   ['apex_class_from_unit_test_123'], 
                    'ApexTrigger'   :   ['apex_trigger_from_unit_test_123'], 
                    'ApexPage'      :   ['apex_page_from_unit_test_123'], 
                    'ApexComponent' :   ['apex_component_from_unit_test_123']
                }
            )
            self.__class__.RunInitialDelete = False

    def test_index_project(self):
        config.connection.new_project

    def test_clean_project(self):
        config.connection.new_project(params={
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        },action='new')
        config.connection.project.clean()
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"))
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"+"/config"))
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"+"/src"))
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"+"/src/classes"))
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"+"/src/components"))
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"+"/src/objects"))
        self.assertTrue(os.path.isdir(config.connection.workspace+"/MavensMateUnitTestProject"+"/src/pages"))
        self.assertTrue(os.path.isfile(config.connection.workspace+"/MavensMateUnitTestProject"+"/src/package.xml"))

    def test_create_new_apex_class(self):
        config.connection.new_project(params={
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        },action='new')
        deploy_result = config.connection.project.new_metadata(
            api_name            = 'apex_class_from_unit_test_123',
            apex_class_type     = 'default',
            metadata_type       = 'ApexClass'
        )
        print deploy_result
        self.assertTrue(deploy_result.success == True)
        helper.delete_metadata(config.connection.project.sfdc_client, {'ApexClass':['apex_class_from_unit_test_123']})

    def test_compile_project(self):
        config.connection.new_project(params={
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        },action='new')
        deploy_result = config.connection.project.compile()
        print deploy_result
        self.assertTrue(deploy_result.success == True)

    def test_create_new_apex_trigger(self):
        config.connection.new_project(params={
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        },action='new')
        deploy_result = config.connection.project.new_metadata(
            api_name                        = 'apex_trigger_from_unit_test_123',
            metadata_type                   = 'ApexTrigger',
            apex_trigger_object_api_name    = 'Account'
        )
        print deploy_result
        self.assertTrue(deploy_result.success == True)
        helper.delete_metadata(config.connection.project.sfdc_client, {'ApexTrigger':['apex_trigger_from_unit_test_123']})

    def test_create_new_apex_page(self):
        config.connection.new_project(params={
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        },action='new')
        deploy_result = config.connection.project.new_metadata(
            api_name                        = 'apex_page_from_unit_test_123',
            metadata_type                   = 'ApexPage'
        )
        print deploy_result
        self.assertTrue(deploy_result.success == True)
        helper.delete_metadata(config.connection.project.sfdc_client, {'ApexPage':['apex_page_from_unit_test_123']})

    def test_create_new_apex_component(self):
        config.connection.new_project(params={
            "project_name"    : self.project_name,
            "username"        : self.username,
            "password"        : self.password,
            "org_type"        : self.org_type,
            "package"         : config.base_path+'/test/resources/package.xml' #=> this should be a dict of package contents or the location of a package.xml
        },action='new')
        deploy_result = config.connection.project.new_metadata(
            api_name                        = 'apex_component_from_unit_test_123',
            metadata_type                   = 'ApexComponent'
        )
        print deploy_result
        self.assertTrue(deploy_result.success == True)
        helper.delete_metadata(config.connection.project.sfdc_client, {'ApexComponent':['apex_component_from_unit_test_123']})

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