"""Exercise documented CLI arguments without evaluating shell snippets or calling APIs."""
import io
import json
import re
import shlex
from pathlib import Path

import pytest

from linkedin_cli.cli import build_parser, main

ROOT = Path(__file__).resolve().parents[1]
GUIDES = ["docs/credentials.md", "docs/onboarding.md"]


def _commands(guide):
    text = (ROOT / guide).read_text()
    for block in re.findall(r"```(?:bash|sh)\n(.*?)```", text, flags=re.DOTALL):
        for line in block.replace("\\\n", " ").splitlines():
            tokens = shlex.split(line, comments=True)
            if tokens[:3] != ["uv", "run", "lkdn"]:
                continue
            args = tokens[3:]
            # Redirection is a shell operation, not a CLI operand.
            if "<" in args:
                args = args[:args.index("<")]
            yield args


@pytest.mark.parametrize("guide", GUIDES)
def test_guides_show_working_file_and_stdin_credentials(guide, tmp_path, monkeypatch, capsys):
    examples = [args for args in _commands(guide)
                if args[:2] == ["profile", "whoami"] and "--access-token-file" in args]
    assert examples, "the guide must show private token input"
    sources = set()
    token_file = tmp_path / "token"
    token_file.write_text("documentation-test-token\n")
    token_file.chmod(0o600)

    class Client:
        def get_userinfo(self):
            return {"sub": "documentation-example"}

    def factory(**kwargs):
        assert kwargs["access_token"] == "documentation-test-token"
        return Client()

    for command in examples:
        assert command[:2] == ["profile", "whoami"], "only run the documented read example against a stub"
        args = list(command)
        index = args.index("--access-token-file") + 1
        if args[index] == "-":
            sources.add("stdin")
        else:
            sources.add("file")
            args[index] = str(token_file)
        monkeypatch.setattr("sys.stdin", io.StringIO("documentation-test-token\n"))
        assert main(args, env={}, client_factory=factory) == 0
        streams = capsys.readouterr()
        assert json.loads(streams.out)["sub"] == "documentation-example"
        assert "documentation-test-token" not in streams.out + streams.err
        assert streams.err == ""
    assert sources == {"file", "stdin"}


@pytest.mark.parametrize("guide", GUIDES)
def test_guides_confirm_the_correct_target_and_preview_without_credentials(guide, capsys):
    surfaces = set()
    previews = 0
    for command in _commands(guide):
        if command[:2] not in [["post", "delete"], ["comment", "delete"],
                               ["social-metadata", "set-comments-state"]]:
            continue
        args = build_parser(explicit_post_actions=True).parse_args(command)
        surface = ".".join(command[:2])
        surfaces.add(surface)
        if args.dry_run:
            previews += 1
            assert main(command, env={}, client_factory=lambda **_: pytest.fail("preview reached an API client")) == 0
            streams = capsys.readouterr()
            assert json.loads(streams.out)["action"] == surface
            assert streams.err == ""
        else:
            target = args.post_urn if surface == "post.delete" else (
                args.comment_id if surface == "comment.delete" else args.entity_urn)
            assert args.confirm == target, f"{guide}: destructive example must confirm its exact target"
    assert surfaces == {"post.delete", "comment.delete", "social-metadata.set-comments-state"}
    assert previews > 0, "the guide must show an offline dry-run plan"


@pytest.mark.parametrize("guide", GUIDES)
def test_guides_do_not_recommend_inline_token_cli_arguments(guide):
    for command in _commands(guide):
        assert "--access-token" not in command, "prefer file/stdin input in executable examples"
