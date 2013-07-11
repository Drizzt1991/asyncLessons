#### -*- coding:utf-8 -*- #######

import hashlib
import struct
import time


class Package:
    """ Package description
        HEADER
        bytes | name     | description
        ------------------------------------------------------------------------
        4     | length   | Full length of package without header
        2     | type     | Type of data passed in package.
              |          | TODO: For now we ignore this, and think all data
              |          | is bynary(`0 `).
        32    | checksum | The checksum of package.
              |          | TODO: Not too big?
        N     | data     | `length` bytes of bynary data.
    """

    HEADER_STRUCT = "IH32s"
    HEADER_SIZE = struct.calcsize(HEADER_STRUCT)


def package_write(package):
    """ Forms packages, that will be sent by socket.
        Forms a new, packaged byte buffer from passed one.
    """
    size = len(package)
    data_type = 0
    md5 = hashlib.md5(package).hexdigest().encode('ascii')
    header = struct.pack(Package.HEADER_STRUCT, size, data_type, md5)
    return header+package


def package_read(bytes):
    """ Can form packages based on socket input.
        Idea is to feed the reader binary data streem and ask it to find
        package(s) in it.

        Returns a tuple: (packages, tail), where packages is a list of found
        packages and tail is the data, that is not a full package.

        Raises a BrokenPackage error if one(or more) package(s) in data was
        broken(checksum validatation failed). Can also be raised if header was
        invalid.
    """
    packages = []
    while True:
        header = bytes[:Package.HEADER_SIZE]
        try:
            size, data_type, checksum = \
                struct.unpack(Package.HEADER_STRUCT, header)
        except struct.error as error:
            # assume the header is not full
            break
        # For now we have 1 format `0` as of bytes
        if data_type != 0:
            raise BrokenPackage()
        # Extract package data
        package_data = bytes[Package.HEADER_SIZE:Package.HEADER_SIZE+size]
        if len(package_data) != size:
            # assume the package is not full
            break
        # Validate package data
        signature = hashlib.md5(package_data).hexdigest().encode('ascii')
        if signature != checksum:
            raise BrokenPackage()
        # Ok, the package is valid. Save it and continue
        packages.append(package_data)
        # Trim bytes for next iteration
        bytes = bytes[Package.HEADER_SIZE+size:]
    # return package and the tail, that is left in bytes
    return packages, bytes


class PackagedConnection(object):
    """ An adapter around a socket to send and recv packaged data
        conn = PackagedConnection(s)
        conn.send(b'PING') # Send `PING` package
        pong = conn.recv() # Recv 'PONG' package
    """

    def __init__(self, socket):
        self.socket = socket
        self.read_buffer = b''
        self.read_packages = []

    def send(self, package_data):
        """
            throws:
                ClientDisconnected
        """
        package = package_write(package_data)
        try:
            self.socket.sendall(package)
        except OSError:
            self.socket.close()
            raise ClientDisconnected()

    def recv_block(self):
        """ Read until a package is formed
        """
        package = None
        while package is None:
            try:
                package = self.recv()
            except BlockingIOError:
                time.sleep(0.001)
        return package

    def recv(self):
        """
            throws:
                BlockingIOError
                ClientDisconnected
                BrokenPackage
        """
        if len(self.read_packages) == 0:
            try:
                recv_data = self.socket.recv((1 << 10) * 16)
            except BlockingIOError:
                # For now we raise it, cause do not know how to process.
                raise
            except OSError:
                self.socket.close()
                raise ClientDisconnected()

            if recv_data:
                self.read_buffer += recv_data
            else:
                self.socket.close()
                raise ClientDisconnected()
            self.read_packages, self.read_buffer = package_read(self.read_buffer)
        if len(self.read_packages) > 0:
            return self.read_packages.pop(0)

    def close(self):
        self.socket.close()


class BrokenPackage(Exception):

    def __init__(self):
        """ TODO: insert some valible info here """
        pass


class ClientDisconnected(Exception):

    def __init__(self):
        pass

    # def __init__(self, socket):
    #     self.socket = socket
    #     self.buffer = b""

    # def read_exact(self, bytes):
    #     res = self.buffer
    #     self.buffer = b""
    #     while len(res) < bytes:
    #         data = self.socket.recv(4096)
    #         if not data:
    #             raise Disconnected()
    #         else:
    #             res += data
    #     if len(res) > bytes:
    #         res, self.buffer = res[:bytes], res[bytes:]
    #     if len(res) < bytes:
    #         raise ReadOverhead()
    #     return res

    # def read_package(self):
    #     header = self.read_exact(Header.HEADER_SIZE)
    #     header = Header.unpack(header)
    #     package_data = self.read_exact(header.size)
    #     return package_data

    # def write_package(self, package):
    #     header = Header(size=len(package))
    #     data = header.pack() + package
    #     self.socket.sendall(data)
