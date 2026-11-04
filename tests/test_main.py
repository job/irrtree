import sys
from unittest.mock import Mock

import pytest

from irrtree import cli


def _patch_networking(monkeypatch, query_responses):
    """Patch connect/receive/query/progressbar so main() runs with no I/O.

    query_responses maps (command, as_set, recurse) -> the set query() should
    return for that call.
    """
    monkeypatch.setattr(cli, "connect", Mock(return_value=(Mock(), Mock(), Mock())))
    monkeypatch.setattr(cli, "receive", Mock(return_value="C"))
    monkeypatch.setattr(cli.progressbar, "ProgressBar", Mock(return_value=Mock()))

    def fake_query(connection, cmd, as_set, recurse=False, search=False):
        return query_responses[(cmd, as_set, recurse)]

    monkeypatch.setattr(cli, "query", Mock(side_effect=fake_query))


def test_main_shows_usage_when_no_as_set_given(monkeypatch, capsys):
    """Without an AS-SET argument, main() prints usage and exits."""
    monkeypatch.setattr(sys, "argv", ["irrtree"])

    with pytest.raises(SystemExit):
        cli.main()

    assert "usage: irrtree" in capsys.readouterr().out


def test_main_shows_usage_for_unknown_option(monkeypatch, capsys):
    """An unrecognized flag is reported via getopt and usage() is shown."""
    monkeypatch.setattr(sys, "argv", ["irrtree", "--bogus-flag", "AS-TEST"])

    with pytest.raises(SystemExit):
        cli.main()

    assert "usage: irrtree" in capsys.readouterr().out


def test_main_rejects_argument_without_as_set_marker(monkeypatch, capsys):
    """An argument lacking a '-' is rejected as not being an AS-SET."""
    monkeypatch.setattr(sys, "argv", ["irrtree", "AS100"])

    with pytest.raises(SystemExit):
        cli.main()

    assert "does not appear to be an AS-SET" in capsys.readouterr().out


def test_main_exits_when_sources_list_is_rejected(monkeypatch, capsys):
    """main() aborts if the IRRd server rejects the requested -l source list."""
    monkeypatch.setattr(sys, "argv", ["irrtree", "-l", "BOGUS", "AS-TEST"])
    monkeypatch.setattr(cli, "connect", Mock(return_value=(Mock(), Mock(), Mock())))
    monkeypatch.setattr(cli, "receive", Mock(return_value="E"))  # IRRd rejects the list

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    assert "Error: E" in capsys.readouterr().out


def test_main_applies_host_port_and_debug_flags(monkeypatch):
    """The -h, -p and -d flags configure the server target and debug output."""
    monkeypatch.setattr(
        sys, "argv",
        ["irrtree", "-d", "-h", "irr.example.net", "-p", "4343", "AS-TEST"],
    )
    _patch_networking(monkeypatch, {
        ("i", "AS-TEST", False): {"AS100"},
        ("i", "AS-TEST", True): {"AS100"},
        ("g", "AS100", False): {"192.0.2.0/24"},
    })
    monkeypatch.setattr(cli, "process", Mock())

    cli.main()

    cli.connect.assert_called_once_with("irr.example.net", 4343)
    assert cli.debug is True


def test_main_builds_db_and_passes_it_to_process(monkeypatch):
    """main() walks a small AS-SET tree and hands the resulting db to process()."""
    monkeypatch.setattr(sys, "argv", ["irrtree", "AS-TEST"])
    _patch_networking(monkeypatch, {
        ("i", "AS-TEST", False): {"AS100"},   # members
        ("i", "AS-TEST", True): {"AS100"},    # origin_asns
        ("g", "AS100", False): {"192.0.2.0/24"},  # IPv4 prefixes (default afi)
    })
    recorded_process_call = Mock()
    monkeypatch.setattr(cli, "process", recorded_process_call)

    cli.main()

    recorded_process_call.assert_called_once()
    irr_host, afi, db, query_object, search = recorded_process_call.call_args[0]
    assert query_object == "AS-TEST"
    assert afi == 4
    assert search is False
    assert db == {
        "AS-TEST": {"members": {"AS100"}, "origin_asns": {"AS100"}},
        "AS100": {"192.0.2.0/24"},
    }


def test_main_ipv6_and_search_prune_unrelated_branches(monkeypatch):
    """The -6 and -s flags switch to IPv6 lookups and prune unrelated as-sets."""
    monkeypatch.setattr(sys, "argv", ["irrtree", "-6", "-s", "as100", "AS-TEST"])
    _patch_networking(monkeypatch, {
        ("i", "AS-TEST", False): {"AS-BRANCH-A", "AS-BRANCH-B"},
        ("i", "AS-TEST", True): {"AS100", "AS200"},
        ("i", "AS-BRANCH-A", False): {"AS100"},
        ("i", "AS-BRANCH-A", True): {"AS100"},
        ("i", "AS-BRANCH-B", False): {"AS200"},
        ("i", "AS-BRANCH-B", True): {"AS200"},
        ("6", "AS100", False): {"2001:db8::/32"},  # only the matching ASN is resolved
    })
    recorded_process_call = Mock()
    monkeypatch.setattr(cli, "process", recorded_process_call)

    cli.main()

    irr_host, afi, db, query_object, search = recorded_process_call.call_args[0]
    assert afi == 6
    assert search == "AS100"
    # AS-BRANCH-B's origin (AS200) doesn't match the search target, so it's pruned.
    assert "AS-BRANCH-B" not in db
    assert db["AS-TEST"]["members"] == {"AS-BRANCH-A"}
    assert db["AS100"] == {"2001:db8::/32"}
