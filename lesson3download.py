################### -*- coding:utf-8 -*- #################
# Just a package

import sys
import re
import tulip
import tulip.http
import tulip.locks
from tulip.protocols import Protocol
from urllib.parse import urlparse

valid_http_responce = re.compile("^HTTP\/1\.\d (\d+)")


class HTTPProtocol(Protocol):

    def __init__(self):
        super(HTTPProtocol, self).__init__()
        self._on_ok = lambda x: None
        self._on_error = lambda: None

    def connection_made(self, transport):
        self.transport = transport
        print('Connection made')

    def data_received(self, data):
        # A valid package
        match = valid_http_responce.match(data.decode('ascii'))
        # Valid are 2XX and 3XX responces
        if match:
            if match.group(1)[0] in ['2', '3']:
                self.on_ok(data)
            else:
                self.on_error(ValueError(
                    'Returned {} status code.'.format(match.group(1))))
        # Received garbage
        else:
            self.on_error(ValueError('Data corrupted'))

    def eof_received(self):
        pass
        # print("RECEIVED EOF")

    def connection_lost(self, exc):
        pass
        print("CONNECTION LOST", exc)

    def on_ok(self, cb):
        self._on_ok = cb

    def on_error(self, cb):
        self._on_error = cb


def create_connection_with_cb(on_result, on_error, loop, *args, **kw):
    """ Calls loop.create_connection and runs it to the end.
        On done calls on_result callback
    """
    task = tulip.Task(
        loop.create_connection(*args, **kw), loop=loop)
    def dispatch_result(task):
        try:
            on_result(*task.result())
        except OSError as exc:
            on_error(exc)
    task.add_done_callback(dispatch_result)


def retriable_download(url, on_ok, on_error, retries=2, sleep=1, loop=None):
    loop = loop or tulip.get_event_loop()
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path

    def retry_on_error(exc):
        print("ERROR {}. Retrying after {} s. Number or retries {}"
                .format(exc, sleep, retries))
        loop.call_later(
            sleep,
            retriable_download,
            url, on_ok, on_error, retries-1, sleep, loop)

    error_cb = on_error if retries == 0 else retry_on_error

    # We wait for addrinfo to be resolved. When it is this func will be called.
    def got_connection(transport, protocol):
        # Set callbacks on data received
        protocol.on_ok = on_ok
        protocol.on_error = error_cb
        # Send request to transport. Responce will be handled by callbacks.
        request = (
            b'GET ' + path.encode('ascii') + b' HTTP/1.1\n' +
            b'HOST: ' + host.encode('ascii') + b'\n' +
            b'\r\n')
        transport.write(request)
    # We do not want our callback's based code to be mixed in corutines code.
    create_connection_with_cb(
        got_connection, error_cb, loop, HTTPProtocol, host, port)


@tulip.task
def download(url, lock):
    loop = tulip.get_event_loop()
    print('DOWNLOADING', url)
    retriable_download(
        url,
        on_ok=lambda x: print("RECEIVED OK", len(x)),
        on_error=lambda exc: print("RECEIVED ERROR", exc),
        loop=loop
    )


def main():
    url = len(sys.argv) > 1 and sys.argv[1] or 'http://example.com/'
    loop = tulip.get_event_loop()
    lock = tulip.locks.Lock()
    loop.call_soon(download, 'http://example.com', lock)
    loop.call_later(4, download, 'http://google.com', lock)
    loop.call_later(8, download, 'http://some_lame_address_1111.com', lock)
    loop.run_until_complete(tulip.sleep(20))

if __name__ == "__main__":
    main()
