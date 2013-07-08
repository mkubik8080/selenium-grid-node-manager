import os
import sys
import argparse

from src import service
from src.nodemanager import getNodeManager
from src.daemon import Daemon

# basic configuration
PORT = 5005
SERVICE_NAME = "selenium-node-manager"
SERVICE_DESCRIPTION = "Selenium Node Manager - Sabre QA"


class NodeManagerService(service.Service):
    logFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'manager.log')
    nodeManager = getNodeManager('', 5005, logRequests=True, loggerFile=logFile, loggerLevel=10)

    _svc_name_ = SERVICE_NAME
    _svc_description_ = SERVICE_DESCRIPTION

    def start(self):
        self.runflag = True
        while self.runflag:
            self.log("Starting service")
            self.nodeManager.start(os.path.dirname(os.path.realpath(__file__)))

    def stop(self):
        self.log("Stopping service")
        self.nodeManager.stop()
        self.runflag = False

    def restart(self):
        self.stop()
        self.start()


class NodeManagerDaemon(Daemon):
    def run(self):
        pass


def parseOptions():
    parser = argparse.ArgumentParser(description='selenium-node-manager runner')
    sp = parser.add_subparsers()

    sp_start = sp.add_parser('start', help='Starts %(prog)s daemon/service')
    sp_start.add_argument("-p", "--port", dest="port", default=5005, type=int,
                          help="node-manager port, default is 5005")
    sp_start.add_argument("-l", "--log-requests", action="store_true", dest="logRequests", default=False,
                          help="enables logging requests")
    sp_start.set_defaults(func=start)

    sp_stop = sp.add_parser('stop', help='Stops %(prog)s daemon/service')
    sp_stop.set_defaults(func=stop)
    sp_uninstall = sp.add_parser('uninstall', help='Stops and removes %(prog)s daemon/service')
    sp_uninstall.set_defaults(func=uninstall)
    sp_restart = sp.add_parser('restart', help='Restarts %(prog)s daemon/service')
    sp_restart.set_defaults(func=restart)

    return parser.parse_args()


def start(args):
    if 'win' in sys.platform:
        service.instart(NodeManagerService, SERVICE_NAME, SERVICE_DESCRIPTION)
    else:
        pass
        # daemon = NodeManagerDaemon("node-manager.pid")
        # daemon.start()


def stop(args):
    if 'win' in sys.platform:
        service.stop(NodeManagerService, SERVICE_NAME)
    else:
        pass
        # daemon.stop()


def uninstall(args):
    if 'win' in sys.platform:
        service.uninstall(NodeManagerService, SERVICE_NAME)
    else:
        pass


def restart(args):
    # service.restart() ->  do sth like -> restart(node-manager)
    # daemon.restart()
    print 'restarted...'
    print args


if __name__ == '__main__':
    args = parseOptions()
    args.func(args)
