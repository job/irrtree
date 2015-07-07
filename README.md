IRRTree
=======

Simple tool to quickly assess potential resource consumption of an AS-SET.

```
job$ irrtree
IRRtool v1.0.0
usage: irrtree [-h host] [-p port] [-d] [ -4 | -6 ] [-s ASXX] <AS-SET>
   -d,--debug          print debug information
   -4,--ipv4           resolve IPv4 prefixes (default)
   -6,--ipv6           resolve IPv6 prefixes
   -p,--port=port      port on which IRRd runs (default: 43)
   -h,--host=host      hostname to connect to (default: rr.ntt.net)
   -s,--search=AUTNUM  output only related to autnum (in ASXXX format)

Written by Job Snijders <job@instituut.net>
Source: https://github.com/job/irrtree
(.venv)Vurt:irrtree job$
```

**Note:** especially when dealing with large AS-SETs, the latency towards the
IRRd host has significant impact on this program's execution time. Lower
latency is beter.

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
$ irrtree -s AS15562 AS-COLOCLUE
IRRTree (1.0.0) report for 'AS-COLOCLUE' (IPv4), using rr.ntt.net at 2015-07-08 00:25
AS-COLOCLUE (3 ASNs, 8 pfxs)
 +-- AS-SNIJDERS (2 ASNs, 8 pfxs)
     +-- AS15562 (8 pfxs)
```
