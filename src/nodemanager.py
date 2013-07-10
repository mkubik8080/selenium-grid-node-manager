#!/usr/bin/python

'''
@author: Michal Kubik @ SVT QA 2013
'''

import os
import sys
import logging
import signal
import shlex
import hashlib
import subprocess

from optparse import OptionParser
from time import localtime, strftime
from SimpleXMLRPCServer import SimpleXMLRPCServer


# basic configuration
NOT_SUPPORTED = "Not supported yet, if you need it fill in Issue on https://github.com/mkubik8080/selenium-grid-node-manager ;)"

# exit codes
SUCCESS = True
FAILURE = False

chunked_files = {}


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

    def dummy(self):
        return SUCCESS, "dummy response"

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
        check = is_path_allowed(path)
        if not check.get("status"):
            return FAILURE, check.get("errorMsg")

        with open(path, 'wb') as file:
            file.write(arg.data)

        logging.info("Wrote file " + get_path_and_size_of(path))

        return SUCCESS, md5_for_file(path)

    def writeFileChunk(self, arg, path):
        if not path in chunked_files:
            check = is_path_allowed(path)
            if not check.get("status"):
                return FAILURE, check.get("errorMsg")
            chunked_files[path] = 0

        with open(path, 'ab') as file:
            file.write(arg.data)

        chunked_files[path] += len(arg.data)
        logging.info("Wrote file chunk: {}/{}".format(
            sizeof_fmt(len(arg.data)), sizeof_fmt(chunked_files.get(path)))
        )

        return SUCCESS, chunked_files.get(path)

    def finalizeChunkedFile(self, path):
        if not chunked_files.has_key(path):
            return FAILURE, "There is no unfinished file like: " + path
        else:
            logging.info(
                "Finished writing file " + get_path_and_size_of(path))
            chunked_files.pop(path)

        return SUCCESS, md5_for_file(path)

    def selfUpdate(self):
        logging.info("self update proccess started...")
        getCommandExecutionResponse("pullFromGitHub.bat")
        return SUCCESS, getCommandExecutionResponse("reInstallNodeManager.bat")


class NodeManagerFunctionsUnix(NodeManagerFunctionsBase):
    def killChromes(self):
        return FAILURE, NOT_SUPPORTED

    def killChromeDrivers(self):
        return FAILURE, NOT_SUPPORTED


class NodeManagerFunctionsWin(NodeManagerFunctionsBase):
    def killChromes(self):
        logging.info("Executing killChromes request")
        return SUCCESS, getCommandExecutionResponse("taskkill /F /IM chrome.exe")
        # return SUCCESS

    def killChromeDrivers(self):
        logging.info("Executing killChromedrivers request")
        # _executeCommand("taskkill /F /IM chromedriver.exe", silently=True)
        return SUCCESS, getCommandExecutionResponse("taskkill /F /IM chromedriver.exe")
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


def executeCommandInShell(command, silently=False):
    devnull = open(os.devnull, 'w') if silently else None
    return subprocess.call(shlex.split(command), shell=True, stdout=devnull, stderr=devnull)


def executeCommand(command, silently=False):
    devnull = open(os.devnull, 'w') if silently else None
    return subprocess.call(shlex.split(command), shell=False, stdout=devnull, stderr=devnull)


def getCommandExecutionResponse(command):
    try:
        output = subprocess.check_output(shlex.split(command), shell=False, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        output = e.output
    logging.debug(output)
    return output


def md5_for_file(fileName, block_size=2 ** 20):
    with open(fileName, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def is_path_allowed(path):
    wrong_path = "Saving outside working directory not allowed, use relative path wisely or proper absolute path"
    file_exists = "File exists in filesystem, cannot overwrite"
    if not os.getcwd() in os.path.abspath(path):
        logging.warn("Tried to save outside working directory: " + path)
        return {"status": FAILURE, "errorMsg": wrong_path}
    if os.path.isfile(path):
        logging.warn("Tried to overwrite existing file: " + path)
        return {"status": FAILURE, "errorMsg": file_exists}
    return {"status": SUCCESS, "errorMsg": None}


def get_path_and_size_of(path):
    return os.path.abspath(path) + " (" + sizeof_fmt(os.path.getsize(path)) + ")"


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-P", "--port", dest="port", default=5005, type="int",
                      help="node-manager port [default: 5005]")
    parser.add_option("-l", "--log-requests", action="store_true", dest="logRequests", default=False,
                      help="enables logging requests [default: False]")
    (options, args) = parser.parse_args()
    s = getNodeManager('', options.port, options.logRequests, loggerLevel=logging.DEBUG)

    s.start()