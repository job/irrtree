# IRRTree

A simple tool to quickly assess potential resource consumption of an AS-SET.

```shell
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

## Installation

Through pypi (try `pip install --upgrade pip` if you get errors):

```shell
pip install irrtree
```

From source:

```shell
git clone https://github.com/job/irrtree.git
cd irrtree
pip install --upgrade pip
pip install .
```

## Examples

Display structure of `AS-COLOCLUE`, counting IPv6 prefixes:

```shell
$ irrtree -6 AS-COLOCLUE
Processed: 205 objects (Elapsed Time: 0:00:33)
IRRTree (1.4.0) report for 'AS-COLOCLUE' (IPv6), using rr.ntt.net at 2026-11-04 08:39
AS-COLOCLUE (135 ASNs, 1690 pfxs)
 +-- AS8283:AS-COLOCLUE (135 ASNs, 1690 pfxs)
     +-- AS215296:AS-RAOULBROUNS (23 ASNs, 147 pfxs)
     |   +-- AS213409:AS-LYNQIA (4 ASNs, 29 pfxs)
     |   |   +-- AS206586:AS-CUSTOMERS (2 ASNs, 12 pfxs)
     |   |   |   +-- AS206586 (11 pfxs)
     |   |   |   +-- AS154003 (1 pfxs)
     |   |   +-- AS213409 (15 pfxs)
     |   |   +-- AS206586 (11 pfxs)
     |   |   +-- AS112 (2 pfxs)
     |   +-- AS210880:AS-ARDADAGLIOGLU (3 ASNs, 5 pfxs)
     |   |   +-- AS210880 (2 pfxs)
     |   |   +-- AS112 (2 pfxs)
     |   |   +-- AS219479 (1 pfxs)
...
```

## Testing

Unit tests use `pytest` and mock out all network calls, so no IRRd server is
required. Run them in a virtual environment:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest
pip install -e .
pytest -v
```
