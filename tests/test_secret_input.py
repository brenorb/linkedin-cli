import io
import json

import pytest

from linkedin_cli.cli import main


@pytest.mark.parametrize("argv", [["post", "get", "urn:li:share:123"], ["profile", "whoami"]])
@pytest.mark.parametrize("source", ["file", "stdin"])
def test_token_sources_work_without_prompt_or_secret_in_argv(argv, source, tmp_path, monkeypatch, capsys):
    token = "test-private-token"
    seen = []

    class Client:
        def get_post(self, urn, **_):
            return {"id": urn}

        def get_userinfo(self):
            return {"sub": "123"}

    def factory(**kwargs):
        seen.append(kwargs["access_token"])
        return Client()

    path = tmp_path / "token"
    path.write_text(token + "\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(token + "\n"))
    assert main(
        [*argv, "--access-token-file", str(path) if source == "file" else "-"],
        env={"LINKEDIN_ACCESS_TOKEN": "stale-env-token"}, client_factory=factory,
    ) == 0
    assert seen == [token]
    output = capsys.readouterr()
    assert json.loads(output.out)
    assert token not in output.out + output.err
    assert output.err == ""


@pytest.mark.parametrize("contents", ["", "\n", "PRIVATE-FIRST\nPRIVATE-SECOND\n", "PRIVATE-FIRST\rPRIVATE-SECOND", "  "])
def test_invalid_token_files_fail_without_client_or_secret_echo(contents, tmp_path, capsys):
    path = tmp_path / "token"
    path.write_text(contents)
    assert main(["profile", "whoami", "--access-token-file", str(path)], env={},
                client_factory=lambda **_: pytest.fail("must not create client")) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "PRIVATE" not in output.err
    assert "--access-token-file" in output.err


def test_missing_token_file_has_concise_error(tmp_path, capsys):
    assert main(["profile", "whoami", "--access-token-file", str(tmp_path / "missing")],
                env={}, client_factory=lambda **_: pytest.fail("must not create client")) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "Cannot read" in output.err
    assert "Traceback" not in output.err


def test_token_stdin_refuses_terminal_without_reading(monkeypatch, capsys):
    class Terminal(io.StringIO):
        def isatty(self):
            return True

        def read(self, *_):
            pytest.fail("must not wait for terminal input")

    monkeypatch.setattr("sys.stdin", Terminal())
    assert main(["profile", "whoami", "--access-token-file", "-"], env={}) == 2
    assert "pipe" in capsys.readouterr().err


def test_direct_token_and_file_are_mutually_exclusive(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(["profile", "whoami", "--access-token", "DO-NOT-ECHO",
              "--access-token-file", str(tmp_path / "missing")], env={})
    assert error.value.code == 2
    assert "DO-NOT-ECHO" not in capsys.readouterr().err
