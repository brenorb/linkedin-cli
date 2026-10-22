import json

import pytest

from linkedin_cli.cli import main


CASES = [
    (["post", "delete", "urn:li:share:123"], "urn:li:share:123", "post.delete"),
    (["comment", "delete", "urn:li:share:123", "456"], "456", "comment.delete"),
    (["social-metadata", "set-comments-state", "urn:li:share:123", "--actor",
      "urn:li:person:abc", "--state", "CLOSED"], "urn:li:share:123", "social-metadata.set-comments-state"),
]


@pytest.mark.parametrize("argv,target,action", CASES)
@pytest.mark.parametrize("confirmation", [[], ["--confirm", "wrong-target"]])
def test_destructive_actions_fail_before_client_without_matching_confirmation(argv, target, action, confirmation, capsys):
    assert main([*argv, *confirmation], env={"LINKEDIN_ACCESS_TOKEN": "test-token"},
                client_factory=lambda **_: pytest.fail("unconfirmed operation reached client")) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "--confirm" in output.err
    assert target in output.err


@pytest.mark.parametrize("argv,target,action", CASES)
def test_dry_run_is_json_without_credentials_or_client(argv, target, action, tmp_path, capsys):
    assert main([*argv, "--dry-run", "--access-token-file", str(tmp_path / "missing")], env={},
                client_factory=lambda **_: pytest.fail("dry run reached client")) == 0
    output = capsys.readouterr()
    plan = json.loads(output.out)
    assert plan["action"] == action
    assert plan["target"] == "urn:li:share:123"
    if action == "comment.delete":
        assert plan["comment_id"] == target
    if action.startswith("social-metadata"):
        assert plan["state"] == "CLOSED"
        assert "delete" in plan["warning"].lower()
    assert output.err == ""


@pytest.mark.parametrize("argv,target,action", CASES)
def test_exact_confirmation_executes_once_without_reading_stdin(argv, target, action, monkeypatch, capsys):
    calls = []

    class Client:
        def delete_post(self, urn):
            calls.append(("post.delete", urn))

        def delete_comment(self, **kwargs):
            calls.append(("comment.delete", kwargs["comment_id"]))

        def update_social_metadata_comments_state(self, **kwargs):
            calls.append(("social-metadata.set-comments-state", kwargs["entity_urn"]))

    monkeypatch.setattr("sys.stdin.read", lambda *_: pytest.fail("must not prompt"))
    assert main([*argv, "--confirm", target], env={"LINKEDIN_ACCESS_TOKEN": "test-token"},
                client_factory=lambda **_: Client()) == 0
    assert calls == [(action, target)]
    assert capsys.readouterr().err == ""


def test_opening_comments_needs_no_confirmation(capsys):
    calls = []

    class Client:
        def update_social_metadata_comments_state(self, **kwargs):
            calls.append(kwargs)

    assert main(["social-metadata", "set-comments-state", "urn:li:share:123", "--actor",
                 "urn:li:person:abc", "--state", "OPEN"],
                env={"LINKEDIN_ACCESS_TOKEN": "test-token"}, client_factory=lambda **_: Client()) == 0
    assert calls[0]["comments_state"] == "OPEN"
    assert capsys.readouterr().err == ""
