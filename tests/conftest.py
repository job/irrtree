import pytest

from irrtree import cli

# Mirrors the class-level defaults declared on irrtree.cli.server.
_DEFAULT_SERVER_STATE = {
    "irr_host": "rr.ntt.net",
    "irr_port": 43,
    "afi": 4,
    "search": False,
    "sources_list": False,
}


def _reset_cli_globals():
    for name, value in _DEFAULT_SERVER_STATE.items():
        setattr(cli.server, name, value)
    cli.debug = False


@pytest.fixture(autouse=True)
def reset_cli_globals():
    """Reset irrtree.cli's mutable globals before and after every test.

    irrtree.cli.server is a plain class used as a configuration namespace,
    and `debug` is a bare module-level global. Both are mutated by main()
    and export(), so without this fixture one test could leak its config
    (e.g. a search filter or debug flag) into the next test.
    """
    _reset_cli_globals()
    yield
    _reset_cli_globals()
