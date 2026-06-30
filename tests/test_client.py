import json
from pathlib import Path

import httpx
import pytest

from linkedin_cli.client import LinkedInApiError, LinkedInClient


def test_client_defaults_to_current_linkedin_api_version() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Linkedin-Version"] == "202606"
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:987"},
            json={"id": "urn:li:share:987"},
        )

    client = LinkedInClient(
        access_token="test-token",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_text_post(
        author="urn:li:person:abc123",
        commentary="Hello from tests",
    )

    assert result.post_id == "urn:li:share:987"


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


def test_get_post_uses_rest_posts_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987?viewContext=AUTHOR"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(
            200,
            json={
                "id": "urn:li:share:987",
                "author": "urn:li:person:abc123",
                "commentary": "Hello from tests",
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_post("urn:li:share:987", view_context="AUTHOR")

    assert result["id"] == "urn:li:share:987"
    assert result["commentary"] == "Hello from tests"


def test_list_posts_uses_author_finder() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/posts"
            "?author=urn%3Ali%3Aperson%3Aabc123&q=author&count=25&start=5&sortBy=CREATED&viewContext=AUTHOR"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "FINDER"
        return httpx.Response(
            200,
            json={
                "paging": {"start": 5, "count": 25, "links": []},
                "elements": [
                    {
                        "id": "urn:li:share:987",
                        "author": "urn:li:person:abc123",
                        "commentary": "Newest first",
                    }
                ],
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.list_posts(
        author="urn:li:person:abc123",
        count=25,
        start=5,
        sort_by="CREATED",
        view_context="AUTHOR",
    )

    assert result["paging"]["start"] == 5
    assert result["elements"][0]["id"] == "urn:li:share:987"


def test_batch_get_posts_uses_rest_posts_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/posts"
            "?ids=List(urn%3Ali%3Ashare%3A123,urn%3Ali%3Ashare%3A456)&viewContext=AUTHOR"
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:share:123": {"id": "urn:li:share:123"},
                    "urn:li:share:456": {"id": "urn:li:share:456"},
                },
                "statuses": {},
                "errors": {},
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_posts(
        ["urn:li:share:123", "urn:li:share:456"],
        view_context="AUTHOR",
    )

    assert result["results"]["urn:li:share:123"]["id"] == "urn:li:share:123"
    assert result["results"]["urn:li:share:456"]["id"] == "urn:li:share:456"


def test_delete_post_uses_rest_posts_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "DELETE"
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.delete_post("urn:li:share:987")


def test_update_post_uses_restli_partial_update() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts/urn%3Ali%3Ashare%3A987")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        assert request.headers["X-RestLi-Method"] == "PARTIAL_UPDATE"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "patch": {
                "$set": {
                    "commentary": "Edited text",
                    "contentCallToActionLabel": "LEARN_MORE",
                    "contentLandingPage": "https://example.com",
                }
            }
        }
        return httpx.Response(204)

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    client.update_post(
        "urn:li:share:987",
        commentary="Edited text",
        content_call_to_action_label="LEARN_MORE",
        content_landing_page="https://example.com",
    )


def test_get_image_uses_rest_images_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/images/urn%3Ali%3Aimage%3A123")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(200, json={"id": "urn:li:image:123", "status": "AVAILABLE"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_image("urn:li:image:123")

    assert result["id"] == "urn:li:image:123"


def test_batch_get_images_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/images"
            "?ids=List(urn%3Ali%3Aimage%3A123,urn%3Ali%3Aimage%3A456)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:image:123": {"id": "urn:li:image:123"},
                    "urn:li:image:456": {"id": "urn:li:image:456"},
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_images(["urn:li:image:123", "urn:li:image:456"])

    assert result["results"]["urn:li:image:456"]["id"] == "urn:li:image:456"


def test_get_video_uses_rest_videos_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A123")
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Linkedin-Version"] == "202505"
        return httpx.Response(200, json={"id": "urn:li:video:123", "status": "AVAILABLE"})

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_video("urn:li:video:123")

    assert result["id"] == "urn:li:video:123"


def test_batch_get_videos_uses_restli_batch_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(
            "https://api.linkedin.com/rest/videos"
            "?ids=List(urn%3Ali%3Avideo%3A123,urn%3Ali%3Avideo%3A456)"
        )
        assert request.headers["X-RestLi-Method"] == "BATCH_GET"
        return httpx.Response(
            200,
            json={
                "results": {
                    "urn:li:video:123": {"id": "urn:li:video:123"},
                    "urn:li:video:456": {"id": "urn:li:video:456"},
                }
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.batch_get_videos(["urn:li:video:123", "urn:li:video:456"])

    assert result["results"]["urn:li:video:123"]["id"] == "urn:li:video:123"


def test_create_image_post_from_existing_asset_uses_media_urn() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello with reused image",
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

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_image_post_from_asset(
        author="urn:li:person:abc123",
        commentary="Hello with reused image",
        image_urn="urn:li:image:123",
        alt_text="Bitdevs banner",
    )

    assert result.post_id == "urn:li:share:456"


def test_create_video_post_from_existing_asset_uses_media_urn() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://api.linkedin.com/rest/posts")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "author": "urn:li:person:abc123",
            "commentary": "Hello with reused video",
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

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.create_video_post_from_asset(
        author="urn:li:person:abc123",
        commentary="Hello with reused video",
        video_urn="urn:li:video:123",
        title="Linus clip",
    )

    assert result.post_id == "urn:li:share:654"


def test_get_userinfo_uses_linkedin_oidc_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL("https://api.linkedin.com/v2/userinfo")
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={
                "sub": "abc123",
                "name": "Breno Brito",
                "email": "breno@example.com",
            },
        )

    client = LinkedInClient(
        access_token="test-token",
        api_version="202505",
        transport=httpx.MockTransport(handler),
    )

    result = client.get_userinfo()

    assert result["sub"] == "abc123"


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
            assert request.headers["Content-Type"] == "image/png"
            assert request.extensions["timeout"]["write"] == 300.0
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
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.extensions["timeout"]["write"] == 300.0
            assert request.content == b"abcd"
            return httpx.Response(200, headers={"ETag": '/ambry-videoei/signedId/part-1.bin'})

        if request.url == httpx.URL("https://www.linkedin.com/dms-uploads/example/uploaded-video/1"):
            assert request.method == "PUT"
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.extensions["timeout"]["write"] == 300.0
            assert request.content == b"efgh"
            return httpx.Response(200, headers={"ETag": '/ambry-videoei/signedId/part-2.bin'})

        if request.url == httpx.URL("https://api.linkedin.com/rest/videos?action=finalizeUpload"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "finalizeUploadRequest": {
                    "video": "urn:li:video:123",
                    "uploadToken": "upload-token",
                    "uploadedPartIds": [
                        "/ambry-videoei/signedId/part-1.bin",
                        "/ambry-videoei/signedId/part-2.bin",
                    ],
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
