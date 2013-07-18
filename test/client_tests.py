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
import test_helper as helper
from lib.mm_client import MavensMateClient

class TestClientOperations(unittest.TestCase):

    # FYI: overriding this constructor is apparently not recommended, so we should find a better way to init test data
    def __init__(self, *args, **kwargs): 
        super(TestClientOperations, self).__init__(*args, **kwargs) 
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

    def test_describe(self):
        print self.client.describeMetadata(retXml=False)

    def test_bad_login(self):
        try:
            self.client = MavensMateClient(credentials={"username":self.username, "password":"a_bad_password"}) 
        except BaseException, e:
            self.assertTrue(e.message == 'Server raised fault: \'INVALID_LOGIN: Invalid username, password, security token; or user locked out.\'')

    def test_list_complex_metadata(self):
        list_result = self.client.list_metadata('CustomObject')
        print list_result

    def test_login(self):
        self.assertTrue(self.client.sid != '')
        self.assertTrue(self.client.user_id != '')
        self.assertTrue(self.client.metadata_server_url != '')
        self.assertTrue(self.client.endpoint != '')
        self.assertTrue(self.client.is_connection_alive() == True)
        self.assertTrue(len(self.client.describeMetadata(retXml=False).metadataObjects) > 1)

    def test_compile_apex(self):        
        print '>>> attempting bad compile of apex class'
        compile_result = self.client.compile_apex('class', 'public this_wont_compile { }')
        self.assertTrue(compile_result.success == False)
        
        print '>>> attempting good compile of apex class'
        compile_result = self.client.compile_apex('class', 'public class this_will_compile { }')
        self.assertTrue(compile_result.success == True)
        
        print '>>> attempting bad compile of apex trigger'
        compile_result = self.client.compile_apex('trigger', 'trigger mavensmate_test_trigger on Accounttt (before insert) { }')
        self.assertTrue(compile_result.success == False)

        print '>>> attempting good compile of apex trigger'
        compile_result = self.client.compile_apex('trigger', 'trigger mavensmate_test_trigger on Account (before insert) { }')
        self.assertTrue(compile_result.success == True)

        trigger_id = self.client.get_apex_entity_id_by_name(object_type="ApexTrigger", name="mavensmate_test_trigger")
        self.assertTrue(len(trigger_id) == 18)

        helper.delete_metadata(self.client, {'ApexClass':['this_will_compile'], 'ApexTrigger':['mavensmate_test_trigger']})

    def test_retrieve(self):
        print '>>> attempting to retrieve some metadata'
        #print '>>>>>>>>>>> ' + os.path.dirname(os.path.realpath(__file__))
        retrieve_result = self.client.retrieve(package=os.path.dirname(os.path.realpath(__file__))+'/resources/retrieve_package.xml')
        self.assertTrue(retrieve_result.fileProperties[0].type == 'CustomObject')
        self.assertTrue(retrieve_result.fileProperties[1].type == 'Package')

    def test_retrieve_specific_metadata_type(self):
        print '>>> attempting to retrieve specific type of metadata from a package.xml'
        retrieve_result = self.client.retrieve(package=os.path.dirname(os.path.realpath(__file__))+'/resources/package.xml',type="ApexClass")
        self.assertTrue(retrieve_result.fileProperties[0].type == 'ApexClass')

    def test_run_apex_tests(self):
        print '>>> attempting to run single apex test'
        test_result = self.client.run_tests(classes=['MultiselectControllerTest'])
        self.assertTrue(test_result.numTestsRun == 1)

    def test_server_dupe_check(self):
        self.assertFalse(self.client.does_metadata_exist(object_type="ApexClass", name="this_wont_be_found"))
        compile_result = self.client.compile_apex('class', 'public class this_will_compile { }')
        self.assertTrue(compile_result.success == True)
        self.assertTrue(self.client.does_metadata_exist(object_type="ApexClass", name="this_will_compile"))
        helper.delete_metadata(self.client, {'ApexClass':['this_will_compile']})

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()