#!/usr/bin/python
#
# NOTE: all these destination types are JSON-per-line based (EOL markers will
# be added as necessary)
#

import socket
import time
import sys

#-----------------------------------------------------------------------------

class STDOUTDestination:
    def send(self, line):
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

#-----------------------------------------------------------------------------

class TCPDestination:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def _disconnect(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def _connect(self):
        def try_connect():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                return sock
            except socket.error:
                return None

        self._disconnect()
        self.sock = try_connect()

        while self.sock is None:
            time.sleep(0.1)
            self.sock = try_connect()

    def send(self, line):
        line += "\n"

        # on error, disconnect and try to reconnect
        # FIXME: on broken connection (even to localhost) one line will most
        # probably be lost, but I don't see what could I do to prevent this
        # happening
        while True:
            if self.sock is None:
                self._connect()
            try:
                self.sock.send(line)
                return
            except socket.error:
                self._disconnect()

#-----------------------------------------------------------------------------

class UDPDestination:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, line):
        # XXX: ignore send errors
        try:
            self.sock.sendto(line, (self.host, self.port))
        except socket.error:
            pass

#-----------------------------------------------------------------------------

class UNIXDestination:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    def send(self, line):
        # XXX: ignore send errors
        try:
            self.sock.sendto(line, self.path)
        except socket.error:
            pass

#-----------------------------------------------------------------------------
# vim:ft=python
