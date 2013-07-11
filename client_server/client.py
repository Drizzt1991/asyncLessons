#### -*- coding:utf-8 -*- #######

import socket
from protocol import PackagedConnection, ClientDisconnected, BrokenPackage
from server import PING, PONG, CLOSE
from threading import Thread


def main():
    test_data = [
        b"SOME DATA",
        b"B"*5000,
        b"",
        b"1234567890",
        b"LOL"
    ]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect(('127.0.0.1', 7777))
    conn = PackagedConnection(s)
    # Simplified handshake. If something failes on client - just die
    conn.send(PING)
    # print('SENDING PING')
    server_pong = conn.recv()
    assert server_pong == PONG, server_pong
    # print('HANDSHAKE OK')

    for i, data in enumerate(test_data):
        conn.send(data)
        # print(i, conn.recv() == data)

    conn.send(CLOSE)
    conn.close()

if __name__ == "__main__":
    # Spam server with connections
    count = 0

    def execute():
        main()
        # Not executed if error
        global count
        count += 1
    threads = [Thread(target=execute) for i in range(1000)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    print('Finished successfuly', count)
