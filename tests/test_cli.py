import pytest

from linkedin_cli.cli import main


def test_cli_post_reads_required_values_from_environment(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_text_post(self, *, author: str, commentary: str, visibility: str) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            return type("Result", (), {"post_id": "urn:li:share:123"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["post", "Ship", "it"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202505",
        "author": "urn:li:person:env123",
        "commentary": "Ship it",
        "visibility": "PUBLIC",
    }
    assert "urn:li:share:123" in stdout


def test_cli_post_requires_author_and_access_token(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["post", "Hello"], env={}, client_factory=_unused_client_factory)

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "access token" in stderr.lower()
    assert "author urn" in stderr.lower()


def _unused_client_factory(*, access_token: str, api_version: str) -> object:
    raise AssertionError(f"client factory should not be called: {access_token=} {api_version=}")
