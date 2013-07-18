from lib.sforce.base import SforceBaseClient
from suds import WebFault
from lib.sforce.partner import SforcePartnerClient
from lib.sforce.metadata import SforceMetadataClient
from lib.sforce.apex import SforceApexClient
from lib.sforce.tooling import SforceToolingClient

import ipdb
import lib.mm_util as mm_util

import os
wsdl_location = os.path.join(mm_util.WSDL_PATH, 'partner.xml')
client = SforcePartnerClient(
            wsdl_location, 
            apiVersion=None, 
            environment='production', 
            sid=None, 
            metadata_server_url=None, 
            server_url=None)

client.login('crm.dev@codestreet.com', 'T@rH3el04akhHrO4Kuku2PlaQa11l429f', '')

apex_wsdl_location = os.path.join(mm_util.WSDL_PATH, 'apex.xml')
apex_client = SforceApexClient(
            apex_wsdl_location, 
            apiVersion=mm_util.SFDC_API_VERSION, 
            environment='production', 
            sid=client.getSessionId(), 
            metadata_server_url=client.getMetadaServerUrl(), 
            server_url=mm_util.get_sfdc_endpoint_by_type('enterprise'))

# VICTORY!
apex_client.executeAnonymous({"body":"System.Debug('pepe');"})