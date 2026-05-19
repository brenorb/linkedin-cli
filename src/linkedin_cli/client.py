from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_API_VERSION = "202505"


class LinkedInApiError(RuntimeError):
    """Raised when the LinkedIn API returns a non-success response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"LinkedIn API request failed with status {status_code}: {message}")
        self.status_code = status_code
        self.message = message


@dataclass(slots=True)
class PostCreationResult:
    post_id: str | None
    response: dict[str, Any]


class LinkedInClient:
    def __init__(
        self,
        *,
        access_token: str,
        api_version: str = DEFAULT_API_VERSION,
        base_url: str = "https://api.linkedin.com",
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            transport=transport,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Linkedin-Version": api_version,
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

    def close(self) -> None:
        self._client.close()

    def create_text_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        payload = {
            "author": author,
            "commentary": commentary,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        response = self._client.post("/rest/posts", json=payload)
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        post_id = response.headers.get("x-restli-id") or body.get("id")
        return PostCreationResult(post_id=post_id, response=body)


def _response_json(response: httpx.Response) -> dict[str, Any]:
    if not response.content:
        return {}

    data = response.json()
    if isinstance(data, dict):
        return data
    return {"data": data}


def _extract_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text or "Unknown error"

    if isinstance(data, dict):
        for key in ("message", "error_description", "error"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value

    return response.text or "Unknown error"
