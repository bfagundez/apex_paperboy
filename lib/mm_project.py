import datetime
import re
import string
import sys
import unittest
import traceback
import json
import os
import yaml
import logging
import mm_util
import config
import shutil
import distutils
import xmltodict
import threading
import time
import collections
import webbrowser
import tempfile
import subprocess
import traceback

from xml.dom import minidom
from mm_exceptions import MMException
from operator import itemgetter
from mm_client import MavensMateClient
sys.path.append('../')

class MavensMateProject(object):

    def __init__(self, params={}, **kwargs):
        params = dict(params.items() + kwargs.items())

        self.sfdc_session       = None
        self.id                 = params.get('id', None)
        self.project_name       = params.get('project_name', None)
        self.username           = params.get('username', None)
        self.password           = params.get('password', None)
        self.org_type           = params.get('org_type', None)
        self.package            = params.get('package', None)
        self.ui                 = params.get('ui', False)
        self.directory          = params.get('directory', False)
        self.sfdc_client        = None
        self.defer_connection   = params.get('defer_connection', False)

        if 'location' in params and os.path.exists(params['location']): #=> existing project on the disk
            
            self.location                   = params.get('location', None)
            self.settings                   = self.__get_settings()
            self.project_name               = self.settings.get('project_name', os.path.basename(self.location))
            self.sfdc_session               = self.__get_sfdc_session()
            self.package                    = os.path.join(self.location,"src","package.xml")
            self.apex_file_properties_path  = os.path.join(self.location,"config",".apex_file_properties")
            self.is_metadata_indexed        = self.get_is_metadata_indexed()

            config.logger.debug(self.sfdc_session)
            config.logger.debug(self.get_creds())

            if self.ui == False and self.defer_connection == False:
                self.sfdc_client        = MavensMateClient(credentials=self.get_creds())

                if self.sfdc_session != None and 'sid' in self.sfdc_session and self.sfdc_client != None and (self.sfdc_session['sid'] != self.sfdc_client.sid): 
                    config.logger.debug('storing updated session information locally')
                    self.__set_sfdc_session()
                elif self.sfdc_session == None:
                    config.logger.debug('storing new session information locally')
                    self.__set_sfdc_session()
                elif 'server_url' not in self.sfdc_session:
                    config.logger.debug('storing new session information locally because of missing server_url')
                    self.__set_sfdc_session()
                elif self.sfdc_client.reset_creds == True:
                    config.logger.debug('storing new session information locally because reset_creds')
                    self.__set_sfdc_session()

        elif 'location' in params and not os.path.exists(params['location']):
            raise MMException('Project not found in your workspace')

    #used to create a new project in a workspace
    def retrieve_and_write_to_disk(self,action='new'):
        try:
            if os.path.isdir(os.path.join(config.connection.workspace,self.project_name)) and action == 'new':
                return mm_util.generate_error_response("A project with this name already exists in your workspace.")
            
            if action == 'existing':
                existing_parent_directory = os.path.dirname(self.directory)
                existing_is_in_workspace = True
                if existing_parent_directory != config.connection.workspace:
                    existing_is_in_workspace = False
                if os.path.isdir(os.path.join(config.connection.workspace,self.project_name)) and existing_is_in_workspace == False and action == 'existing':
                    raise MMException("A project with this name already exists in your workspace.")   

            self.sfdc_client = MavensMateClient(credentials={"username":self.username,"password":self.password,"org_type":self.org_type})             
            self.id = mm_util.new_mavensmate_id()
            if action == 'new':
                project_metadata = self.sfdc_client.retrieve(package=self.package)
                mm_util.put_project_directory_on_disk(self.project_name, force=True)
                mm_util.extract_base64_encoded_zip(project_metadata.zipFile, config.connection.workspace+"/"+self.project_name)
                mm_util.rename_directory(os.path.join(config.connection.workspace,self.project_name,"unpackaged"), os.path.join(config.connection.workspace,self.project_name,"src"))
            elif action == 'existing' and existing_is_in_workspace == False:
                shutil.move(self.directory, config.connection.workspace)

            self.location = os.path.join(config.connection.workspace,self.project_name)
            self.__put_project_file()
            self.__put_base_config()
            self.__set_sfdc_session()
            mm_util.put_password_by_key(self.id, self.password)
            self.sfdc_session = self.__get_sfdc_session() #hacky...need to fix
            if action == 'new':
                return mm_util.generate_success_response("Project Retrieved and Created Successfully")
            else:
                return mm_util.generate_success_response("Project Created Successfully")
        except Exception, e:
            return mm_util.generate_error_response(e.message)

    #updates the salesforce.com credentials associated with the project
    def update_credentials(self):
        self.sfdc_client = MavensMateClient(credentials={"username":self.username,"password":self.password,"org_type":self.org_type}, override_session=True)              
        self.id = self.settings['id']
        self.username = self.username
        self.environment = self.org_type
        mm_util.put_password_by_key(self.id, self.password)
        self.__put_base_config()
        self.__set_sfdc_session()

    #upgrades project from the legacy format to 2.0+format
    def upgrade(self):
        try:
            self.sfdc_client = MavensMateClient(credentials={"username":self.username,"password":self.password,"org_type":self.org_type})             
            self.id = mm_util.new_mavensmate_id()
            self.__put_project_file()
            self.__put_base_config()
            self.__set_sfdc_session()
            mm_util.put_password_by_key(self.id, self.password)
            self.sfdc_session = self.__get_sfdc_session() #hacky...need to fix
            if os.path.exists(os.path.join(self.location,"config","settings.yaml")):
                os.remove(os.path.join(self.location,"config","settings.yaml"))
            if os.path.exists(os.path.join(self.location,"config",".org_metadata")):
                os.remove(os.path.join(self.location,"config",".org_metadata"))
            return mm_util.generate_success_response("Project Upgraded Successfully")
        except Exception, e:
            #print traceback.print_exc()
            return mm_util.generate_error_response(e.message)

    #creates a new piece of metadata
    def new_metadata(self, params):
        try:
            metadata_type                   = params.get('metadata_type', None)
            api_name                        = params.get('api_name', None)
            apex_class_type                 = params.get('apex_class_type', None)
            apex_trigger_object_api_name    = params.get('apex_trigger_object_api_name', None)

            if metadata_type == 'ApexClass' and apex_class_type == None:
                apex_class_type = 'default'

            if api_name == None:
                return mm_util.generate_error_response("You must provide a name for the new metadata.")

            if self.sfdc_client.does_metadata_exist(object_type=metadata_type, name=api_name) == True:
                mt = mm_util.get_meta_type_by_name(metadata_type)
                filepath = os.path.join(self.location, 'src', mt['directoryName'], api_name+'.'+mt['suffix'])
                fetched = ""
                if not os.path.exists(filepath):
                    params['files'] = [filepath]
                    self.refresh_selected_metadata(params)
                    fetched = ", fetched metadata file from server"
                return mm_util.generate_error_response("This API name is already in use in your org" + fetched + ".")      

            tmp, tmp_unpackaged = mm_util.put_tmp_directory_on_disk(True)
            mm_util.put_skeleton_files_on_disk(metadata_type, api_name, tmp_unpackaged, apex_class_type, apex_trigger_object_api_name)
            package_xml_body = mm_util.get_package_xml_contents({metadata_type : [ api_name ]})
            mm_util.put_package_xml_in_directory(tmp_unpackaged, package_xml_body)
            zip_file = mm_util.zip_directory(tmp, tmp)
            deploy_params = {
                "zip_file"          : zip_file,
                "rollback_on_error" : True,
                "ret_xml"           : True
            }
            deploy_result = self.sfdc_client.deploy(deploy_params)
            d = xmltodict.parse(deploy_result,postprocessor=mm_util.xmltodict_postprocessor)
            meta_dir = ""
            params['files'] = []
            path = None
            for dirname, dirnames, filenames in os.walk(tmp_unpackaged):
                for filename in filenames:
                    if 'package.xml' in filename:
                        continue
                    full_file_path = os.path.join(dirname, filename)
                    extension = filename.split(".")[-1]
                    mt = mm_util.get_meta_type_by_suffix(extension)
                    if mt != None: 
                        meta_dir = mt['directoryName']
                        path = os.path.join(self.location, 'src', meta_dir)
                        if not os.path.exists(path):
                            os.makedirs(path)
                        params['files'].append(os.path.join(path, filename))
                    elif extension != "xml":
                        continue;
                    # only apex files and meta.xml files should make it to here
                    shutil.copy(full_file_path, path)
            shutil.rmtree(tmp)
            
            self.__update_package_xml_with_metadata(metadata_type, api_name)
            self.refresh_selected_properties(params)

            return json.dumps(d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result'])
        except BaseException, e:
            return mm_util.generate_error_response(e.message)

    def __update_package_xml_with_metadata(self, metadata_type, api_name, operation='insert'):
        supported_types = ['ApexClass', 'ApexTrigger', 'ApexComponent', 'ApexPage']
        if metadata_type not in supported_types:
            return
        package_types = self.get_package_types()
        for i, val in enumerate(package_types):
            if val['name'] == metadata_type:
                if val['members'] == '*':
                    pass #we don't need to add/remove here
                else:
                    if operation == 'insert' and api_name not in val['members']:
                        if type(val['members']) is not list:
                            val['members'] = [val['members']]
                        val['members'].append(api_name)
                        val['members'] = sorted(val['members'])
                    elif operation == 'delete' and api_name in val['members']:
                        if type(val['members']) is not list:
                            val['members'] = [val['members']]
                        val['members'].pop(api_name)
                        if type(val['members']) is list:
                            val['members'] = sorted(val['members'])
                        else:
                            val['members'] = ""

        metadata_hash = collections.OrderedDict()
        for val in package_types:
            if val['members'] == "*" or type(val['members']) is list:
                metadata_hash[val['name']] = val['members']
            else:
                metadata_hash[val['name']] = [val['members']]

        new_package_xml_contents = mm_util.get_package_xml_contents(metadata_hash)
        existing_package_xml = open(self.location+"/src/package.xml", "w")
        existing_package_xml.write(new_package_xml_contents)
        existing_package_xml.close()

    #compiles the entire project
    def compile(self):
        try:
            tmp = mm_util.put_tmp_directory_on_disk()
            shutil.copytree(self.location+"/src", tmp+"/src")
            mm_util.rename_directory(tmp+"/src", tmp+"/unpackaged")
            zip_file = mm_util.zip_directory(tmp, tmp)
            mm_compile_rollback_on_error = config.connection.get_plugin_client_setting("mm_compile_rollback_on_error", False)
            deploy_params = {
                "zip_file"          : zip_file,
                "rollback_on_error" : mm_compile_rollback_on_error,
                "ret_xml"           : True
            }
            deploy_result = self.sfdc_client.deploy(deploy_params)
            d = xmltodict.parse(deploy_result,postprocessor=mm_util.xmltodict_postprocessor)

            dictionary = collections.OrderedDict()
            dictionary2 = []

            result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']
            
            for x, y in result.iteritems():
                if(x == "id"):
                    dictionary["id"] = y
                if(x == "runTestResult"):
                    dictionary["runTestResult"] = y
                if(x == "success"):
                    dictionary["success"] = y
            for a in result['messages']:
                for key, value in a.iteritems():
                    if(key == 'problemType' and value == 'Error'):
                        dictionary2.append(a)
            dictionary["Messages"] = dictionary2 

            shutil.rmtree(tmp)

            self.refresh_selected_properties({'project_name':self.project_name, 'directories': [os.path.join(self.location, 'src')]})

            return json.dumps(dictionary, sort_keys=True, indent=2, separators=(',', ': '))
            #return json.dumps(d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result'], sort_keys=True, indent=2, separators=(',', ': '))
        except BaseException, e:
            try:
                shutil.rmtree(tmp)
            except:
                pass
            return mm_util.generate_error_response(e.message)

    def synchronize_selected_metadata(self, params):
        files = params.get('files', None)
        directories = params.get('directories', None)

        if len(files)==1:
            projectpath = files[0]
            destination = tempfile.mktemp()
        elif len(directories)==1:
            projectpath = directories[0]
            destination = tempfile.mkdtemp()
        else:
            return mm_util.generate_error_response("You may only synchronize one file or at a time");
            
        diffmerge = "/Applications/DiffMerge.app/Contents/Resources/diffmerge.sh"
        if not os.path.exists(diffmerge):
            return mm_util.generate_error_response("You must have DiffMerge installed to synchronize.");

        retrieve_result = self.get_retrieve_result(params)
        mm_util.extract_base64_encoded_zip(retrieve_result.zipFile, self.location)
       
        # get metadata and copy to temp file or folder as necessary
        for dirname, dirnames, filenames in os.walk(self.location+"/unpackaged"):
            for filename in filenames:
                full_file_path = os.path.join(dirname, filename)
                if '/unpackaged/package.xml' in full_file_path:
                    continue

                current_destination = destination
                if os.path.basename(projectpath) == 'src':
                    subdir = full_file_path.split('/')[-2]
                    current_destination = os.path.join(destination, subdir)
                    if not os.path.exists(current_destination):
                        os.makedirs(current_destination)
                elif len(files)==1 and '-meta.xml' in full_file_path:
                    continue

                shutil.move(full_file_path, current_destination)
                projectfile = full_file_path.replace('/unpackaged', '/src')

        shutil.rmtree(os.path.join(self.location,"unpackaged"))

        #compare retrieved metadata to local metadata
        p = subprocess.Popen([diffmerge, destination, projectpath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return mm_util.generate_success_response("Launched diff tool")

    #compiles metadata
    def compile_selected_metadata(self, params):        
        files = params.get('files', None)

        use_tooling_api = config.connection.get_plugin_client_setting('mm_compile_with_tooling_api', False)
        
        if use_tooling_api == True:
            if 'metadata_container' not in self.settings:
                container_id = self.sfdc_client.get_metadata_container_id()
                new_settings = self.settings
                new_settings['metadata_container'] = container_id
                self.__put_settings_file(new_settings)
            else:
                container_id = self.settings['metadata_container']
            
            file_ext = files[0].split('.')[-1]

            #use tooling api here, if possible
            if len(files) == 1 and file_ext in mm_util.TOOLING_API_EXTENSIONS:
                result = self.sfdc_client.compile_with_tooling_api(files[0], container_id)
                if 'Id' in result and 'State' in result:
                    return mm_util.generate_response(result)

        try:
            #this first try goes to the apex api
            try:
                #when compiling a single class, check to see if it is newer on the server
                # if len(files) == 1 and config.connection.get_plugin_client_setting('mm_compile_check_conflicts', False) == True:
                #     if 'override' not in params or params['override'] == False:
                #         apex_file_properties = self.get_apex_file_properties();
                #         filename = os.path.basename(files[0])

                #         error_result = {
                #             'success': False,
                #             'line': '0',
                #             'column': '0',
                #             'conflict' : True
                #         }

                #         if filename not in apex_file_properties:
                #             error_result['problem'] = "Uh oh, could not find property for " + filename + ". Please refresh this file or its Apex properties from the server."
                #             return json.dumps(error_result)
                       
                #         retrieve_result = self.get_retrieve_result(params)
                #         for props in retrieve_result.fileProperties:
                #             if props.type != 'Package':
                #                 if filename in apex_file_properties:
                #                     if 'lastModifiedDate' in apex_file_properties[filename]:
                #                         lastModifiedDate = apex_file_properties[filename]['lastModifiedDate']
                #                     else:
                #                         lastModifiedDate = ''

                #                     if lastModifiedDate != str(props.lastModifiedDate):
                #                         error_result['problem'] = "Uh oh, " + props.lastModifiedByName + " changed this file on " + str(props.lastModifiedDate) + " and you last refreshed it on " + lastModifiedDate
                #                         return json.dumps(error_result)

                #no conflicts, compile
                if len(files) == 1 and (files[0].split('.')[-1] == 'trigger' or files[0].split('.')[-1] == 'cls'):
                    file_path = files[0]
                    file_ext = file_path.split('.')[-1]
                    metadata_type = mm_util.get_meta_type_by_suffix(file_ext)
                    f = open(file_path, "r")
                    file_body = f.read()
                    f.close()
                    file_body = file_body.decode("utf-8")
                    result = self.sfdc_client.compile_apex(metadata_type['xmlName'], file_body, retXml=True)
                    d = xmltodict.parse(result,postprocessor=mm_util.xmltodict_postprocessor)
                    body = d["soapenv:Envelope"]["soapenv:Body"]
                    # print(d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']['changed'])
                    if file_ext == 'trigger':
                        result = body["compileTriggersResponse"]["result"]
                    else:
                        result = body["compileClassesResponse"]["result"]

                    # Get new properties for the files we just compiled
                    if result['success'] == True:
                        self.refresh_selected_properties(params)

                    return json.dumps(result)
            except UnicodeDecodeError:
                #decode error, let's use the metadata api
                pass

            for f in files:
                if '-meta.xml' in f:
                    corresponding_file = f.split('-meta.xml')[0]
                    if corresponding_file not in files:
                        files.append(corresponding_file)
            for f in files:
                if '-meta.xml' in f:
                    continue
                file_ext = f.split('.')[-1]
                metadata_type = mm_util.get_meta_type_by_suffix(file_ext)
                if metadata_type != None and 'metaFile' in metadata_type and metadata_type['metaFile'] == True:
                    corresponding_file = f + '-meta.xml'
                    if corresponding_file not in files:
                        files.append(corresponding_file)

            metadata_package_dict = mm_util.get_metadata_hash(files)
            tmp = mm_util.put_tmp_directory_on_disk()
            os.makedirs(tmp+"/unpackaged")
            #copy files from project directory to tmp
            for full_file_path in files:
                if '/package.xml' in full_file_path:
                    continue
                destination = tmp + '/unpackaged/' + full_file_path.split('/src/')[1]
                destination_directory = os.path.dirname(destination)
                if not os.path.exists(destination_directory):
                    os.makedirs(destination_directory)
                shutil.copy2(full_file_path, destination_directory)

            package_xml = mm_util.get_package_xml_contents(metadata_package_dict)
            mm_util.put_package_xml_in_directory(tmp+"/unpackaged", package_xml)
            zip_file = mm_util.zip_directory(tmp, tmp)
            deploy_params = {
                "zip_file"          : zip_file,
                "rollback_on_error" : True,
                "ret_xml"           : True
            }
            deploy_result = self.sfdc_client.deploy(deploy_params)

            d = xmltodict.parse(deploy_result,postprocessor=mm_util.xmltodict_postprocessor)
            result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']
            shutil.rmtree(tmp)

            # Get new properties for the files we just compiled
            if result['success'] == True:
                self.refresh_selected_properties(params)

            return json.dumps(result)

        except Exception, e:
            try:
                shutil.rmtree(tmp)
            except:
                pass
            return mm_util.generate_error_response(e.message)

    #deletes metadata
    def delete_selected_metadata(self, params):
        try:
            files = params.get('files', None)
            for f in files:
                if '-meta.xml' in f:
                    corresponding_file = f.split('-meta.xml')[0]
                    if corresponding_file not in files:
                        files.append(corresponding_file)
            for f in files:
                if '-meta.xml' in f:
                    continue
                file_ext = f.split('.')[-1]
                metadata_type = mm_util.get_meta_type_by_suffix(file_ext)
                if metadata_type['metaFile'] == True:
                    corresponding_file = f + '-meta.xml'
                    if corresponding_file not in files:
                        files.append(corresponding_file)

            metadata_package_dict = mm_util.get_metadata_hash(files)
            tmp, tmp_unpackaged = mm_util.put_tmp_directory_on_disk(True)
            package_xml = mm_util.get_package_xml_contents(metadata_package_dict)
            mm_util.put_package_xml_in_directory(tmp_unpackaged, package_xml, True)
            empty_package_xml = mm_util.get_empty_package_xml_contents()
            mm_util.put_empty_package_xml_in_directory(tmp_unpackaged, empty_package_xml)
            zip_file = mm_util.zip_directory(tmp, tmp)
            deploy_params = {
                "zip_file"          : zip_file,
                "rollback_on_error" : True,
                "ret_xml"           : True
            }
            delete_result = self.sfdc_client.delete(deploy_params)
            d = xmltodict.parse(delete_result,postprocessor=mm_util.xmltodict_postprocessor)
            shutil.rmtree(tmp)
            result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']
            if result['success'] == True:
                removed = []
                for f in files:
                    try:
                        file_ext = f.split('.')[-1]
                        metadata_type = mm_util.get_meta_type_by_suffix(file_ext)
                        if metadata_type == None or not 'directoryName' in metadata_type:
                            continue;
                        directory = metadata_type['directoryName']
                        filepath = os.path.join(config.connection.project_location, "src", directory, f)
                        metapath = os.path.join(config.connection.project_location, "src", directory, f + '-meta.xml')
                        os.remove(filepath)
                        os.remove(metapath)
                        # remove the entry in file properties
                        self.remove_apex_file_property(f)
                        removed.append(f)
                    except Exception, e:
                        print e.message
                return mm_util.generate_success_response("Removed metadata files: " + (",".join(removed)))
            else:
                return json.dumps(result)
        except Exception, e:
            return mm_util.generate_error_response(e.message)

    #edits the contents of the project based on a package definition
    def edit(self, params):
        try:
            if 'package' not in params:
                raise MMException('"package" definition required in JSON body')
            self.package = params['package']

            if 'CustomObject' in self.package:
                custom_fields = []
                for member in self.package['CustomObject']:
                    if member == "*" or not member.endswith("__c"):
                        for item in self.get_org_metadata():
                           if item['xmlName'] == 'CustomObject':
                                for child in item['children']:
                                    if (member == "*" and not child['key'].endswith("__c")) or child['key'] == member:
                                        for props in child['children']:
                                            if props['key'] == 'fields':
                                                for field in props['children']:
                                                    custom_fields.append(child['key']+'.'+field['key'])
                                                break
                                        if member != "*":
                                            break
                                break

                if len(custom_fields):
                    if 'CustomField' not in self.package:
                        self.package['CustomField'] = []
                    self.package['CustomField'] = list(set(self.package['CustomField']+custom_fields))

            clean_result = json.loads(self.clean(overwrite_package_xml=True))
            if clean_result['success'] == True:
                return mm_util.generate_success_response('Project Edited Successfully')
            else:
                return mm_util.generate_error_response(clean_result['body'])
        except Exception as e:
            return mm_util.generate_error_response(e.message)

    #reverts a project to the server state based on the existing package.xml
    def clean(self, **kwargs):
        try:
            if self.sfdc_client == None or self.sfdc_client.is_connection_alive() == False:
                self.sfdc_client = MavensMateClient(credentials=self.get_creds(), override_session=True)  
                self.__set_sfdc_session()
            
            #TESTING: moving to tmp directory in case something goes wrong during clean
            # tmp = mm_util.put_tmp_directory_on_disk()
            # shutil.copytree(self.location, tmp)

            project_metadata = self.sfdc_client.retrieve(package=self.package)
            mm_util.extract_base64_encoded_zip(project_metadata.zipFile, self.location)

            #removes all metadata from directories
            for dirname, dirnames, filenames in os.walk(self.location+"/src"):
                if '.git' in dirnames:
                    dirnames.remove('.git')
                if '.svn' in dirnames:
                    dirnames.remove('.svn')

                for filename in filenames:
                    full_file_path = os.path.join(dirname, filename)
                    if '/src/package.xml' not in full_file_path:
                        os.remove(full_file_path)

            #replaces with retrieved metadata
            for dirname, dirnames, filenames in os.walk(self.location+"/unpackaged"):
                for filename in filenames:
                    full_file_path = os.path.join(dirname, filename)
                    if '/unpackaged/package.xml' in full_file_path:
                        continue
                    destination = full_file_path.replace('/unpackaged/', '/src/')
                    destination_directory = os.path.dirname(destination)
                    if not os.path.exists(destination_directory):
                        os.makedirs(destination_directory)
                    shutil.move(full_file_path, destination)
           
            #remove empty directories
            for dirname, dirnames, filenames in os.walk(self.location+"/src"):
                if dirname == self.location+"/src":
                    continue
                files = os.listdir(dirname)
                if len(files) == 0:
                    os.rmdir(dirname) 
                    

            if 'overwrite_package_xml' in kwargs and kwargs['overwrite_package_xml'] == True:
                os.remove(self.location+"/src/package.xml")
                shutil.move(self.location+"/unpackaged/package.xml", self.location+"/src")
            shutil.rmtree(self.location+"/unpackaged")
            return mm_util.generate_success_response('Project Cleaned Successfully')
        except Exception, e:
            #TODO: if the clean fails, we need to have a way to ensure the project is returned to its original state
            #maybe we copy the project tree to a tmp folder, if we encounter an exception, we can remove the project
            #and replace it with the copied one in tmp
            #raise e
            return mm_util.generate_error_response(e.message)

    def get_retrieve_result(self, params):

        if self.sfdc_client == None or self.sfdc_client.is_connection_alive() == False:
            self.sfdc_client = MavensMateClient(credentials=self.get_creds(), override_session=True)  
        
        if 'directories' in params and len(params['directories']) > 0 and 'files' in params and len(params['files']) > 0:
            raise MMException("Please select either directories or files to refresh, not both")
        elif 'directories' in params and len(params['directories']) > 0:
            metadata = {}
            types = []
            for d in params['directories']:
                basename = os.path.basename(d)
                # refresh all if it's the project base or src directory
                if basename == config.connection.project_name or basename == "src":
                    data = mm_util.get_default_metadata_data();
                    for item in data["metadataObjects"]: 
                        if 'directoryName' in item:
                            types.append(item['xmlName'])
                else:
                    metadata_type = mm_util.get_meta_type_by_dir(basename)
                    if metadata_type:
                        types.append(metadata_type['xmlName'])
                        if 'childXmlNames' in metadata_type:
                            for child in metadata_type['childXmlNames']:
                                types.append(child)
          
            custom_fields = []
            for val in self.get_package_types():
                package_type = val['name']
                members = val['members']
                if package_type not in types:
                    continue;

                metadata[package_type] = members

                if package_type == 'CustomObject':
                    for member in members:
                        if members == "*":
                            for item in self.get_org_metadata():
                               if item['xmlName'] == 'CustomObject':
                                    for child in item['children']:
                                        if not child['key'].endswith("__c"):
                                            for props in child['children']:
                                                if props['key'] == 'fields':
                                                    for field in props['children']:
                                                        custom_fields.append(child['key']+'.'+field['key'])
                                                    break
                                            if member != "*":
                                                break
                                    break

                    if len(custom_fields):
                        if 'CustomField' not in metadata:
                            metadata['CustomField'] = []
                        metadata['CustomField'] = list(set(metadata['CustomField']+custom_fields))

            if len(metadata) == 0:
                raise MMException("Could not find metadata types to refresh")
        elif 'files' in params and len(params['files']) > 0:
            metadata = mm_util.get_metadata_hash(params['files'])
        else:
            raise MMException("Please provide either an array of 'directories' or an array of 'files'")

        #retrieves a fresh set of metadata based on the files that have been requested
        retrieve_result = self.sfdc_client.retrieve(package=metadata)
        return retrieve_result

    def refresh_selected_properties(self, params):
        retrieve_result = self.get_retrieve_result(params)
        #take this opportunity to freshen the cache
        self.cache_apex_file_properties(retrieve_result.fileProperties)

    #refreshes file(s) from the server
    def refresh_selected_metadata(self, params):
        try:
            retrieve_result = self.get_retrieve_result(params)
            #take this opportunity to freshen the cache
            self.cache_apex_file_properties(retrieve_result.fileProperties)
            mm_util.extract_base64_encoded_zip(retrieve_result.zipFile, self.location)

            #TODO: handle exception that could render the project unusable bc of lost files
            #replace project metadata with retrieved metadata
            for dirname, dirnames, filenames in os.walk(self.location+"/unpackaged"):
                for filename in filenames:
                    full_file_path = os.path.join(dirname, filename)
                    if '/unpackaged/package.xml' in full_file_path:
                        continue
                    destination = full_file_path.replace('/unpackaged/', '/src/')
                    destination_directory = os.path.dirname(destination)
                    if not os.path.exists(destination_directory):
                        os.makedirs(destination_directory)
                    shutil.move(full_file_path, destination)
            shutil.rmtree(self.location+"/unpackaged")
            return mm_util.generate_success_response("Refresh Completed Successfully")
        except Exception, e:
            return mm_util.generate_error_response(e.message)

    def index_apex_file_properties(self):
        directories = []
        if os.path.exists(os.path.join(self.location, 'src', 'classes')):
            directories.append(os.path.join(self.location, 'src', 'classes'))

        if os.path.exists(os.path.join(self.location, 'src', 'triggers')):
            directories.append(os.path.join(self.location, 'src', 'triggers'))

        params = {
            'files'         : [],
            'directories'   : directories
        }
        retrieve_result = self.get_retrieve_result(params)
        apex_file_properties = self.cache_apex_file_properties(retrieve_result.fileProperties, False)
        apex_ids = []
        for p in apex_file_properties.keys():
            apex_ids.append(apex_file_properties[p]["id"])
        symbol_table_result = self.sfdc_client.get_symbol_table(apex_ids)

        if 'records' in symbol_table_result and len(symbol_table_result['records']) > 0:
            for r in symbol_table_result['records']:
                for p in apex_file_properties.keys():
                    if r["ContentEntityId"] == apex_file_properties[p]["id"]:
                        apex_file_properties[p]["symbolTable"] = r["SymbolTable"]
                        break

        self.write_apex_file_properties(apex_file_properties)
        return mm_util.generate_success_response("Apex file properties cached successfully")

    def get_apex_file_properties(self):
        apex_file_properties = None
        try:
            apex_file_properties = mm_util.parse_json_from_file(self.apex_file_properties_path)
        except:
            pass
        if apex_file_properties == None:
            apex_file_properties = {}
        return apex_file_properties

    def remove_apex_file_property(self, apex_file):
        props = self.get_apex_file_properties();
        if apex_file in props:
            del props[apex_file]
        self.write_apex_file_properties(props)    
        
    def cache_apex_file_properties(self, properties, write=True):
        if not len(properties):
            return;
        
        apex_file_properties = self.get_apex_file_properties()

        for prop in properties:
            if prop.type != "Package":
                filename = prop.fileName.split('/')[-1];
                fileprop = {
                    'createdById': prop.createdById,
                    'createdByName': prop.createdByName,
                    'createdDate': str(prop.createdDate),
                    'fileName': prop.fileName,
                    'fullName': prop.fullName,
                    'id': prop.id,
                    'lastModifiedById': prop.lastModifiedById,
                    'lastModifiedByName': prop.lastModifiedByName,
                    'lastModifiedDate': str(prop.lastModifiedDate),
                    'type': prop.type
                }
                if 'manageableState' in prop:
                    fileprop['manageableState'] = prop.manageableState
                apex_file_properties[filename] = fileprop
        if write:
            self.write_apex_file_properties(apex_file_properties)
        return apex_file_properties

    def write_apex_file_properties(self, json_data):
        src = open(self.apex_file_properties_path, "w")
        json_data = json.dumps(json_data, sort_keys=True, indent=4)
        src.write(json_data)
        src.close()

    # Open selected file on SFDC
    def open_selected_metadata(self, params):
        try:
            if "files" in params:
                if "type" in params: 
                    open_type = params.get("type", None) 
                else:
                    open_type = "edit"
                files = params.get("files", None)
                if len(files) > 0:
                    apex_file_properties = self.get_apex_file_properties()
                    opened = []
                    for fileabs in files:
                        basename = os.path.basename(fileabs)

                        if basename not in apex_file_properties: 
                            # make sure we have meta data and then get the object type
                            if os.path.isfile(fileabs+"-meta.xml"):
                                xmldoc = minidom.parse(fileabs+"-meta.xml")
                                root = xmldoc.firstChild
                                object_type = root.nodeName
                            else:
                                continue

                            object_id = self.sfdc_client.get_apex_entity_id_by_name(object_type=object_type, name=basename)
                            if not object_id: 
                                continue
                        else:
                            props = apex_file_properties[basename]
                            object_type = props['type']
                            object_id = props['id']

                        # only ApexClasses that are global and have webservice scope have WSDL files
                        if open_type == "wsdl":
                            if object_type != "ApexClass":
                                continue
                            with open(fileabs, 'r') as content_file:
                                content = content_file.read()
                                p = re.compile("global\s+class\s", re.I + re.M)
                                if not p.search(content):
                                    continue
                                p = re.compile("\swebservice\s", re.I + re.M)
                                if not p.search(content): 
                                    continue

                        # get the server instance url and set the redirect url
                        frontdoor = "https://" + self.sfdc_client.server_url.split('/')[2] + "/secur/frontdoor.jsp?sid=" + self.sfdc_client.sid + "&retURL="
                        if open_type == "wsdl":
                            f, e = os.path.splitext(basename)
                            ret_url = "/services/wsdl/class/" + f
                        else:
                            f, ext = os.path.splitext(basename)
                            if object_type == "CustomObject" and not f.endswith('__c'):
                                # standard object?
                                ret_url = "/p/setup/layout/LayoutFieldList?type=" + f + "%23CustomFieldRelatedList_target"                             
                            else:
                                ret_url = "/" + object_id

                        # open the browser window for this file and track it
                        webbrowser.open(frontdoor+ret_url, new=2)
                        opened.append(basename)
                    if len(opened) == 0:
                        return mm_util.generate_error_response("There were no valid files to open.")
                    return mm_util.generate_success_response("Opened "+(", ".join(opened))+" on server.")
                return mm_util.generate_error_response("Unable to open file on server.")
            else:
                raise MMException("To open on Salesforce, you must provide an array of 'files'")
        except Exception, e:
            print traceback.print_exc()
            return mm_util.generate_error_response(e.message)

    #executes a string of apex
    def execute_apex(self, params):
        try:
            execute_result = self.sfdc_client.execute_apex(params)
            result = {
                'column'                : execute_result['column'],
                'compileProblem'        : execute_result['compileProblem'],
                'compiled'              : execute_result['compiled'],
                'exceptionMessage'      : execute_result['exceptionMessage'],
                'exceptionStackTrace'   : execute_result['exceptionStackTrace'],
                'line'                  : execute_result['line'],
                'success'               : execute_result['success'],
            }
            if 'log' in execute_result:
                result['log'] = execute_result['log']
            if result['success']:
                log_apex = config.connection.get_plugin_client_setting('mm_log_anonymous_apex', False)
                if log_apex:
                    self.__log_anonymous_apex(params['body'])
            return mm_util.generate_response(result)
        except BaseException, e:
            return mm_util.generate_error_response(e.message)

    #executes 1 or more unit tests
    def run_unit_tests(self, params):
        try:
            api = params.get('api', 'apex')
            if api == 'apex':
                run_tests_result = self.sfdc_client.run_tests(params)
                if "soapenv:Envelope" in run_tests_result:
                    result = {}
                    result = run_tests_result["soapenv:Envelope"]["soapenv:Body"]["runTestsResponse"]["result"]
                    try:
                        result['log'] = run_tests_result["soapenv:Envelope"]["soapenv:Header"]["DebuggingInfo"]["debugLog"]
                    except:
                        pass
                    return result
                elif 'log' in run_tests_result:
                    run_tests_result['log'] = run_tests_result['log']
                    return mm_util.generate_response(run_tests_result)
            else:
                # payload = {
                #     'namespace' : params.get('namespace', None),
                #     'allTests'  : params.get('run_all_tests', False),
                #     'classes'   : params.get('classes', [])
                # }
                #deploy_metadata = self.sfdc_client.retrieve(package=params['package'])
                #TODO: empty zip here
                threads = []
                thread = DeploymentHandler(self, destination, params, deploy_metadata)
                thread.start()  
                thread.join()
                test_result = thread.result
                return test_result

        except BaseException, e:
            return mm_util.generate_error_response(e.message)  

    #deploys metadata to one or more orgs
    def deploy_to_server(self, params):
        try:
            deploy_metadata = self.sfdc_client.retrieve(package=params['package'])
            threads = []
            for destination in params['destinations']:
                thread = DeploymentHandler(self, destination, params, deploy_metadata)
                threads.append(thread)
                thread.start()  
            deploy_results = []
            for thread in threads:
                thread.join()  
                deploy_results.append(thread.result)
            return deploy_results
        except Exception, e:
            return mm_util.generate_error_response(e.message)

    #creates a new org connection
    def new_org_connection(self, payload):
        try:
            c = MavensMateClient(credentials={
                "username"  :   payload['username'],
                "password"  :   payload['password'],
                "org_type"  :   payload['org_type']
            })
            org_connection_id = mm_util.new_mavensmate_id()
            mm_util.put_password_by_key(org_connection_id, payload['password'])
            org_connections = self.get_org_connections(False)
            org_connections.append({
                'id'            : org_connection_id,
                'username'      : payload['username'],
                'environment'   : payload['org_type']
            })
            src = open(self.location+"/config/.org_connections", 'w')
            json_data = json.dumps(org_connections, sort_keys=False, indent=4)
            src.write(json_data)
            src.close()
            return mm_util.generate_success_response('Org Connection Successfully Created')
        except Exception, e:
            return mm_util.generate_error_response(e.message) 

    #returns a list of all org connections for this project
    def get_org_connections(self, json=True):
        try:
            if not os.path.exists(self.location+"/config/.org_connections"):
                return []
            if json:
                return open(self.location+"/config/.org_connections", "r").read()
            else:
                return mm_util.parse_json_from_file(self.location+"/config/.org_connections")
        except:
            return []

    #delete a specific org connection
    def delete_org_connection(self, payload):  
        try:
            org_connections = self.get_org_connections(False)
            updated_org_connections = []
            for connection in org_connections:
                if connection['id'] != payload['id']:
                    updated_org_connections.append(connection)
            src = open(self.location+"/config/.org_connections", 'w')
            json_data = json.dumps(updated_org_connections, sort_keys=False, indent=4)
            src.write(json_data)
            src.close()
            mm_util.delete_password_by_key(payload['id'])
            return mm_util.generate_success_response('Org Connection Successfully Deleted')
        except Exception, e:
            return mm_util.generate_error_response(e.message)

    #compiles a list of all metadata in the org and places in .org_metadata file
    def index_metadata(self, mtype=None):
        startThread = time.clock()
        try:    
            return_list = []
            if self.sfdc_client == None or self.sfdc_client.is_connection_alive() == False:
                self.sfdc_client = MavensMateClient(credentials=self.get_creds(), override_session=True)  
                self.__set_sfdc_session()

            data = self.__get_org_describe()

            use_threading = True
            threads = []
            thread_results = []
            creds = self.get_creds()

            if mtype == None:
                metadata_chunks = list(mm_util.grouper(5, data["metadataObjects"]))
                for chunk in metadata_chunks:                    
                    thread_client = MavensMateClient(credentials=creds)
                    thread = IndexCall(thread_client, chunk)
                    threads.append(thread)
                    thread.start()
            else:
                mtype_def = None
                for md in data["metadataObjects"]:
                    if md['xmlName'] == mtype:
                        mtype_def = md
                        break
                thread_client = MavensMateClient(credentials=creds)
                thread = IndexCall(thread_client, [mtype_def])
                threads.append(thread)
                thread.start()
               

            for thread in threads:
                thread.join()
                if len(thread.results) == len(thread.metadata_types):
                    thread_results.extend(thread.results)
                    #del thread.client
            
            #print thread_results
            return_list = sorted(thread_results, key=itemgetter('text')) 
            #return_list = thread_results
            #for testing only
            #return_list = mm_util.parse_json_from_file(self.location+"/config/.org_metadata")
            #end for testing only

            file_body = json.dumps(return_list, sort_keys=False, indent=4)
            src = open(self.location+"/config/.org_metadata", "w")
            src.write(file_body)
            src.close()
            return file_body
        except BaseException, e:
            return mm_util.generate_error_response(e.message)

    def __select_metadata_based_on_package_xml(self, return_list):
        #process package and select only the items the package has specified
        package_types = self.get_package_types();
        #expand standard "custombjects" to customfields
        custom_fields = []
        for val in package_types:
            metadata_type = val['name']
            # If CustomObject is set in package.xml, look at it's members
            if metadata_type == 'CustomObject' and 'members' in val:
                for member in val['members']:
                    # Standard objects don't end with __c, or it's everything
                    if not member.endswith("__c") or member == "*":
                        # We need to look up the fields for this standard object in the org metadata
                        for item in return_list:
                            # CustomField is a child of CustomObject
                            if item['xmlName'] == 'CustomObject':
                                # Loop through all the CustomObject metadata
                                for child in item['children']:
                                    # Currently the standard object from the loop or everything
                                    if child['key'] == member or member == "*":
                                        for props in child['children']:
                                            for field in props['children']:
                                                custom_fields.append(child['key']+'.'+field['key'])
                                        # we can break unless we want to add every field to CustomField for *
                                        if member != "*":
                                            break
                                # we only need to look at CustomObject
                                break

        if len(custom_fields) > 0:
            custom_field = None
            new_packages = []
            for val in package_types:
                if val['name'] == 'CustomField':
                    custom_field = val
                else:
                    new_packages.append(val)

            if custom_field == None:
                custom_field = {'name':'CustomField'}

            if 'members' in custom_field and type(custom_field['members']) == list:
                members = custom_field['members']
            else:
                members = []
            custom_field['members'] = list(set(members+custom_fields))
            new_packages.append(custom_field)
            package_types = new_packages

        for val in package_types:
            metadata_type = val['name']
            metadata_def = mm_util.get_meta_type_by_name(metadata_type)

            if metadata_def == None:
                continue
            
            members = val['members']
            #print 'processing: ', metadata_type
            #print 'package members: ', members
            
            is_parent_type  = 'parentXmlName' not in metadata_def
            is_child_type   = 'parentXmlName' in metadata_def
            is_folder_based = 'inFolder' in metadata_def and metadata_def['inFolder'] == True
            
            server_metadata_item = None
            
            #loop through list of metadata types in the org itself,
            #try to match on the name of this type of metadata
            for item in return_list:
                if is_parent_type and item['xmlName'] == metadata_type:
                    server_metadata_item = item
                    break
                if is_child_type and item['xmlName'] == metadata_def['parentXmlName']:
                    server_metadata_item = item
                    break

            if server_metadata_item == None:
                continue

            if members == "*": #if package is subscribed to all
                server_metadata_item['selected'] = True
                if 'children' in server_metadata_item:
                    for child in server_metadata_item['children']:
                        child['selected'] = True
                        if 'children' in child:
                            for gchild in child['children']:
                                gchild['selected'] = True
                                if 'children' in gchild:
                                    for ggchild in gchild['children']:
                                        ggchild['selected'] = True
                continue
            else: #package has specified members (members => ['Account', 'Lead'])
            
                if type(members) is not list:
                    members = [members]
                
                if is_folder_based: #e.g.: dashboard, report, etc.
                    #print 'folder based!'
                    for m in members:
                        if '/' in m:
                            arr = m.split("/")
                            folder_name = arr[0]
                            item_name = arr[1]
                        else:
                            folder_name = m

                        if '/' in m: #it doesnt seem to matter to set the folder as selected?
                            for child in server_metadata_item['children']:
                                if child['title'] == folder_name:
                                    for folder_item in child['children']:
                                        if folder_item['title'] == item_name:
                                            folder_item['selected'] = True
                                            break
                                    break

                elif is_child_type: #weblink, customfield, etc.
                    #print 'child type!'
                    parent_type = mm_util.get_meta_type_by_name(metadata_def['parentXmlName'])
                    for item in return_list:
                        if item['xmlName'] == parent_type['xmlName']:
                            parent_server_metadata_item = item

                    for m in members:
                        arr = m.split(".")
                        object_name = arr[0]
                        item_name = arr[1]
                        for child in parent_server_metadata_item['children']:
                            if child['title'] == object_name:
                                #"Account"
                                for gchild in child['children']:
                                    #"fields"
                                    for ggchild in gchild['children']:
                                        if gchild['title'] == metadata_def['tagName'] and ggchild['title'] == item_name:
                                            #"field_name__c"
                                            ggchild['selected'] = True
                                        break
                                break

                else:
                    #print 'regular type with specific items selected'
                    for m in members:
                        for child in server_metadata_item['children']:
                            if child['title'] == m:
                                child['selected'] = True
                                if 'children' in child:
                                    for gchild in child['children']:
                                        gchild['selected'] = True
                                        for ggchild in gchild['children']:
                                            ggchild['selected'] = True
        
        return return_list

    def index_apex_overlays(self, payload):
        try:
            result = self.sfdc_client.get_overlay_actions()
            if 'records' not in result or len(result['records']) == 0:
                return mm_util.generate_success_response('Could Not Find Any Apex Execution Overlays')
            else:
                id_to_name_map = {}
                class_ids = []
                trigger_ids = []

                for r in result['records']:
                    entity_id = r["ExecutableEntityId"]
                    if entity_id.startswith('01q'):
                        trigger_ids.append("Id = '"+entity_id+"'")
                    elif entity_id.startswith('01p'):
                        class_ids.append("Id = '"+entity_id+"'")

                class_filter = ' or '.join(class_ids)
                trigger_filter = ' or '.join(trigger_ids)
                
                soql = 'Select Id, Name From ApexClass WHERE '+class_filter
                class_result = self.sfdc_client.execute_query(soql)

                soql = 'Select Id, Name From ApexTrigger WHERE '+class_filter
                trigger_result = self.sfdc_client.execute_query(soql)

                if 'records' in class_result:
                    for r in class_result['records']:
                        id_to_name_map[r['Id']] = r['Name']

                if 'records' in trigger_result:
                    for r in trigger_result['records']:
                        id_to_name_map[r['Id']] = r['Name']

                for r in result['records']:
                    r['API_Name'] = id_to_name_map[r['ExecutableEntityId']]

                overlays = json.dumps(result['records'])
                self.__put_overlays_file(overlays)
                return mm_util.generate_success_response('Apex Execution Overlays Successfully Indexed to config/.overlays')
        except BaseException, e:
            return mm_util.generate_error_response(e.message)

    def new_apex_overlay(self, payload):
        '''
            payload = {
                "ActionScriptType"      : "None",
                "ExecutableEntityId"    : "01pd0000001yXtYAAU",
                "IsDumpingHeap"         : True,
                "Iteration"             : 1,
                "Line"                  : 3,
                "ScopeId"               : "005d0000000xxzsAAA"
            }
        '''
        if 'project_name' in payload:
            payload.pop('project_name', None)

        create_result = self.sfdc_client.create_overlay_action(payload)
        if type(create_result) is list:
            create_result = create_result[0]
        if type(create_result) is not str and type(create_result) is not unicode:
            return json.dumps(create_result)
        else:
            return create_result

    def delete_apex_overlay(self, payload):
        delete_result = self.sfdc_client.remove_overlay_action(overlay_id=payload['id'])
        return delete_result

    def new_trace_log(self, payload):
        try:
            '''
                payload = {
                    "ApexCode"          : "None",
                    "ApexProfiling"     : "01pd0000001yXtYAAU",
                    "Callout"           : True,
                    "Database"          : 1,
                    "ExpirationDate"    : 3,
                    "ScopeId"           : "",
                    "System"            : "",
                    "TracedEntityId"    : "",
                    "Validation"        : "",
                    "Visualforce"       : "",
                    "Workflow"          : ""
                }
            '''
            if 'project_name' in payload:
                payload.pop('project_name', None)
            create_result = self.sfdc_client.create_trace_flag(payload)
            if type(create_result) is list:
                create_result = create_result[0]
            if type(create_result) is not str and type(create_result) is not unicode:
                return json.dumps(create_result)
            else:
                return create_result
        except Exception, e:
            mm_util.generate_error_response(e.message)

    def fetch_logs(self, payload):
        try:
            user_id = payload.get('user_id', self.sfdc_client.user_id)
            limit   = payload.get('limit', 20)
            log_result = self.sfdc_client.execute_query('Select Id, LogUserId, SystemModstamp From ApexLog Where SystemModstamp >= TODAY and Location != \'HeapDump\' and LogUserId = \''+user_id+'\' order by SystemModstamp desc limit '+str(limit))
            logs = []
            if 'records' in log_result:
                for r in log_result['records']:
                    id = r["Id"]
                    log = self.sfdc_client.download_log(id)
                    logs.append({"id":id,"modstamp":str(r["SystemModstamp"]),"log":log,"userid":r["LogUserId"]})
                if os.path.isdir(config.connection.workspace+"/"+self.project_name+"/debug/logs") == False:
                    os.makedirs(config.connection.workspace+"/"+self.project_name+"/debug/logs")
                for the_file in os.listdir(config.connection.workspace+"/"+self.project_name+"/debug/logs"):
                    file_path = os.path.join(config.connection.workspace+"/"+self.project_name+"/debug/logs", the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception, e:
                        print e
                for log in logs:
                    file_name = log["modstamp"]+"."+log["userid"]+".log"
                    src = open(config.connection.workspace+"/"+self.project_name+"/debug/logs/"+file_name, "w")
                    src.write(log["log"])
                    src.close() 
                mm_util.generate_success_response('Logs successfully downloaded') 
            else:
                mm_util.generate_success_response('No logs to download') 

            checkpoint_result = self.sfdc_client.execute_query('Select Id, LogUserId, SystemModstamp From ApexLog Where SystemModstamp >= TODAY and Location = \'HeapDump\' and LogUserId = \''+user_id+'\' order by SystemModstamp desc limit '+str(limit))
            checkpoints = []
            if 'records' in checkpoint_result:
                for r in checkpoint_result['records']:
                    id = r["Id"]
                    cp = self.sfdc_client.download_checkpoint(id)
                    checkpoints.append({"id":id,"modstamp":str(r["SystemModstamp"]),"log":cp,"userid":r["LogUserId"]})
                if os.path.isdir(config.connection.workspace+"/"+self.project_name+"/debug/checkpoints") == False:
                    os.makedirs(config.connection.workspace+"/"+self.project_name+"/debug/checkpoints")
                for the_file in os.listdir(config.connection.workspace+"/"+self.project_name+"/debug/checkpoints"):
                    file_path = os.path.join(config.connection.workspace+"/"+self.project_name+"/debug/checkpoints", the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception, e:
                        print e
                for cp in checkpoints:
                    file_name = cp["modstamp"]+"."+cp["userid"]+".log"
                    src = open(config.connection.workspace+"/"+self.project_name+"/debug/checkpoints/"+file_name, "w")
                    src.write(cp["log"])
                    src.close() 
                mm_util.generate_success_response('Checkpoints successfully downloaded') 
            else:
                mm_util.generate_success_response('No checkpoints to download') 
        except Exception, e:
            mm_util.generate_error_response(e.message)

    def __get_package_as_dict(self):
        return mm_util.parse_xml_from_file(os.path.join(self.location,"src","package.xml"))

    def get_package_types(self):
        try:
            project_package = self.__get_package_as_dict()
            package_types = project_package['Package']['types']
            if not isinstance(package_types, (list, tuple)):
                package_types = [package_types]
            return package_types
        except:
            return []

    def get_is_metadata_indexed(self):
        try:
            if os.path.exists(os.path.join(self.location,"config",".org_metadata")):
                json_data = mm_util.parse_json_from_file(os.path.join(self.location,"config",".org_metadata"))
                return True
            else:
                return False
        except:
            return False

    def get_org_users_list(self):
        if self.sfdc_client == None or self.sfdc_client.is_connection_alive() == False:
            self.sfdc_client = MavensMateClient(credentials=self.get_creds(), override_session=False)  
            self.__set_sfdc_session()
        try:
            query_result = self.sfdc_client.execute_query('Select Id, Name From User Where IsActive = True order by Name limit 10000')
        except:
            query_result = self.sfdc_client.execute_query('Select Id, Name From User Where Active = True order by Name limit 10000')
        if 'records' in query_result:
            return query_result['records']
        else:
            return []

    def get_trace_flags(self):
        if self.sfdc_client == None or self.sfdc_client.is_connection_alive() == False:
            self.sfdc_client = MavensMateClient(credentials=self.get_creds(), override_session=False)  
            self.__set_sfdc_session()
        query_result = self.sfdc_client.execute_query('Select Id, Name From User Where IsActive = True order by Name limit 10000')
        if 'records' in query_result:
            return query_result['records']
        else:
            return []

    def get_org_metadata(self, selected=None, raw=False):
        if self.get_is_metadata_indexed() == True:
            if raw:
                return mm_util.get_file_as_string(os.path.join(self.location,"config",".org_metadata"))
            else:
                metadata = mm_util.parse_json_from_file(os.path.join(self.location,"config",".org_metadata"))
                # if selected != None and len(selected) > 0:
                #     for p in selected:
                #         for item in metadata:
                #             for child in item['children']:
                #                 if child['title'] == p:
                #                     child['selected'] = True
                #                 else:
                #                     child['selected'] = False
                # else:
                #     metadata = self.__select_metadata_based_on_package_xml(metadata)
                #     
                #metadata = None
                #file_body = json.dumps(metadata)
                #src = open(os.path.join(self.location,"config",".org_metadata"), "w")
                #src.write(file_body)
                #src.close()
                return metadata
        else:
            self.index_metadata()
            return mm_util.parse_json_from_file(os.path.join(self.location,"config",".org_metadata"))

    def __get_settings(self):
        #returns settings for this project (handles legacy yaml format)
        try:
            if os.path.isfile(os.path.join(self.location,"config","settings.yaml")):
                f = open(os.path.join(self.location,"config","settings.yaml"))
                settings = yaml.safe_load(f)
                f.close()
                if settings == None:
                    raise MMException('Unable to read settings file for this project.')
                return settings
            elif os.path.isfile(os.path.join(self.location,"config",".settings")):
                settings = mm_util.parse_json_from_file(os.path.join(self.location,"config",".settings"))
                if settings == None:
                    raise MMException('Unable to read settings file for this project.')
                return settings
            else:
                return {}
        except:
            raise MMException('Unable to read settings file for this project.')

    def get_creds(self): 
        #initialize variables so it doesn't bomb if any are missing
        id, project_name, username, environment, endpoint, org_type, password, is_legacy = None, '', '', None, '', '', '', False
        #get the mm project settings
        settings = self.__get_settings()

        #get the common project properties
        if 'id' in settings: 
            id = settings['id']
        if 'project_name' in settings: 
            project_name = settings['project_name']
        else:
            #default to project folder name
            project_name = os.path.basename(self.location)
        if 'username' in settings: 
            username = settings['username']
        if 'environment' in settings: 
            #TODO: let's standardize environment vs. org_type (org_type is preferred)
            environment, org_type = settings['environment'], settings['environment']
            endpoint = mm_util.get_sfdc_endpoint_by_type(environment)
        #get password from id, or name for legacy/backup
        if id:
            password = mm_util.get_password_by_key(id)
        else:
            password = mm_util.get_password_by_project_name(project_name)
  
        creds = { }
        creds['username'] = username
        creds['password'] = password
        creds['endpoint'] = endpoint
        creds['org_type'] = org_type
        if self.sfdc_session != None:
            creds['user_id']                = self.sfdc_session.get('user_id', None)
            creds['sid']                    = self.sfdc_session.get('sid', None)
            creds['metadata_server_url']    = self.sfdc_session.get('metadata_server_url', None)
            creds['endpoint']               = self.sfdc_session.get('endpoint', None)
            creds['server_url']             = self.sfdc_session.get('server_url', None)
        return creds


    def __log_anonymous_apex(self, apex_body):
        if not os.path.exists(os.path.join(self.location, "apex-scripts")):
            os.makedirs(os.path.join(self.location, "apex-scripts"))
        src = open(os.path.join(self.location, "apex-scripts", mm_util.get_timestamp()), "w")
        src.write(apex_body)
        src.close()

    #write a file containing the MavensMate settings for the project
    def __put_settings_file(self, settings=None):
        if settings == None:
            settings = {
                "project_name"          : self.project_name,
                "username"              : self.username,
                "environment"           : self.org_type,
                "namespace"             : self.sfdc_client.get_org_namespace(),
                "id"                    : self.id,
                "metadata_container"    : self.sfdc_client.get_metadata_container_id()
            }
        src = open(os.path.join(config.connection.workspace,self.project_name,"config",".settings"), "w")
        json_data = json.dumps(settings, sort_keys=False, indent=4)
        src.write(json_data)
        src.close()

    #write a file containing the dynamic describe information for the org
    def __put_describe_file(self):
        file_name = ".describe"
        src = open(os.path.join(config.connection.workspace,self.project_name,"config",file_name), "w")
        describe_result = self.sfdc_client.describeMetadata()
        d = xmltodict.parse(describe_result,postprocessor=mm_util.xmltodict_postprocessor)
        json_data = json.dumps(d["soapenv:Envelope"]["soapenv:Body"]["describeMetadataResponse"]["result"], sort_keys=True, indent=4)
        src.write(json_data)
        src.close()

    #write a file containing the dynamic describe information for the org
    def __put_overlays_file(self, overlays):
        file_name = ".overlays"
        src = open(os.path.join(config.connection.workspace,self.project_name,"config",file_name), "w")
        src.write(overlays)
        src.close()   

    #returns metadata types for this org, or default types
    def __get_org_describe(self):
        try:
            return mm_util.parse_json_from_file(os.path.join(self.location,"config",".describe"))
        except:
            return mm_util.get_default_metadata_data()

    def __put_base_config(self):
        if os.path.isdir(os.path.join(config.connection.workspace,self.project_name,"config")) == False:
            os.makedirs(os.path.join(config.connection.workspace,self.project_name,"config"))
        self.__put_settings_file()
        self.__put_describe_file()

    def __put_project_file(self):
        if config.connection.plugin_client == 'SUBLIME_TEXT_2' or config.connection.plugin_client == 'SUBLIME_TEXT_3':
            sublime_project_file_path = os.path.join(config.connection.workspace,self.project_name,self.project_name+".sublime-project")
            project_path = os.path.join(config.connection.workspace,self.project_name)
            src = open(sublime_project_file_path, "w")
            src.write('{"folders":[{"path": "'+project_path+'"}]}')
            src.close()

    #returns the cached session information (handles yaml [legacy] & json)
    def __get_sfdc_session(self):
        session = None
        try:
            try:
                session = mm_util.parse_json_from_file(os.path.join(self.location,"config",".session"))
            except:
                try:
                    f = open(os.path.join(self.location,"config",".session"))
                    session = yaml.safe_load(f)
                    f.close()
                except:
                    pass
            return session
        except:
            return None

    #writes session information to the local cache
    def __set_sfdc_session(self):
        try:
            session = {
                "user_id"               : self.sfdc_client.user_id,
                "sid"                   : self.sfdc_client.sid,
                "metadata_server_url"   : self.sfdc_client.metadata_server_url,
                "server_url"            : self.sfdc_client.server_url,
                "endpoint"              : self.sfdc_client.endpoint
            }
            file_body = json.dumps(session)
            src = open(os.path.join(self.location,"config",".session"), "w")
            src.write(file_body)
            src.close()
        except:
            pass


class DeploymentHandler(threading.Thread):

    def __init__(self, project, destination, params, deploy_metadata):
        self.project            = project
        self.destination        = destination
        self.params             = params
        self.deploy_metadata    = deploy_metadata
        self.result             = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            if 'password' not in self.destination:
                self.destination['password'] = mm_util.get_password_by_key(self.destination['id'])
            deploy_client = MavensMateClient(credentials={
                "username":self.destination['username'],
                "password":self.destination['password'],
                "org_type":self.destination['org_type']
            })    

            # Check testRequired to find out if this is a production org.
            # This is a bit of a misnomer as runAllTests=True will run managed package tests, other 
            # tests are *always* run so we should honor the UI, however Production orgs do require 
            # rollbackOnError=True so we should override it here
            describe_result = deploy_client.describeMetadata(retXml=False)
            if describe_result.testRequired == True:
                self.params['rollback_on_error'] = True

            self.params['zip_file'] = self.deploy_metadata.zipFile      
            deploy_result = deploy_client.deploy(self.params)
            #config.logger.debug('>>>>>> DEPLOY RESULT >>>>>>')
            #config.logger.debug(deploy_result)
            self.result = deploy_result
        except BaseException, e:
            self.result = mm_util.generate_error_response(e.message)

class IndexCall(threading.Thread):
    def __init__(self, client, metadata_types):
        self.metadata_types = metadata_types
        self.client         = client
        self.results        = []
        threading.Thread.__init__(self)

    def run(self):
        startThread = time.clock()
        for mtype in self.metadata_types:
            print mtype["xmlName"]
            if mtype == None:
                continue
            try:
                result = self.client.list_metadata(mtype['xmlName'])
                if result == None:
                    result = []
                self.results.append({
                    "text"      : mtype['xmlName'],
                    "xmlName"   : mtype['xmlName'],
                    "type"      : mtype,
                    "cls"       : "folder",
                    "expanded"  : False,
                    "children"  : result,
                    "checked"   : False,
                    "level"     : 1
                })
                elapsed =  (time.clock() - startThread)
            except BaseException, e:
                #print 'ERROR: %s\n' % str(e)
                #print self.result
                print 'error when trying to index: ', mtype['xmlName']
                print e.message
                trace = re.sub( r'\"/(.*?\.pyz/)', r'', traceback.format_exc()).strip()
                print trace
                #print self.metadata_type['xmlName']
                #self.result = mm_util.generate_error_response(e.message)
                #self.results.append({})
                self.results.append({
                    "text"      : mtype['xmlName'],
                    "xmlName"   : mtype['xmlName'],
                    "type"      : mtype,
                    "cls"       : "folder",
                    "expanded"  : False,
                    "children"  : [],
                    "checked"   : False,
                    "level"     : 1
                })
                continue





