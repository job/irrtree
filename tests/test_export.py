"""Tests for the export() programmatic API.

export() behaves like main() but returns the resolved database instead of
printing a tree, and skips prefix resolution for plain autnums.
"""

from unittest.mock import Mock

import pytest

from irrtree import cli


def test_export_rejects_argument_without_as_set_marker(capsys):
    """export() mirrors main()'s validation that the argument looks like an AS-SET."""
    with pytest.raises(SystemExit):
        cli.export("AS100")

    assert "does not appear to be an AS-SET" in capsys.readouterr().out


def test_export_without_arguments_raises(monkeypatch):
    """export() has no fallback for being called with no data (pre-existing behavior).

    This documents the current contract so the upcoming dependency/Python
    upgrade can be verified not to silently change it.
    """
    with pytest.raises(UnboundLocalError):
        cli.export()


def test_export_exits_when_sources_list_is_rejected(monkeypatch, capsys):
    """export() aborts if the IRRd server rejects the requested source list."""
    cli.server.sources_list = "BOGUS"
    monkeypatch.setattr(cli, "connect", Mock(return_value=(Mock(), Mock(), Mock())))
    monkeypatch.setattr(cli, "receive", Mock(return_value="E"))  # IRRd rejects the list

    with pytest.raises(SystemExit) as exc_info:
        cli.export("AS-TEST")

    assert exc_info.value.code == 2
    assert "Error: E" in capsys.readouterr().out


def test_export_returns_resolved_db_for_given_as_set(monkeypatch):
    """export() returns the member/origin-ASN graph instead of printing a tree."""
    monkeypatch.setattr(cli, "connect", Mock(return_value=(Mock(), Mock(), Mock())))
    monkeypatch.setattr(cli, "receive", Mock(return_value="C"))

    def fake_query(connection, cmd, as_set, recurse=False, search=False):
        # export() queries every item (even autnums) the same way via "i".
        return {"AS100"} if as_set == "AS-TEST" else set()

    monkeypatch.setattr(cli, "query", Mock(side_effect=fake_query))

    db = cli.export("AS-TEST")

    assert db == {
        "AS-TEST": {"members": {"AS100"}, "origin_asns": {"AS100"}},
        "AS100": {"members": set(), "origin_asns": set()},
    }


def test_export_prunes_entries_unrelated_to_the_search_target(monkeypatch):
    """export() applies the same search-based pruning logic as main()."""
    cli.server.search = "AS100"
    monkeypatch.setattr(cli, "connect", Mock(return_value=(Mock(), Mock(), Mock())))
    monkeypatch.setattr(cli, "receive", Mock(return_value="C"))

    responses = {
        ("AS-TEST", False): {"AS-BRANCH-A", "AS-BRANCH-B"},
        ("AS-TEST", True): {"AS100", "AS200"},
        ("AS-BRANCH-A", False): {"AS100"},
        ("AS-BRANCH-A", True): {"AS100"},
        ("AS-BRANCH-B", False): {"AS200"},
        ("AS-BRANCH-B", True): {"AS200"},
        ("AS100", False): set(),
        ("AS100", True): set(),
        ("AS200", False): set(),
        ("AS200", True): set(),
    }

    def fake_query(connection, cmd, as_set, recurse=False, search=False):
        return responses[(as_set, recurse)]

    monkeypatch.setattr(cli, "query", Mock(side_effect=fake_query))

    db = cli.export("AS-TEST")

    # AS-BRANCH-B's origin (AS200) doesn't match the search target, so it's pruned.
    assert "AS-BRANCH-B" not in db
    assert db["AS-TEST"]["members"] == {"AS-BRANCH-A"}
    assert db["AS-BRANCH-A"]["members"] == {"AS100"}
