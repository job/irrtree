import pytest

import irrtree
from irrtree import cli


def test_usage_prints_help_text_and_exits(capsys):
    """usage() prints the CLI help text and then terminates the program."""
    with pytest.raises(SystemExit):
        cli.usage()

    out = capsys.readouterr().out
    assert "usage: irrtree" in out
    assert irrtree.__version__ in out


def test_resolve_prefixes_counts_an_autnums_own_prefixes():
    """For a plain autnum, resolve_prefixes() counts its known prefixes."""
    db = {"AS100": {"192.0.2.0/24", "192.0.2.128/25"}}

    assert cli.resolve_prefixes(db, "AS100") == 2


def test_resolve_prefixes_unions_prefixes_of_an_as_sets_origins():
    """For an as-set, resolve_prefixes() unions the prefixes of its origin ASNs."""
    db = {
        "AS-SET": {"origin_asns": {"AS100", "AS200"}},
        "AS100": {"192.0.2.0/24"},
        "AS200": {"192.0.2.0/24", "198.51.100.0/24"},
    }

    # 192.0.2.0/24 is announced by both ASNs but only counted once.
    assert cli.resolve_prefixes(db, "AS-SET") == 2


def test_process_prints_full_tree_with_asn_and_prefix_counts(capsys):
    """process() renders a full tree annotated with ASN and prefix counts."""
    db = {
        "AS-SET1": {"members": {"AS-SET2", "AS100"}, "origin_asns": {"AS100", "AS200"}},
        "AS-SET2": {"members": {"AS200"}, "origin_asns": {"AS200"}},
        "AS100": {"192.0.2.0/24"},
        "AS200": {"192.0.2.128/25", "198.51.100.0/24"},
    }

    cli.process("irr.example.net", 4, db, "AS-SET1", search=False)

    out = capsys.readouterr().out
    assert "AS-SET1 (2 ASNs, 3 pfxs)" in out
    assert "AS-SET2 (1 ASNs, 2 pfxs)" in out
    assert "AS200 (2 pfxs)" in out
    assert "AS100 (1 pfxs)" in out


def test_process_search_mode_omits_prefix_counts_and_unrelated_leaves(capsys):
    """When searching for one autnum, unrelated branches are skipped entirely."""
    db = {
        "AS-SET1": {"members": {"AS-SET2", "AS100"}, "origin_asns": {"AS100", "AS200"}},
        "AS-SET2": {"members": {"AS200"}, "origin_asns": {"AS200"}},
        "AS100": {"192.0.2.0/24"},
        "AS200": {"192.0.2.128/25", "198.51.100.0/24"},
    }

    cli.process("irr.example.net", 4, db, "AS-SET1", search="AS200")

    out = capsys.readouterr().out
    assert "AS-SET1 (2 ASNs)" in out  # pfxs omitted while searching
    assert "AS200 (2 pfxs)" in out
    assert "AS100" not in out  # unrelated leaf is skipped, not just hidden


def test_process_marks_self_referencing_as_sets_as_already_expanded(capsys):
    """A cycle (an as-set that lists itself) is flagged instead of recursing forever."""
    db = {"AS-LOOP": {"members": {"AS-LOOP"}, "origin_asns": set()}}

    cli.process("irr.example.net", 4, db, "AS-LOOP", search=False)

    assert "already expanded" in capsys.readouterr().out


def test_process_exits_when_search_target_is_not_found(capsys):
    """If the search target has no relation to a plain autnum, process() exits early."""
    db = {"AS100": {"192.0.2.0/24"}}

    with pytest.raises(SystemExit):
        cli.process("irr.example.net", 4, db, "AS100", search="AS999")

    assert "NOT_FOUND" in capsys.readouterr().out
