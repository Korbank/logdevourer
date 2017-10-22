#!/usr/bin/python
#
# Logging handlers. Classes copied from Seismometer Toolbox project.
#
# NullHandler is provided for Python 2.6 compatibility (since I already added
# logging_config module, I could add this handler as well). SysLogHandler is
# provided to improve robustness, as Python's logging.handlers.SysLogHandler
# throws a typically uncaught exception when syslog daemon is down.
#
#-----------------------------------------------------------------------------

import logging
import syslog

#-----------------------------------------------------------------------------

class NullHandler(logging.Handler):
    '''
    Sink log handler. Used to suppress logs.
    '''
    def __init__(self):
        super(NullHandler, self).__init__()

    def emit(self, record):
        pass

    def handle(self, record):
        pass

class SysLogHandler(logging.Handler):
    '''
    Syslog log handler. This one works a little better than
    :mod:`logging.handlers.SysLogHandler` with regard to syslog restarts and
    is independent from log socket location. On the other hand, it only logs
    to locally running syslog.

    This handler requires two fields to be provided in configuration:
    ``"facility"`` (e.g. ``"daemon"``, ``"local0"`` through
    ``"local7"``, ``"syslog"``, ``"user"``) and ``"process_name"``, which will
    identify the daemon in logs.
    '''

    # some of the facilities happen to be missing in various Python
    # installations
    _FACILITIES = dict([
        (n, getattr(syslog, "LOG_" + n.upper()))
        for n in [
            "auth", "authpriv", "cron", "daemon", "ftp", "kern",
            "local0", "local1", "local2", "local3",
            "local4", "local5", "local6", "local7",
            "lpr", "mail", "news", "syslog", "user", "uucp",
        ]
        if hasattr(syslog, "LOG_" + n.upper())
    ])
    _PRIORITIES = { # shamelessly stolen from logging.handlers:SysLogHandler
        "alert":    syslog.LOG_ALERT,
        "crit":     syslog.LOG_CRIT,
        "critical": syslog.LOG_CRIT,
        "debug":    syslog.LOG_DEBUG,
        "emerg":    syslog.LOG_EMERG,
        "err":      syslog.LOG_ERR,
        "error":    syslog.LOG_ERR,        #  DEPRECATED
        "info":     syslog.LOG_INFO,
        "notice":   syslog.LOG_NOTICE,
        "panic":    syslog.LOG_EMERG,      #  DEPRECATED
        "warn":     syslog.LOG_WARNING,    #  DEPRECATED
        "warning":  syslog.LOG_WARNING,
    }

    @classmethod
    def _priority(self, levelname):
        return self._PRIORITIES.get(levelname, syslog.LOG_WARNING)

    def __init__(self, facility, process_name):
        super(SysLogHandler, self).__init__()
        if facility not in SysLogHandler._FACILITIES:
            raise ValueError("invalid syslog facility: %s" % (facility,))
        syslog.openlog(process_name, syslog.LOG_PID,
                       SysLogHandler._FACILITIES[facility])

    def close(self):
        syslog.closelog()
        super(SysLogHandler, self).close()

    def emit(self, record):
        priority = SysLogHandler._priority(record.levelname)
        msg = self.format(record)
        if type(msg) is unicode:
            msg = msg.encode('utf-8')
        syslog.syslog(priority, msg)

#-----------------------------------------------------------------------------
# vim:ft=python
