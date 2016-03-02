#!/usr/bin/python

import socket
import errno
import os
import sha
import fcntl

#-----------------------------------------------------------------------------

class Source(object):
    def open(self):
        raise NotImplementedError()

    def reopen(self):
        raise NotImplementedError()

    def reopen_necessary(self):
        return False

    def flush(self):
        pass

    def poll_makes_sense(self):
        return True

    def is_opened(self):
        return (self.fileno() is not None)

    def fileno(self):
        raise NotImplementedError()

    def try_readlines(self):
        raise NotImplementedError()

#-----------------------------------------------------------------------------

class FileHandleSource(object):
    def __init__(self, fh = None):
        self.fh = fh
        self.read_buffer = []

    def open(self):
        fd = self.fh.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def reopen(self):
        pass

    def reopen_necessary(self):
        return False

    def flush(self):
        pass

    def fileno(self):
        return self.fh.fileno()

    def try_readlines(self):
        if self.fh is None:
            return

        try:
            while True:
                read = self.fh.read(1024)
                if read == "": # EOF
                    break # FIXME: what with `self.read_buffer'?
                if "\n" in read:
                    read = "".join(self.read_buffer) + read
                    del self.read_buffer[:]

                    lines = read.split("\n")
                    if lines[-1] != "":
                        self.read_buffer.append(lines[-1])
                    for line in lines[:-1]:
                        yield line
        except IOError, e:
            if e.errno == errno.EWOULDBLOCK or e.errno == errno.EAGAIN:
                pass # OK, just no more data to read at the moment
            else:
                raise # other error, rethrow

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
            if stat_line != '' and stat_line.endswith("\n"):
                # full line was read
                try:
                    (dev, inode, pos) = stat_line.split()
                    dev   = int(dev, 0)   # hex number
                    inode = int(inode, 0) # hex number
                    pos   = int(pos)      # dec number
                except ValueError:
                    # either unpack failed or one of the int() failed
                    dev   = None
                    inode = None
                    pos   = None
            else:
                # partial line or EOF means damaged status file
                dev   = None
                inode = None
                pos   = None
            return (dev, inode, pos)

        def update(self, dev, inode, pos):
            self.fh.seek(0)
            self.fh.write("0x%08x 0x%08x %d\n" % (dev, inode, pos))
            self.fh.truncate()
            self.fh.flush()

        def truncate(self):
            self.fh.seek(0)
            self.fh.truncate()

    # }}}
    #------------------------------------------------------

    def __init__(self, filename, state_dir):
        self.filename = filename
        self.fh = None
        self.dev = None
        self.inode = None
        self.read_buffer = None

        self.state_dir = state_dir
        position_filename = "%s.pos" % (sha.sha(self.filename).hexdigest(),)
        position_filename = os.path.join(self.state_dir, position_filename)
        self.position_file = FileSource.PositionFile(position_filename)

    def __del__(self):
        if self.fh is not None:
            self._write_position()

    def open(self):
        try:
            self.fh = open(self.filename)
        except (IOError, OSError):
            return
        self._rewind()

    def reopen(self):
        # TODO: read until the EOF?
        self.fh.close()
        self.fh = None
        self.dev = None
        self.inode = None
        # NOTE: non-empty read_buffer from previous file causes wrong file
        # position to be written to state file
        self.read_buffer = None # TODO: or save it somewhere?
        try:
            self.fh = open(self.filename)
        except (IOError, OSError):
            return
        (self.dev, self.inode, _size) = FileSource.stat(fh = self.fh)
        self._write_position()

    def reopen_necessary(self):
        (dev, inode, size) = FileSource.stat(path = self.filename)
        if (dev, inode) == (None, None) or size < self.fh.tell():
            # file has been removed (or truncated)
            self._file_removed()
            return True
        return (dev, inode) != (self.dev, self.inode)

    def flush(self):
        self._write_position()

    def poll_makes_sense(self):
        return False

    def fileno(self):
        if self.fh is None:
            return None
        return self.fh.fileno()

    def try_readlines(self):
        if self.fh is None:
            return
        while True:
            line = self.fh.readline()
            if line.endswith("\n"):
                # proper line with EOL marker
                line = line.rstrip("\n")
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

    def __str__(self):
        return "file: %s" % (self.filename,)

    #------------------------------------------------------
    # stuff around the position in logfile {{{

    def _rewind(self):
        (self.dev, self.inode, size) = FileSource.stat(fh = self.fh)
        (dev, inode, pos) = self.position_file.read()
        if (self.dev, self.inode) == (dev, inode) and pos <= size:
            self.fh.seek(pos)
        else:
            # either the position file is for other (possibly removed) logfile
            # or the logfile shrinked, meaning it was truncated or even
            # removed and recreated
            self._write_position()

    def _file_removed(self):
        self.dev = None
        self.inode = None
        self.position_file.truncate()

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
            # only this stat() can fail
            try:
                stat = os.stat(path)
            except (IOError, OSError):
                return (None, None, None)
        elif fh is not None:
            stat = os.fstat(fh.fileno())
        return (stat.st_dev, stat.st_ino, stat.st_size)

#-----------------------------------------------------------------------------

class UDPSource(Source):
    def __init__(self, host, port):
        if host is None or host == "":
            self.host = ""
        else:
            self.host = host
        self.port = port
        self.socket = None

    def open(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.host, self.port))
            self.socket = sock
        except (IOError, OSError):
            pass

    def __del__(self):
        if self.socket is not None:
            self.socket.close()

    def fileno(self):
        if self.socket is None:
            return None
        return self.socket.fileno()

    def try_readlines(self):
        try:
            while True:
                msg = self.socket.recv(4096, socket.MSG_DONTWAIT)
                yield msg.rstrip("\n")
        except socket.error, e:
            if e.errno == errno.EWOULDBLOCK or e.errno == errno.EAGAIN:
                # this is expected when there's nothing in the socket queue
                return
            else:
                raise # other error, rethrow

    def __str__(self):
        if self.host == "":
            host = "*"
        else:
            host = self.host
        return "UDP: %s:%d" % (host, self.port)

#-----------------------------------------------------------------------------

# TODO: implement reopen_necessary() and reopen()
class UNIXSource(Source):
    def __init__(self, path):
        self.path = path
        self.socket = None

    def __del__(self):
        if self.socket is not None:
            self.socket.close()
            os.unlink(self.path)

    def open(self):
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.bind(self.path)
            self.socket = sock
        except (IOError, OSError):
            pass

    def fileno(self):
        if self.socket is None:
            return None
        return self.socket.fileno()

    def try_readlines(self):
        try:
            while True:
                msg = self.socket.recv(4096, socket.MSG_DONTWAIT)
                yield msg.rstrip("\n")
        except socket.error, e:
            if e.errno == errno.EWOULDBLOCK or e.errno == errno.EAGAIN:
                # this is expected when there's nothing in the socket queue
                return
            else:
                raise # other error, rethrow

    def __str__(self):
        return "UNIX: %s" % (self.path)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
