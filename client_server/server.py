#### -*- coding:utf-8 -*- #######

import socket
from protocol import PackagedConnection, ClientDisconnected, BrokenPackage
from threading import Thread

PING = b"PING"
PONG = b"PONG"
CLOSE = b"CLOSE"

class Server(object):
    """ Simple one thread server, that can process 1 user at a time.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def listen(self):
        """ Starts listening on port. Will block forever
        """
        # Create the listening socket
        s = self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Good for development, no need to wait socket closing.
        # TODO: Is this good for production?
        s.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR, 1)
        # Bind it to specified port
        s.bind((self.host, self.port))
        # Ok, so we binded to our socket
        s.listen(10)
        # Ok, we listen on this port. Now our `s` socket is passive and can accept

        while True:
            # Wait for 1 client to connect
            client, addr = s.accept()

            # Must not raise exceptions
            self.process_client(client, addr)

    def process_client(self, client, addr):
        """ Receive a handshake and echo packages until closed
        """
        print("Client", addr, "connected")
        conn = PackagedConnection(client)
        try:
            # Perform PING-PONG handshake
            hello_package = conn.recv_block()
            if hello_package != PING:
                conn.close()
                return
            conn.send(PONG)
            # Recv packages until we close connection
            while True:
                echo_package = conn.recv_block()
                if echo_package != CLOSE:
                    conn.send(echo_package)
                else:
                    break
        except ClientDisconnected:
            # Client disconnected
            conn.close()
        except BrokenPackage:
            # Connection broken, but maybe we can still disconnect gracefuly
            try:
                conn.send(CLOSE)
            except ClientDisconnected:
                pass
            conn.close()
        else:
            # Client exited gracefully
            conn.close()


class ThreadingServer(Server):
    """ Executes the process_client in a separate thread
    """

    def process_client(self, client, addr):
        super_method = super(ThreadingServer, self).process_client
        Thread(target=super_method, args=(client, addr)).start()


def main():
    server = ThreadingServer('localhost', 7777)
    server.listen()

if __name__ == "__main__":
    main()
