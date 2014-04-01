# -*- coding: utf-8 -*-

# unicode color codes
OKGREEN = '\033[92m'
NOTOKRED = '\033[91m'
OKBLUE = '\033[94m'
WARNING = '\033[93m'
HEADER = '\033[95m'
ENDC = '\033[0m'

from lib.sforce.base import SforceBaseClient
from suds import WebFault
from lib.sforce.partner import SforcePartnerClient
from lib.sforce.metadata import SforceMetadataClient
from lib.sforce.apex import SforceApexClient
from lib.sforce.tooling import SforceToolingClient
from optparse import OptionParser
import lib.mm_util as mm_util
import time
import os
import sys

# Adds an option to command line to clean up all transactions and mappings on start
# for dev purposes only.
parser = OptionParser()

parser.add_option("-u", "--user", dest="user", type="string", help="Salesforce username")
parser.add_option("-p", "--password", dest="password", type="string", help="Salesforce password")
parser.add_option("-t", "--token", dest="token", type="string", help="Salesforce token")
parser.add_option("-s", "--apex-script", dest="apexscriptfilename", type="string", help="Apex code to execute")

(options, args) = parser.parse_args()

missing_args = False
error_log = '\n'+NOTOKRED+' ✗'+ENDC+' Errors found \n\n'

if options.user == None:
  missing_args = True
  error_log += " ~ Salesforce username is required \n"
if options.password == None:
  missing_args = True
  error_log += " ~ Salesforce password is required \n"
if options.apexscriptfilename == None:
  missing_args = True
  error_log += " ~ Apex script filename is required \n"

if missing_args:
  print error_log
else:
  print ' \n🏁   Starting apex execution \n '
  print '- Loading partner WSDL'
  try:
    wsdl_location = os.path.join(mm_util.WSDL_PATH, 'partner.xml')
    client = SforcePartnerClient(
          wsdl_location,
          apiVersion=None,
          environment='production',
          sid=None,
          metadata_server_url=None,
          server_url=None)
    print OKGREEN+'√'+ENDC+' WSDL loaded \n '
  except Exception, e:
    print '\n'+NOTOKRED+'✗'+ENDC+' Unable to load the WSDL '
    print e.message
    sys.exit()

  try:
    # login using partner wsdl
    print '- Authenticating'
    # sometimes password and token are provided together.
    # token parameter is not required.
    token_safe = ''
    if options.token:
          token_safe = options.token
    client.login(options.user,options.password,token_safe)

    # use token with apex wsdl
    apex_wsdl_location = os.path.join(mm_util.WSDL_PATH, 'apex.xml')
    apex_client = SforceApexClient(
                apex_wsdl_location,
                apiVersion=mm_util.SFDC_API_VERSION,
                environment='production',
                sid=client.getSessionId(),
                metadata_server_url=client.getMetadaServerUrl(),
                server_url=mm_util.get_sfdc_endpoint_by_type('enterprise'))

    print OKGREEN+'√'+ENDC+' Authentication succesful. \n '

  except Exception, e:
    print '\n'+NOTOKRED+'✗'+ENDC+' Error during authentication '
    print e.message
    sys.exit()

  try:
    print '- Opening the file'
    # open script file
    f = open(options.apexscriptfilename, "r")
    apex_code = f.read()
    print OKGREEN+'√'+ENDC+' File loaded succesfully. \n '
  except Exception, e:
    print '\n'+NOTOKRED+'✗'+ENDC+' Error found reading the file '
    print e.message
    sys.exit()

  try:
    # Execute code
    print '- Executing the script'
    t0 = time.clock()
    apex_execution = apex_client.executeAnonymous({"body":apex_code})

    if apex_execution.success:
      print OKGREEN+'√'+ENDC+' Script executed succesfully 🍻 \n '
      print 'Code executed in '+str(time.clock() - t0)+ ' seconds. \n'
    else:
      print NOTOKRED+'✗'+ENDC+' Errors found: '
      if apex_execution.exceptionMessage:
            print apex_execution.exceptionMessage
      if apex_execution.compileProblem:
            print 'Compilation error: '+apex_execution.compileProblem
      print 'Line: '+str(apex_execution.line)

  except Exception, e:
    #logger.error(str(e.message))
    print '\n'+NOTOKRED+'✗'+ENDC+' Errors found '
    print e.message
    sys.exit()






