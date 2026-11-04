from unittest.mock import Mock

from irrtree import cli


def test_connect_opens_tcp_socket_and_file_handles(monkeypatch):
    """connect() opens a TCP socket and wraps it in read/write file objects."""
    fake_socket = Mock()
    fake_socket.makefile.side_effect = lambda mode: "handle-%s" % mode
    fake_socket_factory = Mock(return_value=fake_socket)
    monkeypatch.setattr(cli.socket, "socket", fake_socket_factory)

    sock, sock_in, sock_out = cli.connect("irr.example.net", 43)

    fake_socket_factory.assert_called_once_with(cli.socket.AF_INET, cli.socket.SOCK_STREAM)
    fake_socket.connect.assert_called_once_with(("irr.example.net", 43))
    assert sock is fake_socket
    assert sock_in == "handle-r"
    assert sock_out == "handle-w"


def test_send_writes_command_with_line_ending():
    """send() appends the IRRd line terminator and flushes the socket."""
    sock_out = Mock()
    connection = (Mock(), Mock(), sock_out)

    cli.send(connection, "!gAS100")

    sock_out.write.assert_called_once_with("!gAS100\r\n")
    sock_out.flush.assert_called_once()


def test_send_prints_debug_output(monkeypatch, capsys):
    """When debug mode is on, the outgoing command is echoed to stdout."""
    monkeypatch.setattr(cli, "debug", True)
    connection = (Mock(), Mock(), Mock())

    cli.send(connection, "!q")

    assert "sending: !q" in capsys.readouterr().out


def test_receive_strips_trailing_newline():
    """receive() drops the trailing newline from the server's reply line."""
    sock_in = Mock()
    sock_in.readline.return_value = "C\n"
    connection = (Mock(), sock_in, Mock())

    assert cli.receive(connection) == "C"


def test_query_returns_empty_set_for_unknown_object(monkeypatch):
    """A 'D' answer means the object doesn't exist; query() returns no results."""
    connection = (Mock(), Mock(), Mock())
    monkeypatch.setattr(cli, "receive", Mock(return_value="D"))

    assert cli.query(connection, "i", "AS-MISSING") == set()


def test_query_returns_none_on_server_error(monkeypatch, capsys):
    """An 'F' answer signals a server-side error; query() yields no result."""
    monkeypatch.setattr(cli, "debug", True)
    connection = (Mock(), Mock(), Mock())
    monkeypatch.setattr(cli, "receive", Mock(return_value="Fbogus object"))

    result = cli.query(connection, "i", "AS-BAD")

    assert result is None
    assert "Error: bogus object" in capsys.readouterr().out


def test_query_classifies_autnums_and_as_sets(monkeypatch):
    """For the 'i' command, each token is classified as an autnum or as-set."""
    connection = (Mock(), Mock(), Mock())
    # First reply announces the byte count, second carries the member list,
    # third confirms completion.
    monkeypatch.setattr(
        cli, "receive",
        Mock(side_effect=["A42", "as100 AS-FOO ignored-token", "C"]),
    )

    result = cli.query(connection, "i", "AS-TEST", recurse=True)

    assert result == {"AS100", "AS-FOO"}


def test_query_returns_raw_tokens_for_non_member_commands(monkeypatch):
    """Non-'i' commands (e.g. prefix lookups) return their tokens unmodified."""
    connection = (Mock(), Mock(), Mock())
    monkeypatch.setattr(
        cli, "receive",
        Mock(side_effect=["A20", "192.0.2.0/24 198.51.100.0/24", "C"]),
    )

    result = cli.query(connection, "g", "AS100")

    assert result == {"192.0.2.0/24", "198.51.100.0/24"}


def test_query_prints_error_when_completion_marker_missing(monkeypatch, capsys):
    """If the server never confirms completion with 'C', an error is printed."""
    connection = (Mock(), Mock(), Mock())
    monkeypatch.setattr(
        cli, "receive",
        Mock(side_effect=["A20", "192.0.2.0/24", "X"]),
    )

    cli.query(connection, "g", "AS100")

    assert "Error: something went wrong" in capsys.readouterr().out
