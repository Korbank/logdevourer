#!/usr/bin/python

import yaml
import liblognorm

import sys

import sources
import destinations

#-----------------------------------------------------------------------------

def load(config_file, state_dir):
    with open(config_file) as cf:
        configuration = yaml.safe_load(cf)

    cf_sources = []
    for src in configuration["sources"]:
        if type(src) in [str, unicode]:
            new_source = sources.FileSource(src, state_dir)
        elif src["proto"] == "udp":
            # XXX: no state directory needed
            new_source = sources.UDPSource(src.get("host"), int(src["port"]))
        elif src["proto"] == "unix":
            # XXX: no state directory needed
            new_source = sources.UNIXSource(src["path"])
        elif src["proto"] == "stdin":
            # XXX: no state directory needed
            new_source = sources.FileHandleSource(sys.stdin)
        else:
            raise ValueError("unrecognized source: %s" % (str(src)))
        cf_sources.append(new_source)

    cf_destinations = []
    for dest in configuration["destinations"]:
        if dest in ["stdout", "STDOUT"] or dest["proto"] == "stdout":
            new_dest = destinations.STDOUTDestination()
        elif dest["proto"] == "tcp":
            new_dest = destinations.TCPDestination(dest["host"], int(dest["port"]))
        elif dest["proto"] == "udp":
            new_dest = destinations.UDPDestination(dest["host"], int(dest["port"]))
        elif dest["proto"] == "unix":
            retry = dest.get("retry", True)
            new_dest = destinations.UNIXDestination(dest["path"], retry)
        else:
            raise ValueError("unrecognized destination: %s" % (str(dest)))
        cf_destinations.append(new_dest)

    lognorm = liblognorm.Lognorm(configuration["options"]["rulebase"])

    return (cf_sources, cf_destinations, lognorm, configuration)

#-----------------------------------------------------------------------------
# vim:ft=python
