#!/usr/bin/python

import select
import errno

#-----------------------------------------------------------------------------

class Poll:
    '''
    Convenience wrapper around :mod:`select` module.
    '''

    def __init__(self, handles = []):
        self._poll = select.poll()
        self._object_map = {}

        for h in handles:
            self.add(h)

    def add(self, handle):
        '''
        :param handle: file handle (e.g. :obj:`file` object, but anything with
          :meth:`fileno` method)
        :return: ``True`` if the handle was added to poll list, ``False``
          otherwise (either handle is not pollable or was already in poll list)

        Add a handle to poll list. If ``handle.fileno()`` returns ``None``,
        the handle is not added. The same stands for objects that already were
        added (check is based on file descriptor).
        '''
        if handle.fileno() is None:
            return False
        if handle.fileno() in self._object_map:
            return False

        # remember for later
        self._object_map[handle.fileno()] = handle
        self._poll.register(handle, select.POLLIN)
        return True

    def remove(self, handle):
        '''
        :param handle: file handle, the same as for :meth:`add`

        Remove file handle from poll list. Handle must still return valid file
        descriptor on ``handle.fileno()`` call.
        '''
        if handle.fileno() is None:
            return
        if handle.fileno() not in self._object_map:
            return
        del self._object_map[handle.fileno()]
        self._poll.unregister(handle)

    def __contains__(self, handle):
        '''
        :param handle: file handle, the same as for :meth:`add`

        Check if the handle is in poll list.
        '''
        return (handle.fileno() is not None) and \
               (handle.fileno() in self._object_map)

    def poll(self, timeout = 100):
        '''
        :param timeout: timeout in milliseconds for *poll* operation
        :return: list of file handles added with :meth:`add` method

        Check whether any data arrives on descriptors. File handles
        (*handles*, not *descriptors*) that are ready for reading are returned
        as a list.

        Method works around calls interrupted by signals (terminates early
        instead of throwing an exception).
        '''
        try:
            result = self._poll.poll(timeout)
            return [self._object_map[r[0]] for r in result]
        except select.error, e:
            if e.args[0] == errno.EINTR: # in case some signal arrives
                return []
            else: # other error, rethrow
                raise e

    def count(self):
        '''
        Count the descriptors added to the poll.
        '''
        return len(self._object_map)

    def empty(self):
        '''
        Check if the poll is empty (no descriptors).
        '''
        return (len(self._object_map) == 0)

#-----------------------------------------------------------------------------
# vim:ft=python
