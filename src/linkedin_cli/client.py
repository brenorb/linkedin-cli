from __future__ import annotations

import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from linkedin_cli.employment import normalize_current_position, normalize_positions_payload

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
        media_upload_timeout: float = 300.0,
        video_wait_timeout: float = 300.0,
        video_wait_interval: float = 2.0,
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
        self._upload_client = httpx.Client(
            transport=transport,
            timeout=timeout,
            follow_redirects=True,
        )
        self._media_upload_timeout = media_upload_timeout
        self._video_wait_timeout = video_wait_timeout
        self._video_wait_interval = video_wait_interval

    def close(self) -> None:
        self._client.close()
        self._upload_client.close()

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

    def get_employment_history(self) -> list[dict[str, object]]:
        response = self._client.get("/v2/me", params={"projection": "(positions)"})
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))
        return normalize_positions_payload(_response_json(response))

    def get_current_employment(self) -> list[dict[str, object]]:
        response = self._client.get("/rest/identityMe")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))
        return normalize_current_position(_response_json(response))

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

    def create_video_post(
        self,
        *,
        author: str,
        commentary: str,
        video_path: Path,
        title: str | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        video_urn, upload_token, upload_instructions = self._initialize_video_upload(
            owner=author,
            video_path=Path(video_path),
        )
        uploaded_part_ids = self._upload_video_parts(
            upload_instructions=upload_instructions,
            video_path=Path(video_path),
        )
        self._finalize_video_upload(
            video_urn=video_urn,
            upload_token=upload_token,
            uploaded_part_ids=uploaded_part_ids,
        )
        self._wait_for_video_availability(video_urn=video_urn)

        media: dict[str, Any] = {"id": video_urn}
        if title:
            media["title"] = title

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
        response = self._upload_client.put(
            upload_url,
            content=image_path.read_bytes(),
            headers={"Content-Type": content_type},
            timeout=self._media_upload_timeout,
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def _initialize_video_upload(
        self,
        *,
        owner: str,
        video_path: Path,
    ) -> tuple[str, str, list[dict[str, Any]]]:
        response = self._client.post(
            "/rest/videos?action=initializeUpload",
            json={
                "initializeUploadRequest": {
                    "owner": owner,
                    "fileSizeBytes": video_path.stat().st_size,
                    "uploadCaptions": False,
                    "uploadThumbnail": False,
                }
            },
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        value = body.get("value")
        if not isinstance(value, dict):
            raise LinkedInApiError(response.status_code, "Missing video upload initialization payload")

        video_urn = value.get("video")
        upload_token = value.get("uploadToken", "")
        upload_instructions = value.get("uploadInstructions")
        if not isinstance(video_urn, str) or not isinstance(upload_token, str):
            raise LinkedInApiError(response.status_code, "Missing video upload metadata")
        if not isinstance(upload_instructions, list) or not upload_instructions:
            raise LinkedInApiError(response.status_code, "Missing video upload instructions")

        return video_urn, upload_token, upload_instructions

    def _upload_video_parts(
        self,
        *,
        upload_instructions: list[dict[str, Any]],
        video_path: Path,
    ) -> list[str]:
        uploaded_part_ids: list[str] = []
        with video_path.open("rb") as video_file:
            for instruction in upload_instructions:
                upload_url = instruction.get("uploadUrl")
                first_byte = instruction.get("firstByte")
                last_byte = instruction.get("lastByte")
                if (
                    not isinstance(upload_url, str)
                    or not isinstance(first_byte, int)
                    or not isinstance(last_byte, int)
                ):
                    raise LinkedInApiError(500, "Invalid video upload instruction payload")

                video_file.seek(first_byte)
                chunk = video_file.read(last_byte - first_byte + 1)
                response = self._upload_client.put(
                    upload_url,
                    content=chunk,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=self._media_upload_timeout,
                )
                if response.is_error:
                    raise LinkedInApiError(response.status_code, _extract_error_message(response))

                etag = response.headers.get("ETag") or response.headers.get("etag")
                if not etag:
                    raise LinkedInApiError(response.status_code, "Missing uploaded video part identifier")
                uploaded_part_ids.append(_normalize_etag(etag))

        return uploaded_part_ids

    def _finalize_video_upload(
        self,
        *,
        video_urn: str,
        upload_token: str,
        uploaded_part_ids: list[str],
    ) -> None:
        response = self._client.post(
            "/rest/videos?action=finalizeUpload",
            json={
                "finalizeUploadRequest": {
                    "video": video_urn,
                    "uploadToken": upload_token,
                    "uploadedPartIds": uploaded_part_ids,
                }
            },
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def _wait_for_video_availability(self, *, video_urn: str) -> None:
        deadline = time.monotonic() + self._video_wait_timeout
        encoded_video_urn = quote(video_urn, safe="")

        while True:
            response = self._client.get(f"/rest/videos/{encoded_video_urn}")
            if response.is_error:
                raise LinkedInApiError(response.status_code, _extract_error_message(response))

            body = _response_json(response)
            status = body.get("status")
            if status == "AVAILABLE":
                return
            if status == "PROCESSING_FAILED":
                reason = body.get("processingFailureReason")
                message = "Video processing failed"
                if isinstance(reason, str) and reason:
                    message = f"{message}: {reason}"
                raise LinkedInApiError(response.status_code, message)
            if status not in {"WAITING_UPLOAD", "PROCESSING"}:
                raise LinkedInApiError(response.status_code, f"Unexpected video status: {status!r}")
            if time.monotonic() >= deadline:
                raise LinkedInApiError(response.status_code, "Timed out waiting for video processing")
            time.sleep(self._video_wait_interval)


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


def _normalize_etag(value: str) -> str:
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value
