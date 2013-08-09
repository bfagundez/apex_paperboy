import logging
from lib.sforce.base import SforceBaseClient
from suds import WebFault
from lib.sforce.partner import SforcePartnerClient
from lib.sforce.metadata import SforceMetadataClient
from lib.sforce.apex import SforceApexClient
from lib.sforce.tooling import SforceToolingClient
from optparse import OptionParser

logging.basicConfig(format='[=] %(asctime)s | %(levelname)s | %(message)s [%(module)s:%(lineno)d]  ',datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)
logging.info('Loading libs')
import ipdb
import lib.mm_util as mm_util
import time

import os

# Adds an option to command line to clean up all transactions and mappings on start
# for dev purposes only.
parser = OptionParser()

parser.add_option("-u", "--user", dest="user", type="string", help="Salesforce username")
parser.add_option("-p", "--password", dest="password", type="string", help="Salesforce password")
parser.add_option("-t", "--token", dest="token", type="string", help="Salesforce token")
parser.add_option("-s", "--apex-script", dest="apexscriptfilename", type="string", help="Apex code to execute")

(options, args) = parser.parse_args()

missing_args = False
error_log = '\n [!] Errors found \n\n'
if options.user == None:
      missing_args = True
      error_log = error_log + "~ Salesforce username is required \n"
if options.password == None:
      missing_args = True
      error_log = error_log + "~ Salesforce password is required \n"
if options.token == None:
      missing_args = True
      error_log = error_log + "~ Salesforce token is required \n"
if options.apexscriptfilename == None:
      missing_args = True
      error_log = error_log + "~ Apex script filename is required \n"

if missing_args:
      print error_log 
else:
      logging.info('Loading partner WSDL')
      wsdl_location = os.path.join(mm_util.WSDL_PATH, 'partner.xml')
      client = SforcePartnerClient(
                  wsdl_location,
                  apiVersion=None,
                  environment='production',
                  sid=None,
                  metadata_server_url=None,
                  server_url=None)

      try:
            # login using partner wsdl
            logging.info('Authenticating')
            client.login(options.user,options.password,options.token)

            # use token with apex wsdl
            apex_wsdl_location = os.path.join(mm_util.WSDL_PATH, 'apex.xml')
            apex_client = SforceApexClient(
                        apex_wsdl_location,
                        apiVersion=mm_util.SFDC_API_VERSION,
                        environment='production',
                        sid=client.getSessionId(),
                        metadata_server_url=client.getMetadaServerUrl(),
                        server_url=mm_util.get_sfdc_endpoint_by_type('enterprise'))

            # open script file
            logging.info('Loading scripts')
            f = open(options.apexscriptfilename, "r")
            apex_code = f.read()

            # Execute code
            logging.info('Running apex code')
            t0 = time.clock()
            apex_execution = apex_client.executeAnonymous({"body":apex_code})
            logging.info('Finished execution')
            logging.info("Code executed in "+str(time.clock() - t0)+ " seconds.")
            if apex_execution.success:
                  print "~ Script executed successfully"
            else:
                  print "[!] Errors found:"
                  if apex_execution.exceptionMessage:
                        print apex_execution.exceptionMessage
                  if apex_execution.compileProblem:
                        print 'Compilation error: '+apex_execution.compileProblem
                  print 'Line: '+str(apex_execution.line)
                  

      except Exception, e:
            logging.error('Exception found:'+str(e.message)) 
      
      
     


