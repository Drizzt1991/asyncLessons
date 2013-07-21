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


def http_parser():
    out, buf = yield
    try:
        # Read header
        # Header ends on `\r\n\r\n`
        header = yield from buf.readuntil(
            b'\r\n\r\n',
            1 << 20,  # Max a MB
            RuntimeError
        )
        # Body must be read based on content length, but... lets just read as
        # much as we can
        try:
            body = yield from buf.readsome()
        except tulip.EofStream:
            body = b''
        out.feed_data(header+b'\r\n\r\n'+body)
    except tulip.EofStream:
        pass
    out.feed_eof()


def download_single(loop, url):
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path
    t, p = yield from loop.create_connection(tulip.StreamProtocol, host, port)
    stream = p.set_parser(http_parser())
    # Create request
    request = (
            b'GET ' + path.encode('ascii') + b' HTTP/1.1\n' +
            b'HOST: ' + host.encode('ascii') + b'\n' +
            b'\r\n')
    # Send it
    t.write(request)
    # And yield result from our stream.
    return (yield from stream.read())


def download(url, retries=3, sleep=5, loop=None):
    loop = loop or tulip.get_event_loop()
    print('DOWNLOADING', url)
    data = None
    for i in range(retries):
        try:
            data = yield from download_single(loop, url)
        except Exception:
            print("FAILED TO DOWNLOAD", url, "RETRYING.")
            yield from tulip.sleep(sleep)
        else:
            break
    else:
        print("FAILED TO DOWNLOAD", url)
        return
    return data


@tulip.task
def process_downloads():
    data1 = yield from download('http://example.com')
    data1 and print("RECEIVED", len(data1), "B OF DATA")
    data2 = yield from download('http://google.com')
    data2 and print("RECEIVED", len(data2), "B OF DATA")
    data3 = yield from download('http://some_lame_address_1111.com')
    data3 and print("RECEIVED", len(data3), "B OF DATA")


def main():
    # url = len(sys.argv) > 1 and sys.argv[1] or 'http://example.com/'
    loop = tulip.get_event_loop()
    loop.run_until_complete(process_downloads())

if __name__ == "__main__":
    main()
