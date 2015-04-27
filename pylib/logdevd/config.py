#!/usr/bin/python

import yaml
import liblognorm

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
        else:
            raise ValueError("unrecognized source: %s" % (str(src)))
        cf_sources.append(new_source)

    cf_destinations = []
    for dest in configuration["destinations"]:
        if dest["proto"] == "tcp":
            new_dest = destinations.TCPDestination(dest["host"], int(dest["port"]))
        elif dest["proto"] == "udp":
            new_dest = destinations.UDPDestination(dest["host"], int(dest["port"]))
        elif dest["proto"] == "unix":
            new_dest = destinations.UNIXDestination(dest["path"])
        else:
            raise ValueError("unrecognized destination: %s" % (str(dest)))
        cf_destinations.append(new_dest)

    lognorm = liblognorm.Lognorm(configuration["rulebase"])

    return (cf_sources, cf_destinations, lognorm)

#-----------------------------------------------------------------------------
# vim:ft=python
