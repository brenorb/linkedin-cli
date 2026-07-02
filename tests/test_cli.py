from pathlib import Path

import pytest

from linkedin_cli.cli import build_parser, main
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


def test_cli_parser_uses_requested_program_name() -> None:
    parser = build_parser(prog="lkdn")

    assert parser.prog == "lkdn"


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


def test_cli_post_with_image_urn_reuses_existing_asset(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_image_post_from_asset(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            image_urn: str,
            alt_text: str | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["image_urn"] = image_urn
            captured["alt_text"] = alt_text
            return type("Result", (), {"post_id": "urn:li:share:456"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--image-urn",
            "urn:li:image:123",
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
        "image_urn": "urn:li:image:123",
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


def test_cli_post_with_video_urn_reuses_existing_asset(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_video_post_from_asset(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            video_urn: str,
            title: str | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["video_urn"] = video_urn
            captured["title"] = title
            return type("Result", (), {"post_id": "urn:li:share:789"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--video-urn",
            "urn:li:video:123",
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
        "video_urn": "urn:li:video:123",
        "title": "Linus on abstraction",
    }
    assert "urn:li:share:789" in stdout


def test_cli_post_with_reshare_post_urn_uses_reshare_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_reshare_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            reshared_post_urn: str,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["reshared_post_urn"] = reshared_post_urn
            return type("Result", (), {"post_id": "urn:li:share:990"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--reshare-post-urn",
            "urn:li:share:777",
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
        "reshared_post_urn": "urn:li:share:777",
    }
    assert "urn:li:share:990" in stdout


def test_cli_post_with_document_upload_uses_document_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document_path = tmp_path / "deck.pdf"
    document_path.write_bytes(b"%PDF-1.7 fake")
    captured: dict[str, object] = {}

    class StubClient:
        def create_document_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            document_path: Path,
            title: str,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["document_path"] = document_path
            captured["title"] = title
            return type("Result", (), {"post_id": "urn:li:share:991"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--document",
            str(document_path),
            "--document-title",
            "June deck",
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
        "document_path": document_path,
        "title": "June deck",
    }
    assert "urn:li:share:991" in stdout


def test_cli_post_with_document_urn_reuses_existing_asset(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_document_post_from_asset(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            document_urn: str,
            title: str,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["document_urn"] = document_urn
            captured["title"] = title
            return type("Result", (), {"post_id": "urn:li:share:992"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--document-urn",
            "urn:li:document:123",
            "--document-title",
            "June deck",
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
        "document_urn": "urn:li:document:123",
        "title": "June deck",
    }
    assert "urn:li:share:992" in stdout


def test_cli_post_with_article_uses_article_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_article_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            article_url: str,
            title: str,
            description: str | None = None,
            thumbnail_image_urn: str | None = None,
            thumbnail_image_path: Path | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["article_url"] = article_url
            captured["title"] = title
            captured["description"] = description
            captured["thumbnail_image_urn"] = thumbnail_image_urn
            captured["thumbnail_image_path"] = thumbnail_image_path
            return type("Result", (), {"post_id": "urn:li:share:993"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--article-url",
            "https://example.com/post",
            "--article-title",
            "Deep systems",
            "--article-description",
            "A long read",
            "--article-thumbnail-urn",
            "urn:li:image:777",
            "Worth",
            "reading",
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
        "commentary": "Worth reading",
        "visibility": "PUBLIC",
        "article_url": "https://example.com/post",
        "title": "Deep systems",
        "description": "A long read",
        "thumbnail_image_urn": "urn:li:image:777",
        "thumbnail_image_path": None,
    }
    assert "urn:li:share:993" in stdout


def test_cli_post_with_multi_image_upload_uses_multi_image_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first_image = tmp_path / "one.png"
    second_image = tmp_path / "two.png"
    first_image.write_bytes(b"one")
    second_image.write_bytes(b"two")
    captured: dict[str, object] = {}

    class StubClient:
        def create_multi_image_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            image_paths: list[Path],
            alt_texts: list[str] | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["image_paths"] = image_paths
            captured["alt_texts"] = alt_texts
            return type("Result", (), {"post_id": "urn:li:share:994"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--multi-image",
            str(first_image),
            "--multi-image",
            str(second_image),
            "Photo",
            "dump",
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
        "commentary": "Photo dump",
        "visibility": "PUBLIC",
        "image_paths": [first_image, second_image],
        "alt_texts": None,
    }
    assert "urn:li:share:994" in stdout


def test_cli_post_rejects_article_without_title(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "post",
            "--article-url",
            "https://example.com/post",
            "Worth",
            "reading",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "article" in stderr.lower()
    assert "title" in stderr.lower()


def test_cli_post_with_multi_image_upload_alt_text_uses_multi_image_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first_image = tmp_path / "one.png"
    second_image = tmp_path / "two.png"
    first_image.write_bytes(b"one")
    second_image.write_bytes(b"two")
    captured: dict[str, object] = {}

    class StubClient:
        def create_multi_image_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            image_paths: list[Path],
            alt_texts: list[str] | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["image_paths"] = image_paths
            captured["alt_texts"] = alt_texts
            return type("Result", (), {"post_id": "urn:li:share:994"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--multi-image",
            str(first_image),
            "--multi-image",
            str(second_image),
            "--multi-image-alt-text",
            "First image",
            "--multi-image-alt-text",
            "Second image",
            "Photo",
            "dump",
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
        "commentary": "Photo dump",
        "visibility": "PUBLIC",
        "image_paths": [first_image, second_image],
        "alt_texts": ["First image", "Second image"],
    }
    assert "urn:li:share:994" in stdout


def test_cli_post_with_article_thumbnail_upload_uses_article_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    thumbnail_path = tmp_path / "thumb.png"
    thumbnail_path.write_bytes(b"thumb")
    captured: dict[str, object] = {}

    class StubClient:
        def create_article_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            article_url: str,
            title: str,
            description: str | None = None,
            thumbnail_image_urn: str | None = None,
            thumbnail_image_path: Path | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["article_url"] = article_url
            captured["title"] = title
            captured["description"] = description
            captured["thumbnail_image_urn"] = thumbnail_image_urn
            captured["thumbnail_image_path"] = thumbnail_image_path
            return type("Result", (), {"post_id": "urn:li:share:993"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--article-url",
            "https://example.com/post",
            "--article-title",
            "Deep systems",
            "--article-thumbnail",
            str(thumbnail_path),
            "Worth",
            "reading",
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
        "commentary": "Worth reading",
        "visibility": "PUBLIC",
        "article_url": "https://example.com/post",
        "title": "Deep systems",
        "description": None,
        "thumbnail_image_urn": None,
        "thumbnail_image_path": thumbnail_path,
    }
    assert "urn:li:share:993" in stdout


def test_cli_post_with_video_captions_and_thumbnail_uses_video_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    video_path = tmp_path / "clip.mp4"
    captions_path = tmp_path / "clip.vtt"
    thumbnail_path = tmp_path / "thumb.png"
    video_path.write_bytes(b"video")
    captions_path.write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nHello\n", encoding="utf-8")
    thumbnail_path.write_bytes(b"thumb")
    captured: dict[str, object] = {}

    class StubClient:
        def create_video_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            video_path: Path,
            title: str | None = None,
            captions_path: Path | None = None,
            thumbnail_path: Path | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["video_path"] = video_path
            captured["title"] = title
            captured["captions_path"] = captions_path
            captured["thumbnail_path"] = thumbnail_path
            return type("Result", (), {"post_id": "urn:li:share:995"})()

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
            "Linus clip",
            "--video-captions",
            str(captions_path),
            "--video-thumbnail",
            str(thumbnail_path),
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
        "title": "Linus clip",
        "captions_path": captions_path,
        "thumbnail_path": thumbnail_path,
    }
    assert "urn:li:share:995" in stdout


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


def test_cli_post_rejects_image_path_and_image_urn_together(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", "--image", "/tmp/banner.png", "--image-urn", "urn:li:image:123", "Hello"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "image" in stderr.lower()
    assert "urn" in stderr.lower()


def test_cli_post_rejects_reshare_with_uploaded_media(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "post",
            "--reshare-post-urn",
            "urn:li:share:123",
            "--image",
            "/tmp/banner.png",
            "Hello",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "reshare" in stderr.lower()
    assert "image" in stderr.lower()


def test_cli_post_rejects_document_upload_without_title(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["post", "--document", "/tmp/deck.pdf", "Hello"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "document" in stderr.lower()
    assert "title" in stderr.lower()


def test_cli_post_rejects_multi_image_with_fewer_than_two_images(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", "--multi-image", "/tmp/one.png", "Hello"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "multi-image" in stderr.lower()
    assert "2" in stderr


def test_cli_post_rejects_multi_image_with_more_than_twenty_images(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", *sum([["--multi-image", f"/tmp/{index}.png"] for index in range(21)], []), "Hello"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "multi-image" in stderr.lower()
    assert "20" in stderr


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


def test_cli_post_batch_get_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_posts(
            self,
            post_urns: list[str],
            *,
            view_context: str | None = None,
        ) -> dict[str, object]:
            captured["post_urns"] = post_urns
            captured["view_context"] = view_context
            return {
                "results": {
                    "urn:li:share:123": {"id": "urn:li:share:123"},
                    "urn:li:share:456": {"id": "urn:li:share:456"},
                },
                "statuses": {},
                "errors": {},
            }

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["post", "batch-get", "urn:li:share:123", "urn:li:share:456", "--view-context", "AUTHOR"],
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
        "post_urns": ["urn:li:share:123", "urn:li:share:456"],
        "view_context": "AUTHOR",
    }
    assert '"urn:li:share:123"' in stdout
    assert '"urn:li:share:456"' in stdout


def test_cli_document_get_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_document(self, document_urn: str) -> dict[str, object]:
            captured["document_urn"] = document_urn
            return {"id": document_urn, "status": "AVAILABLE"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["document", "get", "urn:li:document:123"],
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
        "document_urn": "urn:li:document:123",
    }
    assert '"urn:li:document:123"' in stdout


def test_cli_document_list_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_documents(self, document_urns: list[str]) -> dict[str, object]:
            captured["document_urns"] = document_urns
            return {
                "results": {
                    "urn:li:document:123": {"id": "urn:li:document:123"},
                    "urn:li:document:456": {"id": "urn:li:document:456"},
                }
            }

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["document", "list", "--id", "urn:li:document:123", "--id", "urn:li:document:456"],
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
        "document_urns": ["urn:li:document:123", "urn:li:document:456"],
    }
    assert '"urn:li:document:456"' in stdout


def test_cli_post_with_poll_uses_poll_flow(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_poll_post(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            question: str,
            options: list[str],
            duration: str,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["question"] = question
            captured["options"] = options
            captured["duration"] = duration
            return type("Result", (), {"post_id": "urn:li:share:996"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--poll-question",
            "Favorite color?",
            "--poll-option",
            "Red",
            "--poll-option",
            "Blue",
            "--poll-duration",
            "THREE_DAYS",
            "Vote",
            "now",
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
        "commentary": "Vote now",
        "visibility": "PUBLIC",
        "question": "Favorite color?",
        "options": ["Red", "Blue"],
        "duration": "THREE_DAYS",
    }
    assert "urn:li:share:996" in stdout


def test_cli_post_with_multi_image_urns_uses_asset_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_multi_image_post_from_assets(
            self,
            *,
            author: str,
            commentary: str,
            visibility: str,
            image_urns: list[str],
            alt_texts: list[str] | None = None,
        ) -> object:
            captured["author"] = author
            captured["commentary"] = commentary
            captured["visibility"] = visibility
            captured["image_urns"] = image_urns
            captured["alt_texts"] = alt_texts
            return type("Result", (), {"post_id": "urn:li:share:997"})()

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "--multi-image-urn",
            "urn:li:image:123",
            "--multi-image-urn",
            "urn:li:image:456",
            "--multi-image-alt-text",
            "First image",
            "--multi-image-alt-text",
            "Second image",
            "Photo",
            "dump",
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
        "commentary": "Photo dump",
        "visibility": "PUBLIC",
        "image_urns": ["urn:li:image:123", "urn:li:image:456"],
        "alt_texts": ["First image", "Second image"],
    }
    assert "urn:li:share:997" in stdout


def test_cli_comment_get_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_comment(self, target_urn: str, comment_id: str) -> dict[str, object]:
            captured["target_urn"] = target_urn
            captured["comment_id"] = comment_id
            return {"id": comment_id, "message": {"text": "Hello"}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["comment", "get", "urn:li:share:123", "456"],
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
        "target_urn": "urn:li:share:123",
        "comment_id": "456",
    }
    assert '"Hello"' in stdout


def test_cli_comment_list_reads_target_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def list_comments(self, *, target_urn: str, count: int, start: int) -> dict[str, object]:
            captured["target_urn"] = target_urn
            captured["count"] = count
            captured["start"] = start
            return {"elements": [{"id": "456"}], "paging": {"count": count, "start": start, "links": []}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["comment", "list", "urn:li:share:123", "--count", "25", "--start", "10"],
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
        "target_urn": "urn:li:share:123",
        "count": 25,
        "start": 10,
    }
    assert '"456"' in stdout


def test_cli_comment_batch_get_reads_target_and_ids(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_comments(self, target_urn: str, comment_ids: list[str]) -> dict[str, object]:
            captured["target_urn"] = target_urn
            captured["comment_ids"] = comment_ids
            return {"results": {"456": {"id": "456"}}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["comment", "batch-get", "urn:li:share:123", "456", "789"],
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
        "target_urn": "urn:li:share:123",
        "comment_ids": ["456", "789"],
    }
    assert '"456"' in stdout


def test_cli_comment_create_uses_actor_text_attributes_and_content(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    attributes_path = tmp_path / "attributes.json"
    attributes_path.write_text('[{"start":0,"length":5,"value":{"member":"urn:li:person:abc"}}]', encoding="utf-8")
    captured: dict[str, object] = {}

    class StubClient:
        def create_comment(
            self,
            *,
            target_urn: str,
            actor: str,
            text: str,
            parent_comment: str | None = None,
            attributes: list[dict[str, object]] | None = None,
            content_image_urn: str | None = None,
        ) -> dict[str, object]:
            captured["target_urn"] = target_urn
            captured["actor"] = actor
            captured["text"] = text
            captured["parent_comment"] = parent_comment
            captured["attributes"] = attributes
            captured["content_image_urn"] = content_image_urn
            return {"id": "456", "message": {"text": text}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "comment",
            "create",
            "urn:li:share:123",
            "--actor",
            "urn:li:person:abc",
            "--attributes-json",
            str(attributes_path),
            "--content-image-urn",
            "urn:li:image:123",
            "Hello",
            "world",
        ],
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
        "target_urn": "urn:li:share:123",
        "actor": "urn:li:person:abc",
        "text": "Hello world",
        "parent_comment": None,
        "attributes": [{"start": 0, "length": 5, "value": {"member": "urn:li:person:abc"}}],
        "content_image_urn": "urn:li:image:123",
    }
    assert '"456"' in stdout


def test_cli_comment_edit_uses_comment_id_text_and_attributes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    attributes_path = tmp_path / "attributes.json"
    attributes_path.write_text('[{"start":0,"length":7,"value":{"member":"urn:li:person:def"}}]', encoding="utf-8")
    captured: dict[str, object] = {}

    class StubClient:
        def update_comment(
            self,
            *,
            target_urn: str,
            comment_id: str,
            text: str,
            actor: str | None = None,
            attributes: list[dict[str, object]] | None = None,
        ) -> None:
            captured["target_urn"] = target_urn
            captured["comment_id"] = comment_id
            captured["text"] = text
            captured["actor"] = actor
            captured["attributes"] = attributes

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "comment",
            "edit",
            "urn:li:share:123",
            "456",
            "--actor",
            "urn:li:organization:123",
            "--text",
            "Updated",
            "comment",
            "--attributes-json",
            str(attributes_path),
        ],
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
        "target_urn": "urn:li:share:123",
        "comment_id": "456",
        "text": "Updated comment",
        "actor": "urn:li:organization:123",
        "attributes": [{"start": 0, "length": 7, "value": {"member": "urn:li:person:def"}}],
    }
    assert "Updated comment 456" in stdout


def test_cli_comment_delete_uses_comment_id_and_optional_actor(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def delete_comment(
            self,
            *,
            target_urn: str,
            comment_id: str,
            actor: str | None = None,
        ) -> None:
            captured["target_urn"] = target_urn
            captured["comment_id"] = comment_id
            captured["actor"] = actor

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "comment",
            "delete",
            "urn:li:share:123",
            "456",
            "--actor",
            "urn:li:organization:123",
        ],
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
        "target_urn": "urn:li:share:123",
        "comment_id": "456",
        "actor": "urn:li:organization:123",
    }
    assert "Deleted comment 456" in stdout


def test_cli_comment_create_rejects_reply_content_entities(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "comment",
            "create",
            "urn:li:share:123",
            "--actor",
            "urn:li:person:abc",
            "--parent-comment",
            "urn:li:comment:(urn:li:share:123,456)",
            "--content-image-urn",
            "urn:li:image:123",
            "Reply",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "reply" in stderr.lower()
    assert "content" in stderr.lower()


def test_cli_comment_edit_rejects_comment_urn_target(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "comment",
            "edit",
            "urn:li:comment:(urn:li:share:123,456)",
            "456",
            "--text",
            "Updated",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "share or ugcpost urn" in stderr.lower()


def test_cli_comment_delete_rejects_comment_urn_target(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "comment",
            "delete",
            "urn:li:comment:(urn:li:share:123,456)",
            "456",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "share or ugcpost urn" in stderr.lower()


def test_cli_reaction_create_uses_actor_and_root(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def create_reaction(self, *, actor: str, root: str, reaction_type: str) -> dict[str, object]:
            captured["actor"] = actor
            captured["root"] = root
            captured["reaction_type"] = reaction_type
            return {"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "reaction",
            "create",
            "--actor",
            "urn:li:person:abc",
            "--root",
            "urn:li:share:123",
            "--type",
            "LIKE",
        ],
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
        "actor": "urn:li:person:abc",
        "root": "urn:li:share:123",
        "reaction_type": "LIKE",
    }
    assert '"urn:li:reaction:' in stdout


def test_cli_reaction_get_uses_actor_and_entity(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_reaction(self, *, actor: str, entity: str) -> dict[str, object]:
            captured["actor"] = actor
            captured["entity"] = entity
            return {"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "reaction",
            "get",
            "--actor",
            "urn:li:person:abc",
            "--entity",
            "urn:li:share:123",
        ],
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
        "actor": "urn:li:person:abc",
        "entity": "urn:li:share:123",
    }
    assert '"urn:li:reaction:' in stdout


def test_cli_reaction_list_uses_entity_and_sort(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def list_reactions(
            self,
            *,
            entity: str,
            count: int,
            start: int,
            sort: str,
        ) -> dict[str, object]:
            captured["entity"] = entity
            captured["count"] = count
            captured["start"] = start
            captured["sort"] = sort
            return {"elements": [{"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"}]}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "reaction",
            "list",
            "urn:li:share:123",
            "--count",
            "25",
            "--start",
            "10",
            "--sort",
            "RELEVANCE",
        ],
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
        "entity": "urn:li:share:123",
        "count": 25,
        "start": 10,
        "sort": "RELEVANCE",
    }
    assert '"urn:li:reaction:' in stdout


def test_cli_reaction_batch_get_uses_composite_keys(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_reactions(self, keys: list[tuple[str, str]]) -> dict[str, object]:
            captured["keys"] = keys
            return {"results": {"(actor:urn%3Ali%3Aperson%3Aabc,entity:urn%3Ali%3Ashare%3A123)": {"id": "urn:li:reaction:(urn:li:person:abc,urn:li:share:123)"}}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "reaction",
            "batch-get",
            "--key",
            "urn:li:person:abc",
            "urn:li:share:123",
            "--key",
            "urn:li:organization:456",
            "urn:li:comment:(urn:li:share:123,789)",
        ],
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
        "keys": [
            ("urn:li:person:abc", "urn:li:share:123"),
            ("urn:li:organization:456", "urn:li:comment:(urn:li:share:123,789)"),
        ],
    }
    assert '"urn:li:reaction:' in stdout


def test_cli_reaction_delete_uses_actor_and_entity(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def delete_reaction(self, *, actor: str, entity: str) -> None:
            captured["actor"] = actor
            captured["entity"] = entity

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "reaction",
            "delete",
            "--actor",
            "urn:li:person:abc",
            "--entity",
            "urn:li:share:123",
        ],
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
        "actor": "urn:li:person:abc",
        "entity": "urn:li:share:123",
    }
    assert "Deleted reaction" in stdout


def test_cli_social_metadata_get_reads_entity(capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_social_metadata(self, entity_urn: str) -> dict[str, object]:
            captured["entity_urn"] = entity_urn
            return {"entity": entity_urn, "commentsState": "OPEN"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["social-metadata", "get", "urn:li:share:123"],
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
        "entity_urn": "urn:li:share:123",
    }
    assert '"commentsState": "OPEN"' in stdout


def test_cli_social_metadata_batch_get_reads_entities(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_social_metadata(self, entity_urns: list[str]) -> dict[str, object]:
            captured["entity_urns"] = entity_urns
            return {"results": {"urn:li:share:123": {"commentsState": "OPEN"}}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["social-metadata", "batch-get", "urn:li:share:123", "urn:li:comment:(urn:li:share:123,456)"],
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
        "entity_urns": ["urn:li:share:123", "urn:li:comment:(urn:li:share:123,456)"],
    }
    assert '"commentsState": "OPEN"' in stdout


def test_cli_social_metadata_set_comments_state_uses_actor_and_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def update_social_metadata_comments_state(
            self,
            *,
            entity_urn: str,
            actor: str,
            comments_state: str,
        ) -> None:
            captured["entity_urn"] = entity_urn
            captured["actor"] = actor
            captured["comments_state"] = comments_state

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "social-metadata",
            "set-comments-state",
            "urn:li:share:123",
            "--actor",
            "urn:li:person:abc",
            "--state",
            "CLOSED",
        ],
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
        "entity_urn": "urn:li:share:123",
        "actor": "urn:li:person:abc",
        "comments_state": "CLOSED",
    }
    assert "Updated social metadata" in stdout


def test_cli_social_metadata_set_comments_state_rejects_comment_urn_target(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "social-metadata",
            "set-comments-state",
            "urn:li:comment:(urn:li:share:123,456)",
            "--actor",
            "urn:li:person:abc",
            "--state",
            "CLOSED",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "thread urn" in stderr.lower()


def test_cli_organization_members_lists_access_by_organization(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def list_organization_access_by_organization(
            self,
            *,
            organization: str,
            count: int,
            start: int,
            role: str | None = None,
            state: str | None = None,
        ) -> dict[str, object]:
            captured["organization"] = organization
            captured["count"] = count
            captured["start"] = start
            captured["role"] = role
            captured["state"] = state
            return {"elements": [{"roleAssignee": "urn:li:person:abc"}], "paging": {"count": count, "start": start, "links": []}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["organization", "members", "urn:li:organization:2414183", "--role", "ADMINISTRATOR", "--state", "APPROVED"],
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
        "organization": "urn:li:organization:2414183",
        "count": 100,
        "start": 0,
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
    }
    assert '"urn:li:person:abc"' in stdout


def test_cli_organization_members_accepts_recruiting_poster_role(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def list_organization_access_by_organization(
            self,
            *,
            organization: str,
            count: int,
            start: int,
            role: str | None = None,
            state: str | None = None,
        ) -> dict[str, object]:
            captured["role"] = role
            return {"elements": [], "paging": {"count": count, "start": start, "links": []}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        return StubClient()

    exit_code = main(
        ["organization", "members", "urn:li:organization:2414183", "--role", "RECRUITING_POSTER"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=client_factory,
    )

    assert exit_code == 0
    assert captured == {"role": "RECRUITING_POSTER"}


def test_cli_profile_whoami_accepts_api_version_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_userinfo(self) -> dict[str, object]:
            return {"sub": "abc123"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["profile", "whoami", "--api-version", "202507"],
        env={"LINKEDIN_ACCESS_TOKEN": "env-token"},
        client_factory=client_factory,
    )

    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202507",
    }


def test_cli_profile_whoami_can_use_profile_api_source(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_profile_identity(self) -> dict[str, object]:
            captured["called"] = "profile-api"
            return {"id": "abc123"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["profile", "whoami", "--source", "profile-api"],
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
    assert '"id": "abc123"' in stdout


def test_cli_profile_whoami_identity_me_adds_person_urn(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class StubClient:
        def get_identity_profile(self) -> dict[str, object]:
            return {"id": "abc123", "localizedFirstName": "Breno"}

    exit_code = main(
        ["profile", "whoami", "--source", "identity-me"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
            "LINKEDIN_IDENTITY_API_VERSION": "202510.03",
        },
        client_factory=lambda **_: StubClient(),
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert '"person_urn": "urn:li:person:abc123"' in stdout


def test_cli_profile_whoami_identity_me_requires_identity_api_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["profile", "whoami", "--source", "identity-me"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "identity api version" in stderr.lower()


def test_cli_profile_whoami_passes_identity_api_version_override(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_identity_profile(self) -> dict[str, object]:
            captured["called"] = "identity-me"
            return {"id": "abc123"}

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        identity_api_version: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["identity_api_version"] = identity_api_version
        return StubClient()

    exit_code = main(
        [
            "profile",
            "whoami",
            "--source",
            "identity-me",
            "--identity-api-version",
            "202510.03",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202606",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202606",
        "identity_api_version": "202510.03",
        "called": "identity-me",
    }
    assert '"person_urn": "urn:li:person:abc123"' in stdout

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


def test_cli_post_list_rejects_count_above_linkedin_limit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", "list", "--count", "101"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "count" in stderr.lower()
    assert "100" in stderr


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


def test_cli_organization_list_uses_authenticated_viewer_finder(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def list_organization_access(
            self,
            *,
            count: int,
            start: int,
            role: str | None = None,
            state: str | None = None,
        ) -> dict[str, object]:
            captured["count"] = count
            captured["start"] = start
            captured["role"] = role
            captured["state"] = state
            return {
                "elements": [
                    {
                        "organization": "urn:li:organization:2414183",
                        "roleAssignee": "urn:li:person:viewer123",
                        "role": "ADMINISTRATOR",
                        "state": "APPROVED",
                    }
                ],
                "paging": {"count": count, "start": start, "links": []},
            }

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["organization", "list", "--role", "ADMINISTRATOR", "--state", "APPROVED"],
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
        "count": 100,
        "start": 0,
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
    }
    assert '"organization": "urn:li:organization:2414183"' in stdout


def test_cli_organization_preflight_summarizes_posting_capability(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def preflight_organization_author(
            self,
            *,
            role_assignee: str,
            organization: str,
        ) -> dict[str, object]:
            captured["role_assignee"] = role_assignee
            captured["organization"] = organization
            return {
                "organization": organization,
                "roleAssignee": role_assignee,
                "aclApprovedRoles": ["CONTENT_ADMINISTRATOR"],
                "roles": ["CONTENT_ADMINISTRATOR"],
                "states": ["APPROVED"],
                "canCreateOrganicPosts": True,
                "canReadOrganizationPosts": True,
                "canEditOrganicPosts": False,
                "canDeleteOrganicPosts": False,
            }

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["organization", "preflight", "urn:li:organization:2414183"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_MEMBER_URN": "urn:li:person:env123",
            "LINKEDIN_API_VERSION": "202505",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202505",
        "role_assignee": "urn:li:person:env123",
        "organization": "urn:li:organization:2414183",
    }
    assert '"canCreateOrganicPosts": true' in stdout
    assert '"CONTENT_ADMINISTRATOR"' in stdout


def test_cli_organization_commands_require_member_urn(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["organization", "preflight", "urn:li:organization:2414183"],
        env={"LINKEDIN_ACCESS_TOKEN": "env-token"},
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "member urn" in stderr.lower()


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


def test_cli_post_edit_updates_post(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def update_post(
            self,
            post_urn: str,
            *,
            commentary: str | None = None,
            content_call_to_action_label: str | None = None,
            content_landing_page: str | None = None,
            lifecycle_state: str | None = None,
        ) -> None:
            captured["post_urn"] = post_urn
            captured["commentary"] = commentary
            captured["content_call_to_action_label"] = content_call_to_action_label
            captured["content_landing_page"] = content_landing_page
            captured["lifecycle_state"] = lifecycle_state

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "edit",
            "urn:li:share:987",
            "--text",
            "Edited text",
            "--cta-label",
            "LEARN_MORE",
            "--landing-page",
            "https://example.com",
        ],
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
        "commentary": "Edited text",
        "content_call_to_action_label": "LEARN_MORE",
        "content_landing_page": "https://example.com",
        "lifecycle_state": None,
    }
    assert "Updated post urn:li:share:987" in stdout


def test_cli_post_edit_can_update_lifecycle_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def update_post(
            self,
            post_urn: str,
            *,
            commentary: str | None = None,
            content_call_to_action_label: str | None = None,
            content_landing_page: str | None = None,
            lifecycle_state: str | None = None,
        ) -> None:
            captured["post_urn"] = post_urn
            captured["lifecycle_state"] = lifecycle_state

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        [
            "post",
            "edit",
            "urn:li:share:987",
            "--lifecycle-state",
            "PUBLISHED",
        ],
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
        "lifecycle_state": "PUBLISHED",
    }
    assert "Updated post urn:li:share:987" in stdout


def test_cli_post_edit_requires_at_least_one_change(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", "edit", "urn:li:share:987"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "at least one" in stderr.lower()


def test_cli_image_get_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_image(self, image_urn: str) -> dict[str, object]:
            captured["image_urn"] = image_urn
            return {"id": image_urn, "status": "AVAILABLE"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["image", "get", "urn:li:image:123"],
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
        "image_urn": "urn:li:image:123",
    }
    assert '"urn:li:image:123"' in stdout


def test_cli_image_list_batch_gets_assets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_images(self, image_urns: list[str]) -> dict[str, object]:
            captured["image_urns"] = image_urns
            return {"results": {image_urns[0]: {"id": image_urns[0]}}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["image", "list", "--id", "urn:li:image:123", "--id", "urn:li:image:456"],
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
        "image_urns": ["urn:li:image:123", "urn:li:image:456"],
    }
    assert '"urn:li:image:123"' in stdout


def test_cli_video_get_reads_access_token_and_prints_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_video(self, video_urn: str) -> dict[str, object]:
            captured["video_urn"] = video_urn
            return {"id": video_urn, "status": "AVAILABLE"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["video", "get", "urn:li:video:123"],
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
        "video_urn": "urn:li:video:123",
    }
    assert '"urn:li:video:123"' in stdout


def test_cli_video_list_batch_gets_assets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def batch_get_videos(self, video_urns: list[str]) -> dict[str, object]:
            captured["video_urns"] = video_urns
            return {"results": {video_urns[0]: {"id": video_urns[0]}}}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["video", "list", "--id", "urn:li:video:123", "--id", "urn:li:video:456"],
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
        "video_urns": ["urn:li:video:123", "urn:li:video:456"],
    }
    assert '"urn:li:video:123"' in stdout


def test_cli_profile_whoami_uses_userinfo_by_default(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_userinfo(self) -> dict[str, object]:
            captured["called"] = "userinfo"
            return {"sub": "abc123", "name": "Breno Brito"}

    def client_factory(*, access_token: str, api_version: str) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        return StubClient()

    exit_code = main(
        ["profile", "whoami"],
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
        "called": "userinfo",
    }
    assert '"person_urn": "urn:li:person:abc123"' in stdout


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

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        identity_api_version: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["identity_api_version"] = identity_api_version
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--source",
            "identity-me",
            "--identity-api-version",
            "202510.03",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_API_VERSION": "202606",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202606",
        "identity_api_version": "202510.03",
        "called": "identity-me",
    }
    assert '"LinkedIn"' in stdout
    assert '"Senior Software Engineer"' in stdout


def test_cli_profile_employment_history_can_use_voyager_private(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
            captured["called"] = "voyager-private"
            captured["public_identifier"] = public_identifier
            return [
                {
                    "employer_name": "Factored",
                    "job_title": "Machine Learning Engineer",
                    "start_date": "2025-04",
                    "end_date": "2025-12",
                    "is_current": False,
                }
            ]

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        voyager_li_at: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_csrf_token: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["voyager_li_at"] = voyager_li_at
        captured["voyager_jsessionid"] = voyager_jsessionid
        captured["voyager_csrf_token"] = voyager_csrf_token
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--source",
            "voyager-private",
        ],
        env={
            "LINKEDIN_API_VERSION": "202606",
            "LINKEDIN_VOYAGER_LI_AT": "test-li-at",
            "LINKEDIN_VOYAGER_JSESSIONID": '"ajax:123"',
            "LINKEDIN_PROFILE_PUBLIC_ID": "brenorb",
        },
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "",
        "api_version": "202606",
        "voyager_li_at": "test-li-at",
        "voyager_jsessionid": '"ajax:123"',
        "voyager_csrf_token": None,
        "called": "voyager-private",
        "public_identifier": "brenorb",
    }
    assert '"Factored"' in stdout
    assert '"Machine Learning Engineer"' in stdout


def test_cli_profile_employment_history_can_load_voyager_session_from_browser(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
            captured["called"] = "voyager-private"
            captured["public_identifier"] = public_identifier
            return [
                {
                    "employer_name": "Factored",
                    "job_title": "Machine Learning Engineer",
                    "start_date": "2025-04",
                    "end_date": "2025-12",
                    "is_current": False,
                }
            ]

    class Session:
        li_at = "browser-li-at"
        jsessionid = '"ajax:browser"'
        csrf_token = "ajax:browser"

    monkeypatch.setattr("linkedin_cli.cli.load_voyager_session_from_browser", lambda **_: Session())

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        voyager_li_at: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_csrf_token: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["voyager_li_at"] = voyager_li_at
        captured["voyager_jsessionid"] = voyager_jsessionid
        captured["voyager_csrf_token"] = voyager_csrf_token
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--source",
            "voyager-private",
            "--browser",
            "chrome",
            "--public-id",
            "brenorb",
        ],
        env={},
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "",
        "api_version": "202606",
        "voyager_li_at": "browser-li-at",
        "voyager_jsessionid": '"ajax:browser"',
        "voyager_csrf_token": "ajax:browser",
        "called": "voyager-private",
        "public_identifier": "brenorb",
    }
    assert '"Factored"' in stdout


def test_cli_profile_employment_history_falls_back_to_voyager_on_api_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_employment_history(self) -> list[dict[str, object]]:
            captured["official_called"] = True
            raise LinkedInApiError(403, "Access denied")

        def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
            captured["voyager_called"] = public_identifier
            return [
                {
                    "employer_name": "Factored",
                    "job_title": "Machine Learning Engineer",
                    "start_date": "2025-04",
                    "end_date": "2025-12",
                    "is_current": False,
                }
            ]

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        voyager_li_at: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_csrf_token: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["voyager_li_at"] = voyager_li_at
        captured["voyager_jsessionid"] = voyager_jsessionid
        captured["voyager_csrf_token"] = voyager_csrf_token
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--public-id",
            "brenorb",
            "--li-at",
            "test-li-at",
            "--jsessionid",
            '"ajax:123"',
        ],
        env={"LINKEDIN_ACCESS_TOKEN": "env-token"},
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202606",
        "voyager_li_at": "test-li-at",
        "voyager_jsessionid": '"ajax:123"',
        "voyager_csrf_token": None,
        "official_called": True,
        "voyager_called": "brenorb",
    }
    assert '"Factored"' in stdout


def test_cli_profile_employment_history_can_use_voyager_without_access_token(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
            captured["voyager_called"] = public_identifier
            return [
                {
                    "employer_name": "Factored",
                    "job_title": "Machine Learning Engineer",
                    "start_date": "2025-04",
                    "end_date": "2025-12",
                    "is_current": False,
                }
            ]

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        voyager_li_at: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_csrf_token: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["voyager_li_at"] = voyager_li_at
        captured["voyager_jsessionid"] = voyager_jsessionid
        captured["voyager_csrf_token"] = voyager_csrf_token
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--public-id",
            "brenorb",
            "--li-at",
            "test-li-at",
            "--jsessionid",
            '"ajax:123"',
        ],
        env={},
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "",
        "api_version": "202606",
        "voyager_li_at": "test-li-at",
        "voyager_jsessionid": '"ajax:123"',
        "voyager_csrf_token": None,
        "voyager_called": "brenorb",
    }
    assert '"Factored"' in stdout


def test_cli_profile_employment_history_falls_back_to_chrome_profile_when_voyager_is_gone(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
            captured["voyager_called"] = public_identifier
            raise LinkedInApiError(410, '{"status":410}')

    class Session:
        li_at = "browser-li-at"
        jsessionid = '"ajax:browser"'
        csrf_token = "ajax:browser"

    monkeypatch.setattr("linkedin_cli.cli.load_voyager_session_from_browser", lambda **_: Session())
    monkeypatch.setattr(
        "linkedin_cli.cli.load_employment_history_from_chrome_profile",
        lambda public_identifier: [
            {
                "employer_name": "Factored",
                "job_title": "Machine Learning Engineer",
                "start_date": "2025-04",
                "end_date": None,
                "is_current": True,
            }
        ],
    )

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        voyager_li_at: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_csrf_token: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["voyager_li_at"] = voyager_li_at
        captured["voyager_jsessionid"] = voyager_jsessionid
        captured["voyager_csrf_token"] = voyager_csrf_token
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--public-id",
            "brenorb",
            "--browser",
            "chrome",
        ],
        env={},
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "",
        "api_version": "202606",
        "voyager_li_at": "browser-li-at",
        "voyager_jsessionid": '"ajax:browser"',
        "voyager_csrf_token": "ajax:browser",
        "voyager_called": "brenorb",
    }
    assert '"Factored"' in stdout
    assert '"Machine Learning Engineer"' in stdout


def test_cli_profile_employment_history_falls_back_to_chrome_profile_after_official_and_voyager_errors(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class StubClient:
        def get_employment_history(self) -> list[dict[str, object]]:
            captured["official_called"] = True
            raise LinkedInApiError(403, "Access denied")

        def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
            captured["voyager_called"] = public_identifier
            raise LinkedInApiError(410, '{"status":410}')

    monkeypatch.setattr(
        "linkedin_cli.cli.load_employment_history_from_chrome_profile",
        lambda public_identifier: [
            {
                "employer_name": "Factored",
                "job_title": "Machine Learning Engineer",
                "start_date": "2025-04",
                "end_date": None,
                "is_current": True,
            }
        ],
    )

    def client_factory(
        *,
        access_token: str,
        api_version: str,
        voyager_li_at: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_csrf_token: str | None = None,
    ) -> StubClient:
        captured["access_token"] = access_token
        captured["api_version"] = api_version
        captured["voyager_li_at"] = voyager_li_at
        captured["voyager_jsessionid"] = voyager_jsessionid
        captured["voyager_csrf_token"] = voyager_csrf_token
        return StubClient()

    exit_code = main(
        [
            "profile",
            "employment-history",
            "--public-id",
            "brenorb",
            "--li-at",
            "test-li-at",
            "--jsessionid",
            '"ajax:123"',
            "--browser",
            "chrome",
        ],
        env={"LINKEDIN_ACCESS_TOKEN": "env-token"},
        client_factory=client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured == {
        "access_token": "env-token",
        "api_version": "202606",
        "voyager_li_at": "test-li-at",
        "voyager_jsessionid": '"ajax:123"',
        "voyager_csrf_token": None,
        "official_called": True,
        "voyager_called": "brenorb",
    }
    assert '"Factored"' in stdout


def test_cli_profile_voyager_session_exports_env(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Session:
        browser = "chrome"
        li_at = "browser-li-at"
        jsessionid = '"ajax:browser"'
        csrf_token = "ajax:browser"

    monkeypatch.setattr("linkedin_cli.cli.load_voyager_session_from_browser", lambda **_: Session())

    exit_code = main(
        [
            "profile",
            "voyager-session",
            "--public-id",
            "brenorb",
        ],
        env={},
        client_factory=_unused_client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "LINKEDIN_VOYAGER_LI_AT" in stdout
    assert "LINKEDIN_VOYAGER_JSESSIONID" in stdout
    assert "LINKEDIN_VOYAGER_CSRF_TOKEN" in stdout
    assert "LINKEDIN_PROFILE_PUBLIC_ID=brenorb" in stdout


def test_cli_profile_voyager_session_outputs_json(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Session:
        browser = "chrome"
        li_at = "browser-li-at"
        jsessionid = '"ajax:browser"'
        csrf_token = "ajax:browser"

    monkeypatch.setattr("linkedin_cli.cli.load_voyager_session_from_browser", lambda **_: Session())

    exit_code = main(
        [
            "profile",
            "voyager-session",
            "--public-id",
            "brenorb",
            "--format",
            "json",
        ],
        env={},
        client_factory=_unused_client_factory,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert '"browser": "chrome"' in stdout
    assert '"li_at": "browser-li-at"' in stdout
    assert '"csrf_token": "ajax:browser"' in stdout
    assert '"public_id": "brenorb"' in stdout


def test_cli_post_rejects_document_title_without_document(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", "--document-title", "June deck", "Ship", "it"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "document title requires a document" in stderr.lower()


def test_cli_post_rejects_article_fields_without_article_url(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    thumbnail_path = tmp_path / "thumb.png"
    thumbnail_path.write_bytes(b"fakepng")

    exit_code = main(
        [
            "post",
            "--article-title",
            "Deep systems",
            "--article-description",
            "A long read",
            "--article-thumbnail",
            str(thumbnail_path),
            "Ship",
            "it",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "article fields require an article url" in stderr.lower()


def test_cli_post_rejects_video_metadata_without_video(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captions_path = tmp_path / "clip.vtt"
    thumbnail_path = tmp_path / "thumb.png"
    captions_path.write_text("WEBVTT", encoding="utf-8")
    thumbnail_path.write_bytes(b"fakepng")

    exit_code = main(
        [
            "post",
            "--video-title",
            "Linus on abstraction",
            "--video-captions",
            str(captions_path),
            "--video-thumbnail",
            str(thumbnail_path),
            "Ship",
            "it",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "video metadata requires a video" in stderr.lower()


def test_cli_post_rejects_upload_only_video_extras_with_video_urn(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captions_path = tmp_path / "clip.vtt"
    thumbnail_path = tmp_path / "thumb.png"
    captions_path.write_text("WEBVTT", encoding="utf-8")
    thumbnail_path.write_bytes(b"fakepng")

    exit_code = main(
        [
            "post",
            "--video-urn",
            "urn:li:video:123",
            "--video-captions",
            str(captions_path),
            "--video-thumbnail",
            str(thumbnail_path),
            "Ship",
            "it",
        ],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "video captions and thumbnail require a local video upload" in stderr.lower()


def test_cli_post_rejects_poll_duration_without_poll_question(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["post", "--poll-duration", "THREE_DAYS", "Ship", "it"],
        env={
            "LINKEDIN_ACCESS_TOKEN": "env-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:person:env123",
        },
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "poll duration requires a poll question" in stderr.lower()


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


def test_cli_profile_employment_history_voyager_private_requires_session_configuration(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "profile",
            "employment-history",
            "--source",
            "voyager-private",
        ],
        env={},
        client_factory=_unused_client_factory,
    )

    stderr = capsys.readouterr().err
    assert exit_code == 2
    assert "voyager li_at session cookie" in stderr.lower()
    assert "voyager csrf token or jsessionid" in stderr.lower()
    assert "public profile identifier" in stderr.lower()


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
