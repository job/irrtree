#!/usr/bin/env python

debug = False

import progressbar
from Queue import Queue
import socket
import sys

irr_host = 'rr.ntt.net'
irr_port = 43

as_set = sys.argv[1]

try:
    import asciitree
except ImportError:
    print "ERROR: install asciitree: pip install asciitree"
    sys.exit(1)

def connect():
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

queue = Queue()
queue.put(as_set)

connection = connect()
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
        prefixes = query(connection, "g", item)
        db[item] = prefixes
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

print db
