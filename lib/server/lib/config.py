import logging
import os.path
import sys
import tempfile 

def __get_base_path():
    if hasattr(sys, 'frozen'):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.dirname(__file__))

def __get_is_frozen():
    if hasattr(sys, 'frozen'):
        return True
    else:
        return False

mm_path = '/Users/josephferraro/Development/Python/mavensmate/mm/mm.py'
frozen = __get_is_frozen()
base_path = __get_base_path()

handler = logging.FileHandler(tempfile.gettempdir()+"/mmserver.log")
#handler = logging.NullHandler()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('mmserver')
logging.getLogger('mmserver').propagate = False 
logging.getLogger('mmserver').addHandler(handler)
logger.setLevel(logging.DEBUG)