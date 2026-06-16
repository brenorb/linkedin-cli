from pathlib import Path

import pytest

from linkedin_cli.cli import main
from linkedin_cli.client import LinkedInApiError


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


def test_cli_post_with_image_uses_image_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    image_path = tmp_path / "banner.png"
    image_path.write_bytes(b"fakepng")
    captured: dict[str, object] = {}

    class StubClient:
        def create_text_post(self, *, author: str, commentary: str, visibility: str) -> object:
            raise AssertionError("text flow should not be used when --image is provided")

        def create_image_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            image_path: Path,
            alt_text: str | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["image_path"] = image_path
            captured["alt_text"] = alt_text
            return type("Result", (), {"post_id": "urn:li:share:456"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--image",
            str(image_path),
            "--alt-text",
            "Bitdevs banner",
            "Ship",
            "it",
        ],
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
        "image_path": image_path,
        "alt_text": "Bitdevs banner",
    }
    assert "urn:li:share:456" in stdout


def test_cli_post_rejects_alt_text_without_image(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["post", "--alt-text", "Bitdevs banner", "Hello"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "alt text" in stderr.lower()
    assert "image" in stderr.lower()


def test_cli_post_requires_author_and_access_token(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["post", "Hello"], env={}, client_factory=_unused_client_factory)

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "access token" in stderr.lower()
    assert "author urn" in stderr.lower()


def test_cli_profile_employment_history_reads_positions_from_profile_api(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_employment_history(self) -> list[dict[str, object]]:
            captured["called"] = "profile-api"
            return [
                {
                    "employer_name": "FACTORED",
                    "job_title": "AI Engineer",
                    "start_date": "2024-01",
                    "end_date": None,
                    "is_current": True,
                }
            ]

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["profile", "employment-history"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202505",
        "called": "profile-api",
    }
    assert '"FACTORED"' in stdout
    assert '"AI Engineer"' in stdout


def test_cli_profile_employment_history_can_use_identity_me(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_current_employment(self) -> list[dict[str, object]]:
            captured["called"] = "identity-me"
            return [
                {
                    "employer_name": "LinkedIn",
                    "job_title": "Senior Software Engineer",
                    "start_date": "2022-01",
                    "end_date": None,
                    "is_current": True,
                }
            ]

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["profile", "employment-history", "--source", "identity-me"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202510.03",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202510.03",
        "called": "identity-me",
    }
    assert '"LinkedIn"' in stdout
    assert '"Senior Software Engineer"' in stdout


def test_cli_profile_employment_history_requires_access_token(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["profile", "employment-history"],
        env={},
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "access token" in stderr.lower()


def test_cli_profile_employment_history_returns_1_on_api_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    closed = False

    class StubClient:
        def get_employment_history(self) -> list[dict[str, object]]:
            raise LinkedInApiError(403, "Access denied")

        def close(self) -> None:
            nonlocal closed
            closed = True

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        return StubClient()

    exit_code = main(
        ["profile", "employment-history"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
        },
        client_factory=client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 1
    assert closed is True
    assert "403" in stderr


def _unused_client_factory(*, access_token: str, api_version: str) -> object:
    raise AssertionError(f"client factory should not be called: {access_token=} {api_version=}")
