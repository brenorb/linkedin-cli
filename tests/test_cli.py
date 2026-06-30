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


def test_cli_post_create_alias_uses_create_flow(capsys: pytest.CaptureFixture[str]) -> None:
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
        ["post", "create", "Ship", "it"],
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


def test_cli_post_with_video_uses_video_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"fake-mp4")
    captured: dict[str, object] = {}

    class StubClient:
        def create_text_post(self, *, author: str, commentary: str, visibility: str) -> object:
            raise AssertionError("text flow should not be used when --video is provided")

        def create_video_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            video_path: Path,
            title: str | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["video_path"] = video_path
            captured["title"] = title
            return type("Result", (), {"post_id": "urn:li:share:789"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--video",
            str(video_path),
            "--video-title",
            "Linus on abstraction",
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
        "video_path": video_path,
        "title": "Linus on abstraction",
    }
    assert "urn:li:share:789" in stdout


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


def test_cli_post_rejects_image_and_video_together(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["post", "--image", "/tmp/banner.png", "--video", "/tmp/clip.mp4", "Hello"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "image" in stderr.lower()
    assert "video" in stderr.lower()


def test_cli_post_requires_author_and_access_token(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["post", "Hello"], env={}, client_factory=_unused_client_factory)

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "access token" in stderr.lower()
    assert "author urn" in stderr.lower()


def test_cli_post_get_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_post(self, post_urn: str, *, view_context: str | None = None) -> dict[str, object]:
            captured["post_urn"] = post_urn
            captured["view_context"] = view_context
            return {
                "id": "urn:li:share:987",
                "author": "urn:li:person:env123",
                "commentary": "Hello from tests",
            }

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["post", "get", "urn:li:share:987", "--view-context", "AUTHOR"],
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
        "post_urn": "urn:li:share:987",
        "view_context": "AUTHOR",
    }
    assert '"urn:li:share:987"' in stdout
    assert '"Hello from tests"' in stdout


def test_cli_post_list_reads_author_from_environment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def list_posts(
            self,
            *,
            author: str,
            count: int,
            start: int,
            sort_by: str,
            view_context: str | None = None,
        ) -> dict[str, object]:
            captured["author"] = author
            captured["count"] = count
            captured["start"] = start
            captured["sort_by"] = sort_by
            captured["view_context"] = view_context
            return {
                "paging": {"start": 0, "count": 10, "links": []},
                "elements": [
                    {
                        "id": "urn:li:share:987",
                        "author": author,
                        "commentary": "Hello from tests",
                    }
                ],
            }

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["post", "list"],
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
        "count": 10,
        "start": 0,
        "sort_by": "LAST_MODIFIED",
        "view_context": None,
    }
    assert '"urn:li:share:987"' in stdout


def test_cli_post_list_requires_author(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["post", "list"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "author urn" in stderr.lower()


def test_cli_post_delete_reads_access_token_and_deletes_post(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def delete_post(self, post_urn: str) -> None:
            captured["post_urn"] = post_urn

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["post", "delete", "urn:li:share:987"],
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
        "post_urn": "urn:li:share:987",
    }
    assert "Deleted post urn:li:share:987" in stdout


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
