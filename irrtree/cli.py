#!/usr/bin/env python3
# Copyright (C) 2015-2018 Job Snijders <job@instituut.net>
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

from collections import OrderedDict as OD
from queue import Queue

import asciitree
import getopt
import irrtree
import progressbar
import re
import socket
import sys


def connect(irr_host, irr_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((irr_host, irr_port))
    sock_in = sock.makefile('r')
    sock_out = sock.makefile('w')
    return sock, sock_in, sock_out


def send(connection, command):
    sock, sock_in, sock_out = connection
    if debug:
        print("sending: %s" % command)
    sock_out.write(command + '\r\n')
    sock_out.flush()


def receive(connection):
    sock, sock_in, sock_out = connection
    return sock_in.readline()[:-1]


def query(connection, cmd, as_set, recurse=False, search=False):
    query = "!%s%s%s" % (cmd, as_set, ",1" if recurse else "")
    send(connection, query)
    answer = receive(connection)
    if answer == "D":
        return set()
    elif answer[0] == "F":
        if debug:
            print("Error: %s" % answer[1:])
            print("Query was: %s" % query)
    elif answer[0] == "A":
        if debug:
            print("Info: receiving %s bytes" % answer[1:])
        unfiltered = receive(connection).split()
        results = set()
        if cmd == "i":
            for result in unfiltered:
                if re.match(r'^[aA][sS]\d+', result):
                    results.add(result.upper())  # found an autnum
                elif re.match(r'^[aA][sS]-.*', result):
                    results.add(result.upper())  # found as-set
                else:
                    if debug:
                        print("Warning: not honoring mbrs-by-ref for object %s with '%s'" % (as_set, result))
        else:
            results = unfiltered

        if not receive(connection) == "C":
            print("Error: something went wrong with: %s" % query)

        return set(results)

def usage():
    print("IRRtool v%s" % irrtree.__version__)
    print("usage: irrtree [-h host] [-p port] [-l sources] [-d] [-4 | -6] [-s ASXX] <AS-SET>")
    print("   -d,--debug          print debug information")
    print("   -4,--ipv4           resolve IPv4 prefixes (default)")
    print("   -6,--ipv6           resolve IPv6 prefixes")
    print("   -l,--list=SOURCES   list of sources (e.g.: RIPE,NTTCOM,RADB)")
    print("   -p,--port=PORT      port on which IRRd runs (default: 43)")
    print("   -h,--host=HOST      hostname to connect to (default: rr.ntt.net)")
    print("   -s,--search=AUTNUM  output only related to autnum (in ASXXX format)")
    print("")
    print("Written by Job Snijders <job@instituut.net>")
    print("Source: https://github.com/job/irrtree")
    sys.exit()


def resolve_prefixes(db, item):
    all_prefixes = set()
    if "-" not in item:
        return len(db[item])
    for origin in db[item]['origin_asns']:
        all_prefixes |= db[origin]
    return len(all_prefixes)


def process(irr_host, afi, db, as_set, search):
    import datetime
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M")
    print("IRRTree (%s) report for '%s' (IPv%i), using %s at %s" \
        % (irrtree.__version__, as_set, afi, irr_host, now))

    if search and "-" not in list(db.keys()):
        if not search in list(db.keys()):
            print("NOT_FOUND: %s not present in %s or any of its members" % (search, as_set))
            sys.exit()

    def print_member(as_set, db, search):
        if not "-" in as_set:
            res = "%s (%s pfxs)" % (as_set, resolve_prefixes(db, as_set))
        elif search:
            res = "%s (%s ASNs)" % (as_set, len(db[as_set]['origin_asns']))
        else:
            res = "%s (%s ASNs, %s pfxs)" % (as_set,
                                             len(db[as_set]['origin_asns']),
                                             resolve_prefixes(db, as_set))
        return res

    def getasncount(db, item):
        v = db[item]
        if type(v) == set:
            ret = (0, len(v))
        else:
            ret = (len(v['origin_asns']), resolve_prefixes(db, item))
        return ret

    def resolve_tree(as_set, db, tree=OD(), seen=set()):
        seen.add(as_set)
        for member in sorted(db[as_set]['members'], key=lambda x:
                             getasncount(db, x), reverse=True):
            if member in seen:
                tree["%s - already expanded" % print_member(member, db, search)] = {}
                continue
            if "-" in member:
                seen.add(member)
                tree["%s" % print_member(member, db, search)] = resolve_tree(member, db, OD(), seen)
            else:
                if not search or search == member:
                    tree["%s" % print_member(member, db, search)] = {}
                else:
                    continue
        return tree

    tree = OD()
    tree["%s" % print_member(as_set, db, search)] = resolve_tree(as_set, db)
    tr = asciitree.LeftAligned()
    print(tr(tree))


def main():

    global debug
    debug = False

    irr_host = 'rr.ntt.net'
    irr_port = 43
    afi = 4
    search = False
    sources_list = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:dp:64s:l:",
                                   ["host=", "debug", "port=", "ipv6", "ipv4",
                                    "search=", "list="])
    except getopt.GetoptError as err:
        print(str(err))
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
        elif o in ("-s", "--search"):
            search = a.upper()
        elif o in ("-l", "--list"):
            sources_list = a

    if not len(args) == 1:
        usage()
    if not "-" in args[0]:
        print("Error: %s does not appear to be an AS-SET" % args[0])
        usage()
    query_object = args[0].upper()

    queue = Queue()
    queue.put(query_object)

    connection = connect(irr_host, irr_port)
    send(connection, "!!")
    if sources_list:
        send(connection, "!s%s" % sources_list)
        answer = receive(connection)
        if answer is not "C":
            print("Error: %s" % answer)
            sys.exit(2)

    db = {}

    widgets = ['Processed: ', progressbar.Counter(), ' objects (',
            progressbar.Timer(), ')']
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=2**32)
    if not debug:
        pbar.start()
    counter = 0

    while not queue.empty():
        item = queue.get()
        if debug:
            print("Info: expanding %s" % item)
        if not "-" in item:  # expand aut-nums
            if not search or search == item:
                prefixes = query(connection, "g" if afi == 4 else "6", item, False, False)
            else:
                prefixes = set()
            db[item] = prefixes
            counter += 1
            if not debug:
                pbar.update(counter)
            queue.task_done()
            continue
        db.setdefault(item, {})['members'] = query(connection, "i", item,
                                                   False, False)
        db[item]['origin_asns'] = query(connection, "i", item, True, False)
        for candidate in db[item]['members'] | db[item]['origin_asns']:
            if not candidate in db and candidate not in queue.queue:
                queue.put(candidate)
        counter += 1
        if not debug:
            pbar.update(counter)
        queue.task_done()

    send(connection, '!q')
    connection[0].close()

    if search:
        to_delete = set()
        iter_db = dict(db)
        for item in iter_db:
            if "-" in item:
                if not search in db[item]['origin_asns']:
                    del db[item]
                    to_delete.add(item)
        for item in db:
            if "-" in item:
                db[item]['members'] = db[item]['members'] - to_delete

    process(irr_host, afi, db, query_object, search)


if __name__ == "__main__":
    main()
