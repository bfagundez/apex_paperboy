import os
import random
import string
import json
import shutil
import threading
import subprocess
import pipes
import config as global_config

#this function is only used on async requests
def generate_request_id():
    return get_random_string()

def get_random_string(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

#the main job of the backgroundworker is to submit a request for work to be done by mm
class BackgroundWorker(threading.Thread):
    def __init__(self, operation, params, async, request_id=None, payload=None):
        self.operation  = operation
        self.params     = params
        self.request_id = request_id
        self.async      = async
        self.payload    = payload
        self.response   = None
        threading.Thread.__init__(self)

    def run(self):
        mm_response = None
        args = self.get_arguments()
        global_config.logger.debug('>>> running thread!')
        global_config.logger.debug(args)
        p = subprocess.Popen("{0} {1}".format(pipes.quote(global_config.mm_path), args), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        p.stdin.write(self.payload)
        p.stdin.close()
        if p.stdout is not None: 
            mm_response = p.stdout.readlines()
        elif p.stderr is not None:
            mm_response = p.stderr.readlines()
        response_body = '\n'.join(mm_response)
        self.response = response_body
        self.finish()
        # if self.async == True:
        #     self.queue.put(response_body)
        # else:
        #     return response_body

    def finish(self):
        if self.operation == 'new_project' or self.operation == 'checkout_project':
            print self.response
            if json.loads(self.response)['success'] == True:
                os.system('killAll MavensMateWindowServer')

    def get_arguments(self):
        args = {}
        args['-o'] = self.operation #new_project, get_active_session

        if self.operation == 'new_project':
            pass
        elif self.operation == 'checkout_project':
            pass  
        elif self.operation == 'get_active_session':
            pass 
        elif self.operation == 'update_credentials':
            pass
        elif self.operation == 'execute_apex':
            pass
        elif self.operation == 'deploy':
            args['--html'] = None
        elif self.operation == 'unit_test':
            args['--html'] = None
        elif self.operation == 'index_metadata':
            args['--html'] = None    
                
        arg_string = []
        for x in args.keys():
            if args[x] != None:
                arg_string.append(x + ' ' + args[x] + ' ')
            else:
                arg_string.append(x + ' ')
        stripped_string = ''.join(arg_string).strip()
        return stripped_string