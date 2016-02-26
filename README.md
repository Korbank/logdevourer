logdevourer
===========

logdevourer is a log parsing daemon. It reads logs from several sources
(mainly files from `/var/log`, but UDP and unix socket sources are also
implemented), parses them converting logs to JSON structures, and sends them
to message forwarder, like [Fluentd](http://fluentd.org/) or
[messenger](http://seismometer.net/toolbox/).

logdevourer requires
[Python liblognorm bindings](https://github.com/korbank/python-liblognorm) to
work.


Contact and License
-------------------

logdevourer is written by Stanislaw klekot <dozzie at jarowit.net> for
Korbank S.A <http://korbank.com/>.
The primary distribution point is <https://github.com/korbank/logdevourer>.

logdevourer is distributed under GNU GPL v3 license. See LICENSE file for
details.
