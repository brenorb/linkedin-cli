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


def test_create_video_post_initializes_upload_uploads_parts_finalizes_and_creates_post(
    tmp_path: Path,
) -> None:
    video_path = tmp_path / "clip.mp4"
    video_bytes = b"abcdefgh"
    video_path.write_bytes(video_bytes)
    requests: list[httpx.Request] = []
    status_polls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal status_polls
        requests.append(request)

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=initializeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:abc123",
                    "fileSizeBytes": 8,
                    "uploadCaptions": False,
                    "uploadThumbnail": False,
                }
            }
            return httpx.Response(
                200,
                json={
                    "value": {
                        "video": "urn:li:video:123",
                        "uploadToken": "upload-token",
                        "uploadInstructions": [
                            {
                                "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/0",
                                "firstByte": 0,
                                "lastByte": 3,
                            },
                            {
                                "uploadUrl": "https://www.linkedin.com/dms-uploads/example/uploaded-video/1",
                                "firstByte": 4,
                                "lastByte": 7,
                            },
                        ],
                    }
                },
            )

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/0"):
            assert request.method == "PUT"
            assert request.headers["Authorization"] == "Bearer test-token"
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.content == b"abcd"
            return httpx.Response(201, headers={"ETag": '"etag-1"'})

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/1"):
            assert request.method == "PUT"
            assert request.headers["Authorization"] == "Bearer test-token"
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.content == b"efgh"
            return httpx.Response(201, headers={"ETag": '"etag-2"'})

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=finalizeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "finalizeUploadRequest": {
                    "video": "urn:li:video:123",
                    "uploadToken": "upload-token",
                    "uploadedPartIds": ["etag-1", "etag-2"],
                }
            }
            return httpx.Response(200, json={})

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"):
            status_polls += 1
            if status_polls == 1:
                return httpx.Response(200, json={"id": "urn:li:video:123", "status": "PROCESSING"})
            return httpx.Response(200, json={"id": "urn:li:video:123", "status": "AVAILABLE"})

        if request.url == httpx.URL("https://api.linkedin.com/rest/posts"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "author": "urn:li:person:abc123",
                "commentary": "Hello with video",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {
                    "media": {
                        "id": "urn:li:video:123",
                        "title": "Linus clip",
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            return httpx.Response(
                201,
                headers={"x-restli-id": "urn:li:share:654"},
                json={"id": "urn:li:share:654"},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
        video_wait_interval=0.0,
    )

    result = client.create_video_post(
        author="urn:li:person:abc123",
        commentary="Hello with video",
        video_path=video_path,
        title="Linus clip",
    )

    assert result.post_id == "urn:li:share:654"
    assert result.response["id"] == "urn:li:share:654"
    assert [request.url for request in requests] == [
        httpx.URL("https://api.linkedin.com/rest/videos?action=initializeUpload"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/0"),
        httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/1"),
        httpx.URL("https://api.linkedin.com/rest/videos?action=finalizeUpload"),
        httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"),
        httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123"),
        httpx.URL("https://api.linkedin.com/rest/posts"),
    ]


def test_get_employment_history_uses_profile_api_projection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v2/me"
        assert request.url.params["projection"] == "(positions)"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["X-Restli-Protocol-Version"] == "2.0.0"
        return httpx.Response(
            200,
            json={
                "positions": {
                    "elements": [
                        {
                            "companyName": {
                                "localized": {
                                    "en_US": "FACTORED",
                                },
                                "preferredLocale": {
                                    "country": "US",
                                    "language": "en",
                                },
                            },
                            "title": {
                                "localized": {
                                    "en_US": "AI Engineer",
                                },
                                "preferredLocale": {
                                    "country": "US",
                                    "language": "en",
                                },
                            },
                            "startMonthYear": {
                                "month": 1,
                                "year": 2024,
                            },
                        }
                    ]
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_employment_history()

    assert result == [
        {
            "employer_name": "FACTORED",
            "job_title": "AI Engineer",
            "start_date": "2024-01",
            "end_date": None,
            "is_current": True,
        }
    ]


def test_get_current_employment_uses_identity_me() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/identityMe")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202510.03"
        return httpx.Response(
            200,
            json={
                "primaryCurrentPosition": {
                    "title": {
                        "localized": {
                            "en_US": "Senior Software Engineer",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "companyName": {
                        "localized": {
                            "en_US": "LinkedIn",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "startedOn": {
                        "month": 1,
                        "year": 2022,
                    },
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202510.03",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_current_employment()

    assert result == [
        {
            "employer_name": "LinkedIn",
            "job_title": "Senior Software Engineer",
            "start_date": "2022-01",
            "end_date": None,
            "is_current": True,
        }
    ]
