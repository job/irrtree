IRRTree
=======

Simple tool to quickly assess potential resource consumption of an AS-SET.

```
job$ irrtree
IRRtool v1.1.0
usage: irrtree [-h host] [-p port] [-l sources] [-d] [-4 | -6] [-s ASXX] <AS-SET>
   -d,--debug          print debug information
   -4,--ipv4           resolve IPv4 prefixes (default)
   -6,--ipv6           resolve IPv6 prefixes
   -l,--list=SOURCES   list of sources (e.g.: RIPE,NTTCOM,RADB)
   -p,--port=PORT      port on which IRRd runs (default: 43)
   -h,--host=HOST      hostname to connect to (default: rr.ntt.net)
   -s,--search=AUTNUM  output only related to autnum (in ASXXX format)

Written by Job Snijders <job@instituut.net>
Source: https://github.com/job/irrtree
```

**Note:** especially when dealing with large AS-SETs, the latency towards the
IRRd host has significant impact on this program's execution time. Lower
latency is better.

Installation:
=============

**irrtree requires python 3**

Through pypi (try `pip install --upgrade pip` if you get errors):

```
$ pip install irrtree
```

From source:

```
git clone https://github.com/job/irrtree.git
cd irrtree
pip install 'pip>1.5' --upgrade
python setup.py install
```

Examples
========

Display structure of `AS-COLOCLUE`, counting IPv6 prefixes:

```
$ irrtree -6 AS-COLOCLUE
IRRTree (1.0.0) report for 'AS-COLOCLUE' (IPv6), using rr.ntt.net at 2015-07-08 00:25
AS-COLOCLUE (3 ASNs, 33 pfxs)
 +-- AS-SNIJDERS (2 ASNs, 32 pfxs)
 |   +-- AS-ESGOB-ANYCAST (1 ASNs, 29 pfxs)
 |   |   +-- AS60564 (29 pfxs)
 |   +-- AS15562 (3 pfxs)
 +-- AS8283 (1 pfxs)
```

Only display leaves in the `AS2914:AS-EUROPE` structure that relate to `AS15562`:

```
$ irrtree -s AS15562 AS2914:AS-EUROPE
IRRTree (1.0.0) report for 'AS2914:AS-EUROPE' (IPv4), using rr.ntt.net at 2015-07-07 23:02
AS2914:AS-EUROPE (30098 ASNs)
 +-- AS-HIBERNIA (10732 ASNs)
 |   +-- AS-ATRATO (10732 ASNs)
 |   |   +-- AS-HIBERNIA (10732 ASNs) - already expanded
 |   +-- AS-INTOUCHPEERS (15 ASNs)
 |   |   +-- AS-INTOUCH-CS (15 ASNs)
 |   |   |   +-- AS-INTOUCHPEERS (15 ASNs) - already expanded
 |   |   +-- AS-SNIJDERS (2 ASNs)
 |   |       +-- AS15562 (8 pfxs)
 |   +-- AS-COLOCLUE (3 ASNs)
 |   |   +-- AS-SNIJDERS (2 ASNs) - already expanded
 |   +-- AS-CONCEPTS (3 ASNs)
 |       +-- AS15562 (8 pfxs)
 +-- AS-KQ (9281 ASNs)
 |   +-- AS-KPN (9281 ASNs)
 |       +-- AS-KPNEU (8768 ASNs)
 |           +-- AS-JOINTTRANSIT (440 ASNs)
 |           |   +-- AS-CARRIERONE (440 ASNs)
 |           |       +-- AS-JOINTTRANSIT (440 ASNs) - already expanded
 |           |       +-- AS-CONCEPTS (3 ASNs) - already expanded
 |           +-- AS-SOLCON (8 ASNs)
 |           |   +-- AS-STEFFANN-IPv4 (2 ASNs)
 |           |       +-- AS15562 (8 pfxs)
 |           +-- AS-SOLCON6 (3 ASNs)
 |               +-- AS-STEFFANN-IPv6 (2 ASNs)
 |               |   +-- AS15562 (8 pfxs)
 |               +-- AS15562 (8 pfxs)
 +-- AS-JOINTTRANSIT (440 ASNs) - already expanded
 +-- AS-EASYNET (365 ASNs)
 |   +-- AS-EASYNETNL (28 ASNs)
 |       +-- AS-CONCEPTS (3 ASNs) - already expanded
 +-- AS-ATOM86 (183 ASNs)
 |   +-- AS-ATOM86CUST4 (182 ASNs)
 |   |   +-- AS-CONCEPTS (3 ASNs) - already expanded
 |   |   +-- AS-COLOCLUE (3 ASNs) - already expanded
 |   +-- AS-ATOM86CUST6 (153 ASNs)
 |       +-- AS-CONCEPTS (3 ASNs) - already expanded
 |       +-- AS-COLOCLUE (3 ASNs) - already expanded
 +-- AS-SERVERCENTRAL (116 ASNs)
 |   +-- AS-SERVERCENTRAL-CUSTOMERS (115 ASNs)
 |       +-- AS-YOUR-GLOBAL-SET (6 ASNs)
 |           +-- AS-YOUR-CUSTOMERS (4 ASNs)
 |               +-- AS15562 (8 pfxs)
 +-- AS-SNIJDERS (2 ASNs) - already expanded
```
