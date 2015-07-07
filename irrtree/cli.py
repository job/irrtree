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
import socket
import sys
from collections import OrderedDict as OD
from Queue import Queue

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
    print "usage: irrtree [-h host] [-p port] [-d] [ -4 | -6 ] <AS-SET>"
    print "   -d,--debug       print debug information"
    print "   -4,--ipv4        resolve IPv4 prefixes (default)"
    print "   -6,--ipv6        resolve IPv6 prefixes"
    print "   -p,--port=port   port on which IRRd runs (default: 43)"
    print "   -h,--host=host   hostname to connect to (default: rr.ntt.net)"
    print ""
    print "Written by Job Snijders <job@instituut.net>"
    print "Source: https://github.com/job/irrtree"
    sys.exit()


def resolve_prefixes(db, item):
    all_prefixes = []
    if "-" not in item:
        return len(db[item])
    for origin in db[item]['origin_asns']:
        all_prefixes.extend(db[origin])
    return len(set(all_prefixes))


def process(irr_host, afi, db, as_set):
    import datetime
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M")
    print "IRRTree (%s) report for '%s' (IPv%i), using %s at %s" \
        % (irrtree.__version__, as_set, afi, irr_host, now)
    print "start: %s (%s ASNs, %s pfxs)" % (as_set,
                                            len(db[as_set]['origin_asns']),
                                            resolve_prefixes(db, as_set))
    def print_member(as_set, db):
        if not "-" in as_set:
            res = "%s (%s pfxs)" % (as_set, resolve_prefixes(db, as_set))
        else:
            res = "%s (%s ASNs, %s pfxs)" % (as_set,
                                             len(db[as_set]['origin_asns']),
                                             resolve_prefixes(db, as_set))
        return res

    def resolve_tree(as_set, db, tree=OD(), seen=[]):
        for member in sorted(db[as_set]['members'], key=lambda x:
                             len(db[as_set]['origin_asns'])):
            if member in seen:
                tree["%s - already expanded" % print_member(member, db)] = {}
                continue
            if "-" in member:
                seen.append(member)
                tree["%s" % print_member(member, db)] = resolve_tree(member, db, OD(), seen)
            else:
                tree["%s" % print_member(member, db)] = {}
        return tree

    tree = OD()
    tree["%s" % print_member(as_set, db)]= resolve_tree(as_set, db)
    tr = asciitree.LeftAligned()
    print tr(tree)


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

    if not len(args) == 1:
        usage()
    if not "-" in args[0]:
        print "Error: %s does not appear to be an AS-SET" % args[0]
        usage()

    queue = Queue()
    queue.put(args[0])

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
            db[item] = prefixes
            counter += 1
            if not debug:
                pbar.update(counter)
            queue.task_done()
            continue
        db.setdefault(item, {})['members'] = query(connection, "i", item)
        db[item]['origin_asns'] = query(connection, "i", item, True)
        for candidate in set(db[item]['members'] + db[item]['origin_asns']):
            if not candidate in db and candidate not in queue.queue:
                queue.put(candidate)
        counter += 1
        if not debug:
            pbar.update(counter)
        queue.task_done()

    connection[0].close()

    process(irr_host, afi, db, args[0])


if __name__ == "__main__":
    main()
