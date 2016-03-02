
""" Sookie, is a waiter, waits for a socket to be listening then it moves on

Usage:
    sookie <socket> [--timeout=<to>] [--retry=<rt>] [--logsocket=<ls>] [--logfacility=<lf>] [--loglevel=<ll>]
    sookie -h | --help
    sookie --version

Options:
    -h --help              Show this screen
    --version              Show version
    --timeout=<to>         Timout in seconds [default: 1800]
    --retry=<rt>           Interval between retries in seconds [default: 20]
    --logsocket=<ls>       Socket to send syslog messages to, only logging to local syslog if omitted.
    --logfacility=<lf>     The syslog facility to use for logging [default: user]
    --loglevel=<ll>        The syslog severity level to use, i.e the verbosity level [default: info]
    <socket>               Socket to wait for, 'host:port'


Sookie is intended to be a simple way of providing som measure of management of
inter server dependencies in complex environments. All it does is wait for a
socket to start listening for connections then it exits. It is supposed to be
used as a "smart" sleep in a startup script. 

Sookie logs to syslog, and optionally to a remote syslog server aswell. Level
and facility values can be taken from syslog(1)

Sookie Stackhouse is a waitress.

exitcodes
0: ok, the server answered
1: waited until timout
2: invalid syntax

"""

import docopt
import logging
import logging.handlers
import os
import socket
import sys
import time

def main(args):

    if args['--logsocket']:
        logserver = tuple(args['--logsocket'].split(':'))
    else:
        logserver = None
    logfacility = args['--logfacility']
    loglevel = args['--loglevel']

    logger = logging.getLogger(os.path.basename(__file__))

    localsyslog = logging.handlers.SysLogHandler()
    if logserver:
        remotesyslog = logging.handlers.SysLogHandler(
                address=logserver,
                facility=logging.handlers.SysLogHandler.facility_names[logfacility]
            )
    try:
        localsyslog.setLevel(logging.handlers.SysLogHandler.priority_names[loglevel])
        if logserver:
            remotesyslog.setLevel(logging.handlers.SysLogHandler.priority_names[loglevel])
    except KeyError:
        print "Invalid argument to %s (%s)" % ('--loglevel', args['--loglevel'])
        sys.exit(2)


    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    localsyslog.setFormatter(formatter)
    if logserver:
        remotesyslog.setFormatter(formatter)

    logger.addHandler(localsyslog)
    if logserver:
        logger.addHandler(remotesyslog)

    logger.info('%s Starting' % __file__)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        option = '--timeout'
        timeout = int(args[option])
        option = '--retry'
        interval = int(args[option])
    except ValueError:
        print "Invalid argument to %s (%s)" % (option, args[option])
        sys.exit(2)
    server = tuple(args['<socket>'].split(':'))
    timeout_time = time.time() + timeout
    is_timeout = False

    logger.debug('now: %d, timeout: %d, timeout_time: %d)' % (time.time(), timeout, timeout_time))

    while True:
        t = time.time()
        if t >= timeout_time:
            is_timeout = True
            break
        try:
            sock.connect(server)
            logger.info('Connect')
            print server
            logger.debug('%ds to spare' % int(timeout_time-t))
            break
        except socket.error:
            logger.debug('Waiting %d more seconds' % step)
            time.sleep(step)
        except TypeError, E:
            print E
            print "Invalid socket: %s" % args['<socket>']
            sys.exit(2)

    logger.info('%s Ending' % __file__)
    exitcode = 1 if is_timeout else 0
    logger.debug('exitcode: %d' % exitcode)

    sys.exit(exitcode)


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='0.1')
    main(args)

