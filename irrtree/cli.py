#!/usr/bin/env python
# Copyright (C) 2015 Job Snijders <job@instituut.net>
#
# This file is part of IRRTree
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import irrtree
import getopt
import progressbar
from Queue import Queue
import socket
import sys

try:
    import asciitree
except ImportError:
    print "ERROR: install asciitree: pip install asciitree"
    sys.exit(1)

def connect(irr_host, irr_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((irr_host, irr_port))
    sock_in = sock.makefile('r')
    sock_out = sock.makefile('w')
    return sock, sock_in, sock_out

def send(connection, command):
    sock, sock_in, sock_out = connection
    sock_out.write(command + '\r\n')
    sock_out.flush()

def receive(connection):
    sock, sock_in, sock_out = connection
    return sock_in.readline()[:-1]

def query(connection, cmd, as_set, recurse=False):
    cmd = "!%s%s%s" % (cmd, as_set, ",1" if recurse else "")
    send(connection, cmd)
    answer = receive(connection)
    if answer == "D":
        return list()
    elif answer[0] == "F":
        if debug:
            print "Error: %s" % answer[1:]
            print "Query was: %s" % cmd
    elif answer[0] == "A":
        if debug:
            print "Info: receiving %s bytes" % answer[1:]
        results = receive(connection).split()
        if not receive(connection) == "C":
            print "Error: something went wrong with: %s" % cmd
        return results


def usage():
    print "IRRtool v%s" % irrtree.__version__
    print "usage: irrtree [-h host] [-p port] [-d] [ -4 | -6 ] <AS-SET> [ AS-SET ... ]"
    print "   -d,--debug       print debug information"
    print "   -4,--ipv4        resolve IPv4 prefixes (default)"
    print "   -6,--ipv6        resolve IPv6 prefixes"
    print "   -p,--port=port   port on which IRRd runs (default: 43)"
    print "   -h,--host=host   hostname to connect to (default: rr.ntt.net)"
    sys.exit()

def main():

    global debug
    debug = False

    irr_host = 'rr.ntt.net'
    irr_port = 43
    afi = 4

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:dp:64", ["host=", "debug",
                                                             "port=", "ipv6",
                                                             "ipv4"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o == "-d":
            debug = True
        elif o in ("-h", "--host"):
            irr_host = a
        elif o in ("-6", "--ipv6"):
            afi = 6
        elif o in ("-p", "--port"):
            irr_port = int(a)

    if not args:
        usage()

    queue = Queue()
    for arg in args:
        queue.put(arg)

    connection = connect(irr_host, irr_port)
    send(connection, "!!")

    db = {}

    widgets = ['Processed: ', progressbar.Counter(), ' objects (',
            progressbar.Timer(), ')']
    pbar = progressbar.ProgressBar(widgets=widgets)
    pbar.start()
    counter = 0

    while not queue.empty():
        item = queue.get()
        if debug:
            print "Info: expanding %s" % item
        if not "-" in item:  # expand aut-nums
            prefixes = query(connection, "g" if afi == 4 else "6", item)
            db[item] = len(prefixes)
            counter += 1
            pbar.update(counter)
            queue.task_done()
            continue
        db.setdefault(item, {})['members'] = query(connection, "i", item)
        db[item]['origin_asns'] = query(connection, "i", item, True)
        for candidate in set(db[item]['members'] + db[item]['origin_asns']):
            if not candidate in db and candidate not in queue.queue:
                queue.put(candidate)
        counter += 1
        pbar.update(counter)
        queue.task_done()

    connection[0].close()

    print db

if __name__ == "__main__":
    main()
