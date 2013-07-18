import BaseHTTPServer
import lib.config as config

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
  # set mappings - dict of dicts - ex: {'/' : {'GET' : test}}
  # meaning, path / with GET request will map to test handler
    mappings = {}

    def main_handler(self, method='GET'):
        # get request url (without url params) and remove trailing /
        config.logger.debug('>>> handling request')
        config.logger.debug(self.path)

        request_url = self.path.split('?')[0]
        if request_url is not '/':
            request_url = request_url.rstrip('/')

        handler = None
        try:
            handler = self.mappings[request_url][method]
        except KeyError, e:
            # no mapping found for the request
            self.send_response(404)
            self.end_headers()
            return

        try:
            handler(self)
        except KeyError, e:
            # method not found
            self.send_response(501)
            self.end_headers()
            return

    def do_GET(self):
        self.main_handler('GET')
        return

    def do_POST(self):
        self.main_handler('POST')
        return