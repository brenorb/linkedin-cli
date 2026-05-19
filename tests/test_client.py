import json
from pathlib import Path

import httpx
import pytest

from linkedin_cli.client import LinkedInApiError, LinkedInClient


def test_create_text_post_uses_rest_posts_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-Restli-Protocol-Version"] == "2.0.0"

        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello from tests",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:987"},
            json={"id": "urn:li:share:987"},
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_text_post(
        author="urn:li:person:abc123",
        commentary="Hello from tests",
    )

    assert result.post_id == "urn:li:share:987"
    assert result.response["id"] == "urn:li:share:987"


def test_create_text_post_raises_clear_error_on_api_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid access token"})

    client = LinkedInClient(
        access_token="bad-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LinkedInApiError, match="401"):
        client.create_text_post(
            author="urn:li:person:abc123",
            commentary="Hello from tests",
        )


def test_create_image_post_initializes_upload_uploads_binary_and_creates_post(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "banner.png"
    image_bytes = b"\x89PNG\r\n\x1a\nfakepng"
    image_path.write_bytes(image_bytes)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:abc123",
                }
            }
            return httpx.Response(
                200,
                json={
                    "value": {
                        "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-image/0",
                        "image": "urn:li:image:123",
                    }
                },
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"):
            assert request.method == "PUT"
            assert request.headers["Authorization"] == "Bearer test-token"
            assert request.headers["Content-Type"] == "image/png"
            assert request.content == image_bytes
            return httpx.Response(201)

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "author": "urn:li:person:abc123",
                "commentary": "Hello with image",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": "urn:li:image:123",
                        "altText": "Bitdevs banner",
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:456"},
                json={"id": "urn:li:share:456"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_image_post(
        author="urn:li:person:abc123",
        commentary="Hello with image",
        image_path=image_path,
        alt_text="Bitdevs banner",
    )

    assert result.post_id == "urn:li:share:456"
    assert result.response["id"] == "urn:li:share:456"
    assert [request.url for request in requests] == [
        httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-image/0"),
        httpx.URL("https://api.linkedin.com/rest/posts"),
    ]


def test_create_image_post_raises_clear_error_when_upload_init_fails(tmp_path: Path) -> None:
    image_path = tmp_path / "banner.png"
    image_path.write_bytes(b"fakepng")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://api.linkedin.com/rest/images?action=initializeUpload"):
            return httpx.Response(403, json={"message": "Not enough permissions"})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LinkedInApiError, match="403"):
        client.create_image_post(
            author="urn:li:person:abc123",
            commentary="Hello with image",
            image_path=image_path,
        )
