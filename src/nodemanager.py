#!/usr/bin/python

'''
@author: Michal Kubik @ SVT QA 2013
'''

from SimpleXMLRPCServer import SimpleXMLRPCServer
from optparse import OptionParser
import shlex
from time import localtime, strftime
import subprocess
import os
import sys
import logging
import signal


# basic configuration
logging.basicConfig(filename='node-manager.log', level=logging.INFO)

NOT_SUPPORTED = "Not supported yet, contact michal.kubik.pl@gmail.com if you need it ;)"

# exit codes
SUCCESS = True
FAILURE = False


class NodeManager(SimpleXMLRPCServer):
    """
    Node Manager features served over XML-RPC protocol to be executed from remote host
    """

    finished = False

    def register_signal(self, signum):
        signal.signal(signum, self.signal_handler)

    def signal_handler(self, signum, frame):
        print "Caught signal", signum
        self.shutdown()

    def start(self):
        self.finished = False
        try:
            logging.info(' %s\n\tNode Manager started' % strftime('%d %b %Y %H:%M:%S', localtime()))
            # register breaking signals
            # s.register_signal(signal.SIGTERM)
            # s.register_signal(signal.SIGINT)

            self.serve_forever()
        except KeyboardInterrupt:
            logging.info('Exiting')
        except Exception, e:
            logging.info('\tReceived term signal. Closing.')
        return SUCCESS

    def stop(self):
        self.shutdown()

    def shutdown(self):
        self.finished = True
        return SUCCESS

    def serve_forever(self):
        while not self.finished:
            self.handle_request()


class NodeManagerFunctionsBase:
    def status(self):
        print("status")
        return SUCCESS

    def list_dir(self, dir_name):
        """List directory provided as argument
            @param dir_name: directory to list
        """
        logging.debug('list_dir(%s)', dir_name)
        return os.listdir(dir_name), SUCCESS

    def cwd(self):
        return os.getcwd(), SUCCESS


class NodeManagerFunctionsUnix(NodeManagerFunctionsBase):
    def killChromedrivers(self):
        return NOT_SUPPORTED

    def killChromedrivers(self):
        return NOT_SUPPORTED


class NodeManagerFunctionsWin(NodeManagerFunctionsBase):
    def killChromedrivers(self):
        logging.info("Executing killChromedrivers request")
        # _executeCommand("taskkill /F /IM chromedriver.exe", silently=True)
        return _getCommandExecutionResponse("taskkill /F /IM chromedriver.exe"), SUCCESS
        # return SUCCESS

    def killChromes(self):
        logging.info("Executing killChromes request")
        return _getCommandExecutionResponse("taskkill /F /IM chrome.exe"), SUCCESS
        # return SUCCESS


def getNodeManager(host, port, logRequests=False):
    try:
        s = NodeManager((host, port), logRequests=logRequests)
    except Exception, err:
        logging.error('\tProblem starting server: %s\n' % err)
        sys.stderr.write('Problem starting server. '
                         'If error is: "Address already in use" wait and try again\n'
                         '\terror is: %s\n' % err)
        sys.exit(1)
    if 'win' in sys.platform:
        s.register_instance(NodeManagerFunctionsWin())
    else:
        s.register_instance(NodeManagerFunctionsUnix())

    s.register_introspection_functions()

    return s


def _executeCommandInShell(command, silently=False):
    devnull = open(os.devnull, 'w') if silently else None
    return subprocess.call(shlex.split(command), shell=True, stdout=devnull, stderr=devnull)


def _executeCommand(command, silently=False):
    devnull = open(os.devnull, 'w') if silently else None
    return subprocess.call(shlex.split(command), shell=False, stdout=devnull, stderr=devnull)


def _getCommandExecutionResponse(command):
    try:
        output = subprocess.check_output(shlex.split(command), shell=False, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        output = e.output
    logging.debug(output)
    return output


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-P", "--port", dest="port", default=5005, type="int",
                      help="node-manager port [default: 5005]")
    parser.add_option("-l", "--log-requests", action="store_true", dest="logRequests", default=False,
                      help="enables logging requests [default: False]")
    (options, args) = parser.parse_args()
    s = getNodeManager('', options.port, options.logRequests)

    s.start()