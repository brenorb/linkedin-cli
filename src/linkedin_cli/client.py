from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
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

    def create_image_post(
        self,
        *,
        author: str,
        commentary: str,
        image_path: Path,
        alt_text: str | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        image_urn, upload_url = self._initialize_image_upload(owner=author)
        self._upload_image(upload_url=upload_url, image_path=Path(image_path))

        media: dict[str, Any] = {"id": image_urn}
        if alt_text:
            media["altText"] = alt_text

        payload = _post_payload(
            author=author,
            commentary=commentary,
            visibility=visibility,
            content={"media": media},
        )

        response = self._client.post("/rest/posts", json=payload)
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        post_id = response.headers.get("x-restli-id") or body.get("id")
        return PostCreationResult(post_id=post_id, response=body)

    def _initialize_image_upload(self, *, owner: str) -> tuple[str, str]:
        response = self._client.post(
            "/rest/images?action=initializeUpload",
            json={"initializeUploadRequest": {"owner": owner}},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        value = body.get("value")
        if not isinstance(value, dict):
            raise LinkedInApiError(response.status_code, "Missing upload initialization payload")

        image_urn = value.get("image")
        upload_url = value.get("uploadUrl")
        if not isinstance(image_urn, str) or not isinstance(upload_url, str):
            raise LinkedInApiError(response.status_code, "Missing image upload metadata")

        return image_urn, upload_url

    def _upload_image(self, *, upload_url: str, image_path: Path) -> None:
        content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        response = self._client.put(
            upload_url,
            content=image_path.read_bytes(),
            headers={"Content-Type": content_type},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))


def _post_payload(
    *,
    author: str,
    commentary: str,
    visibility: str,
    content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
    if content is not None:
        payload["content"] = content
    return payload

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
