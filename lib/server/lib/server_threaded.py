import sys
import os
import BaseHTTPServer
import handler
import config
import lib.config as gc

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
import threading
server = None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run(context_path='', port=9000):
    gc.logger.debug('>>> starting threaded MavensMate server!')
    base_dir = os.path.normpath(os.path.abspath(os.path.curdir))
    sys.path.insert(0, base_dir)
    handler.Handler.mappings = config.mappings
    server = ThreadedHTTPServer((context_path, 9000), handler.Handler)
    server.serve_forever()

def stop():
    print '>>> shutting down local MavensMate server'
    server.shutdown()