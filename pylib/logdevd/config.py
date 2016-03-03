#!/usr/bin/python

import yaml
import liblognorm

import sys

import sources
import destinations

#-----------------------------------------------------------------------------

def sources_stdio():
    stdin = sources.FileHandleSource(sys.stdin)
    stdout = destinations.STDOUTDestination()
    return ([stdin], [stdout])

def sources_load(source_defs, dest_defs, state_dir):
    cf_sources = []
    for src in source_defs:
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
    for dest in dest_defs:
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

    return (cf_sources, cf_destinations)

def load(config_file, state_dir, stdio_only = False):
    with open(config_file) as cf:
        configuration = yaml.safe_load(cf)

    if stdio_only:
        (src, dest) = sources_stdio()
    else:
        source_defs = configuration["sources"]
        dest_defs = configuration["destinations"]
        (src, dest) = sources_load(source_defs, dest_defs, state_dir)

    lognorm = liblognorm.Lognorm(configuration["options"]["rulebase"])

    return (src, dest, lognorm, configuration)

#-----------------------------------------------------------------------------
# vim:ft=python
