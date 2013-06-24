import argparse
import sys
from src import service
from src.nodemanager import getNodeManager
from src.daemon import Daemon

# basic configuration
PORT = 5005
SERVICE_NAME = "selenium-node-manager"
SERVICE_DESCRIPTION = "Selenium Node Manager - Sabre QA"


class NodeManagerService(service.Service):
    nodeManager = getNodeManager('', 5005, logRequests=True)

    def start(self):
        self.runflag = True
        while self.runflag:
            self.log("starting...")
            self.nodeManager.start()
            self.log("probably done ;)")

    def stop(self):
        self.log("stopping..")
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
    sp_stop = sp.add_parser('uninstall', help='Stops and removes %(prog)s daemon/service')
    sp_stop.set_defaults(func=uninstall)
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