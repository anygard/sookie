#!/usr/bin/env python

""" Sookie, is a waiter, waits for a socket to be listening then it moves on

Usage:
    sookie <socket> [--timeout=<to>] [--retry=<rt>] [--logsocket=<ls>] [--loglevel=<ll>] [--verbose]
    sookie -h | --help
    sookie --version

Options:
    -h --help              Show this screen
    --version              Show version
    --timeout=<to>         Timout in seconds [default: 1800]
    --retry=<rt>           Interval between retries in seconds [default: 20]
    --logsocket=<ls>       Socket to send syslog messages to, only logging to local syslog if omitted.
    --loglevel=<ll>        The syslog severity level to use, i.e the verbosity level [default: info]
    --verbose              Also log to stdout
    <socket>               Socket to wait for, 'host:port'


Sookie is intended to be a simple way of providing som measure of management of
inter server dependencies in complex environments. All it does is wait for a
socket to start listening for connections then it exits. It is supposed to be
used as a "smart" sleep in a startup script. 

Sookie accepts the following logleves debug,info,warning,error,critical.

Sookie Stackhouse is a waitress.

exitcodes
0: ok, the server answered
1: waited until timout
2: invalid syntax

"""

import docopt
import logging
import logging.handlers
import platform
import os
import socket
import sys
import time

platform_socket = {
        'Linux': '/dev/log',
        'Darwin': '/var/run/syslog',
        }

levels = {
        'notset': logging.NOTSET,
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
        }

def main(args):

    if args['--logsocket']:
        (host, port) = tuple(args['--logsocket'].split(':'))
        logserver = (host, int(port))
    else:
        logserver = None

    if args['--verbose']:
        verbose=True
    else:
        verbose=False

    pf = platform.system()
    if pf in platform_socket.keys():
        localaddr=platform_socket[pf]
    else:
        localaddr=('localhost',514)

    logger = logging.getLogger(os.path.basename(__file__))
    try:
        loglevel = levels[args['--loglevel'].lower()]

        localsyslog = logging.handlers.SysLogHandler(address=localaddr)
        if verbose:
            stdout = logging.StreamHandler(sys.stdout)
        if logserver:
            remotesyslog = logging.handlers.SysLogHandler(address=logserver,socktype=socket.SOCK_STREAM)

        logger.setLevel(loglevel)
        localsyslog.setLevel(loglevel)
        if verbose:
            stdout.setLevel(loglevel)
        if logserver:
            remotesyslog.setLevel(loglevel)
    except KeyError:
        logger.error("Invalid argument to %s (%s)" % ('--loglevel', args['--loglevel']))
        sys.exit(2)


    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    localsyslog.setFormatter(formatter)
    if logserver:
        remotesyslog.setFormatter(formatter)

    logger.addHandler(localsyslog)
    if verbose:
        logger.addHandler(stdout)
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
        logger.error("Invalid argument to %s (%s)" % (option, args[option]))
        sys.exit(2)
    (host, port) = tuple(args['<socket>'].split(':'))
    server = (host, int(port))
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
            logger.debug('%ds to spare' % int(timeout_time-t))
            break
        except socket.error:
            logger.debug('Waiting %d more seconds' % interval)
            time.sleep(interval)
        except TypeError, E:
            logger.error(E)
            logger.error("Invalid socket: %s" % args['<socket>'])
            sys.exit(2)

    logger.info('%s Ending' % __file__)
    exitcode = 1 if is_timeout else 0
    logger.debug('exitcode: %d' % exitcode)

    sys.exit(exitcode)


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='0.1')
    main(args)

