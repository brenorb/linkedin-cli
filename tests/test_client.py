import json

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
