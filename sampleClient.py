import os
import socket
import xmlrpclib
import argparse
import hashlib

# provide urls to servers running selenium-grid-node-manager instances
# schema is hardcoded to http and port to 5005 for convenience
# feel free to modify the code

nodes = ["node1_url", "node2_url"]
clients = []


class TimeoutTransport(xmlrpclib.Transport):
    """
    Custom XML-RPC transport class for HTTP connections, allowing a timeout in
    the base connection.
    """

    def __init__(self, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, use_datetime=0):
        xmlrpclib.Transport.__init__(self, use_datetime)
        self._timeout = timeout

    def make_connection(self, host):
        conn = xmlrpclib.Transport.make_connection(self, host)
        conn.timeout = self._timeout
        return conn


def initializeClients():
    t = TimeoutTransport(timeout=1)
    for node in nodes:
        client = xmlrpclib.ServerProxy('http://{0}:5005'.format(node), transport=t)
        try:
            if client.status()[0]:
                print ' {0} is alive'.format(node)
            clients.append(client)
        except Exception:
            print ' {0} is dead'.format(node)


def killChromes():
    for client in clients:
        print client.killChromes()[1]


def killChromeDrivers():
    for client in clients:
        print client.killChromeDrivers()[1]


def uploadFile(args):
    DEST = args.dest or os.path.basename(args.source)
    SOURCE_FILE = args.source

    for client in clients:
        fileHash = md5_for_file(SOURCE_FILE)
        with open(SOURCE_FILE, 'rb') as file:
            response = write_file_in_chunks(client, file, DEST)
            # response = write_file_at_once(client, file, DEST)

            if response[0]:
                print "file successfully sent, hashes are:\n\t" + response[1] + "\n\t" + fileHash
                if response[1] != fileHash:
                    print "unfortunatelly hases are different"

            else:
                print "ups..., something went wrong:\n\t" + response[1]


###################### support methods ######################
def md5_for_file(fileName, block_size=2 ** 20):
    with open(fileName, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def read_in_chunks(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def write_file_at_once(s, file, dest):
    data = file.read()
    response = s.writeFile(xmlrpclib.Binary(data), dest)
    return response


def write_file_in_chunks(s, file, dest):
    for chunk in read_in_chunks(file, 2 * 1024 * 1024):
        response = s.writeFileChunk(xmlrpclib.Binary(chunk), dest)
        if not response[0]:
            return False, "sth went wrong while writing file chunk\n\t" + response[1]
        print " - chunk written"
    response = s.finalizeChunkedFile(dest)
    return response


##################### script execution control #####################


def parseOptions():
    parser = argparse.ArgumentParser(description='selenium-node-manager example client runner')
    sp = parser.add_subparsers()

    sp_killChromes = sp.add_parser('killChromes',
                                   help='kills any chrome processes that could be running on defined endpoints')
    sp_killChromes.set_defaults(func=killChromes)

    sp_killChromeDrivers = sp.add_parser('killChromeDrivers',
                                         help='kills any chromedriver processes that could be running on defined endpoints')
    sp_killChromeDrivers.set_defaults(func=killChromeDrivers)

    sp_uploadFile = sp.add_parser('uploadFile', help='uploads provided file to defined endpoints')
    sp_uploadFile.add_argument("-f", "--file", dest="source", help="file to be uploaded")
    sp_uploadFile.add_argument("-d", "--destination", dest="dest", default="",
                               help="optional destination on defined endpoints")
    sp_uploadFile.set_defaults(func=uploadFile)

    return parser.parse_args()


if __name__ == '__main__':
    args = parseOptions()
    initializeClients()
    args.func(args)
