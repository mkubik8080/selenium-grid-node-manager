#!/usr/bin/python

'''
@author: Michal Kubik @ SVT QA 2013
'''

from SimpleXMLRPCServer import SimpleXMLRPCServer
import hashlib
from optparse import OptionParser
import shlex
from time import localtime, strftime
import subprocess
import os
import sys
import logging
import signal


# basic configuration
NOT_SUPPORTED = "Not supported yet, if you need it fill in Issue on https://github.com/mkubik8080/selenium-grid-node-manager ;)"

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

    def start(self, cwd=None):
        self.finished = False
        try:
            logging.info('Node Manager started at %s' % strftime('%d %b %Y %H:%M:%S', localtime()))
            # update working dir if needed
            if cwd:
                os.chdir(cwd)

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
        logging.debug("status()")
        return SUCCESS, ""

    def list_dir(self, dir_name):
        """List directory provided as argument
            @param dir_name: directory to list
        """
        logging.debug('list_dir(%s)', dir_name)
        return SUCCESS, os.listdir(dir_name)

    def cwd(self):
        logging.debug("cwd()")
        return SUCCESS, os.getcwd()

    def writeFile(self, arg, path):
        wrong_path = "Saving outside working directory not allowed, use relative path wisely or proper absolute path"
        file_exists = "File exists in filesystem, cannot overwrite"
        if not os.getcwd() in os.path.abspath(path):
            return FAILURE, wrong_path
        if os.path.isfile(path):
            return FAILURE, file_exists
        with open(path, 'w+b') as file:
            file.write(arg.data)
            return SUCCESS, md5_for_file(file)


class NodeManagerFunctionsUnix(NodeManagerFunctionsBase):
    def killChromedrivers(self):
        return FAILURE, NOT_SUPPORTED

    def killChromedrivers(self):
        return FAILURE, NOT_SUPPORTED


class NodeManagerFunctionsWin(NodeManagerFunctionsBase):
    def killChromedrivers(self):
        logging.info("Executing killChromedrivers request")
        # _executeCommand("taskkill /F /IM chromedriver.exe", silently=True)
        return SUCCESS, _getCommandExecutionResponse("taskkill /F /IM chromedriver.exe")
        # return SUCCESS

    def killChromes(self):
        logging.info("Executing killChromes request")
        return SUCCESS, _getCommandExecutionResponse("taskkill /F /IM chrome.exe")
        # return SUCCESS


def getNodeManager(host, port, logRequests=False, loggerFile=None, loggerLevel=logging.INFO):
    FILE_NAME = loggerFile or os.path.join(os.path.dirname(os.path.realpath(__file__)), 'node-manager.log')
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(filename=FILE_NAME, level=loggerLevel, format=FORMAT)

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


def md5_for_file(f, block_size=2 ** 20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-P", "--port", dest="port", default=5005, type="int",
                      help="node-manager port [default: 5005]")
    parser.add_option("-l", "--log-requests", action="store_true", dest="logRequests", default=False,
                      help="enables logging requests [default: False]")
    (options, args) = parser.parse_args()
    s = getNodeManager('', options.port, options.logRequests, loggerLevel=logging.DEBUG)

    s.start()