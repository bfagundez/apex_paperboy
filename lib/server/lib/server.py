import sys
import os
import BaseHTTPServer
import handler
import config as gc
import endpoints
import daemon
import contextlib

server = None

def run(daemon=True, context_path='', port=9000):
    gc.logger.debug('>>> starting local MavensMate server!')
    # set current working dir on python path
    base_dir = os.path.normpath(os.path.abspath(os.path.curdir))
    sys.path.insert(0, base_dir)
    handler.Handler.mappings = endpoints.mappings
    server = BaseHTTPServer.HTTPServer((context_path, port), handler.Handler)
    
    if daemon:
        daemon_context = daemon.DaemonContext()
        daemon_context.files_preserve = [server.fileno()]
        with daemon_context:
            server.serve_forever()
    else:
        server.serve_forever()

def stop():
    print '>>> shutting down local MavensMate server'
    server.shutdown()