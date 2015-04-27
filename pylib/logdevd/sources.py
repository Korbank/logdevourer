#!/usr/bin/python

import socket
import errno
import os
import sha

#-----------------------------------------------------------------------------

class Source(object):
    def fileno(self):
        raise NotImplementedError()

    def try_readlines(self):
        raise NotImplementedError()

    def reopen_if_necessary(self):
        pass

#-----------------------------------------------------------------------------

class FileSource(Source):
    #------------------------------------------------------
    # PositionFile helper class {{{

    class PositionFile:
        def __init__(self, filename):
            self.filename = filename
            # NOTE: do not truncate the file
            fd = os.open(self.filename, os.O_RDWR | os.O_CREAT, 0666)
            self.fh = os.fdopen(fd, 'r+')

        def read(self):
            self.fh.seek(0)
            stat_line = self.fh.readline()
            if stat_line != '':
                # TODO: catch errors
                (dev, inode, pos) = stat_line.split()
                dev   = int(dev, 0)   # hex number
                inode = int(inode, 0) # hex number
                pos   = int(pos)      # dec number
            else:
                dev   = None
                inode = None
                pos   = None
            return (dev, inode, pos)

        def update(self, dev, inode, pos):
            self.fh.seek(0)
            self.fh.write("0x%08x 0x%08x %d\n" % (dev, inode, pos))
            self.fh.flush()

    # }}}
    #------------------------------------------------------

    def __init__(self, filename, state_dir):
        self.filename = filename
        self.fh = open(self.filename)

        self.state_dir = state_dir
        position_filename = "%s.pos" % (sha.sha(self.filename).hexdigest(),)
        position_filename = os.path.join(self.state_dir, position_filename)
        self.position_file = FileSource.PositionFile(position_filename)

        (self.dev, self.inode) = FileSource.stat(fh = self.fh)

        self.read_buffer = None

        self._rewind()

    def __del__(self):
        self._write_position()

    def fileno(self):
        return self.fh.fileno()

    def try_readlines(self):
        while True:
            line = self.fh.readline()
            if line.endswith("\n"):
                line = line.rstrip("\n")
                # proper line with EOL marker
                if self.read_buffer is not None:
                    yield self.read_buffer + line
                    self.read_buffer = None
                else:
                    yield line
            elif line != "":
                # partial line, EOF must have been encountered
                if self.read_buffer is not None:
                    self.read_buffer += line
                else:
                    self.read_buffer = line
                break
            else: # line == ""
                # EOF, no partial line read
                break

    def reopen_if_necessary(self):
        new_fh = open(self.filename)
        new_fh_stat = FileSource.stat(fh = new_fh)
        if (self.dev, self.inode) != new_fh_stat:
            # TODO: read until the EOF?
            self.fh.close()
            self.read_buffer = None # TODO: or save it somewhere?
            self.fh = new_fh
            (self.dev, self.inode) = new_fh_stat
            self._write_position()

    #------------------------------------------------------
    # stuff around the position in logfile {{{

    def _rewind(self):
        (dev, inode, pos) = self.position_file.read()
        if (self.dev, self.inode) == (dev, inode):
            self.fh.seek(pos)
        else:
            self._write_position()

    def _write_position(self):
        if self.read_buffer is None:
            pos = self.fh.tell()
        else:
            # incomplete line, so we'll take previous EOL position
            pos = self.fh.tell() - len(self.read_buffer)
        self.position_file.update(self.dev, self.inode, pos)

    # }}}
    #------------------------------------------------------

    @staticmethod
    def stat(path = None, fh = None):
        if path is not None:
            stat = os.stat(path)
        elif fh is not None:
            stat = os.fstat(fh.fileno())
        return (stat.st_dev, stat.st_ino)

#-----------------------------------------------------------------------------

class UDPSource(Source):
    def __init__(self, host, port):
        if host is None or host == "":
            self.host = ""
        else:
            self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

    def __del__(self):
        self.socket.close()

    def fileno(self):
        return self.socket.fileno()

    def try_readlines(self):
        try:
            while True:
                msg = self.socket.recv(4096, socket.MSG_DONTWAIT)
                yield msg.rstrip("\n")
        except socket.error, e:
            if e.errno == errno.EWOULDBLOCK:
                # this is expected when there's nothing in the socket queue
                return
            raise e

#-----------------------------------------------------------------------------

class UNIXSource(Source):
    def __init__(self, path):
        self.path = path
        self.socket = None
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(self.path)
        self.socket = sock

    def __del__(self):
        if self.socket is not None:
            self.socket.close()
            os.unlink(self.path)

    def fileno(self):
        return self.socket.fileno()

    def try_readlines(self):
        try:
            while True:
                msg = self.socket.recv(4096, socket.MSG_DONTWAIT)
                yield msg.rstrip("\n")
        except socket.error, e:
            if e.errno == errno.EWOULDBLOCK:
                # this is expected when there's nothing in the socket queue
                return
            raise e

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
