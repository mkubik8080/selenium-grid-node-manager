#!/usr/bin/python

'''
@author: Michal Kubik @ SVT QA 2013
'''

from SimpleXMLRPCServer import SimpleXMLRPCServer
from time import localtime, strftime
import subprocess
import os
import sys
import logging


# basic configuration
PORT = 5005
LOGREQUESTS = False
logging.basicConfig(filename='node-manager.log', level=logging.INFO)

# exit codes
SUCCESS = True
FAILURE = False


class NodeManager:
    """
    Node Manager features served over XML-RPC protocol to be executed from remote host
    """

    def __init__(self, hostName, port):
        self.port = port
        self.hostName = hostName

    def _start(self):
        try:
            s = SimpleXMLRPCServer((self.hostName, self.port), logRequests=LOGREQUESTS)
        except Exception, err:
            logging.error('\tProblem starting server: %s\n' % err)
            sys.stderr.write('Problem starting server. '
                             'If error is: "Address already in use" wait and try again\n'
                             '\terror is: %s\n' % err)
            sys.exit(1)
        s.register_instance(self)
        s.register_introspection_functions()
        try:
            print '\n\tNode Manager started\n'
            logging.info(' %s\n\tNode Manager started\n' % strftime('%d %b %Y %H:%M:%S', localtime()))
            s.serve_forever()
        except KeyboardInterrupt:
            print 'Exiting'
        except:
            logging.info('\tReceived term signal. Closing.')

    def _executeCmdInShell(self, command):
        proc = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = proc.communicate()[1]
        if err != '':
            logging.warning('\tError executing shell command: %s' % err)
            raise OSError('Error executing shell command: %s' % err)

    def status(self):
        return SUCCESS

    def list_dir(self, dir_name):
        """List directory provided as argument
            @param dir_name: directory to list
        """
        logging.debug('list_dir(%s)', dir_name)
        return os.listdir(dir_name), SUCCESS

    # def startManager(self):
    #     """Starts Node Manager with proper parameters"""
    #
    #     logging.info('\tStarting Node Manager...')
    #     if (hasattr(os, "devnull")):
    #         DEVNULL = os.devnull
    #     else:
    #         DEVNULL = "/dev/null"
    #
    #     self.devnull = open(DEVNULL, 'w')
    #
    #     return SUCCESS

if __name__ == '__main__':
    server = NodeManager('', PORT)
    server._start()