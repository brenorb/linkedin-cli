from __future__ import annotations

import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from linkedin_cli.employment import (
    normalize_current_position,
    normalize_positions_payload,
    normalize_voyager_profile_payload,
)

DEFAULT_API_VERSION = "202606"
DEFAULT_IDENTITY_API_VERSION = "202510.03"
MIN_MULTI_IMAGE_COUNT = 2
MAX_MULTI_IMAGE_COUNT = 20


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
        identity_api_version: str | None = None,
        base_url: str = "https://api.linkedin.com",
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
        media_upload_timeout: float = 300.0,
        video_wait_timeout: float = 300.0,
        video_wait_interval: float = 2.0,
        voyager_li_at: str | None = None,
        voyager_csrf_token: str | None = None,
        voyager_jsessionid: str | None = None,
        voyager_base_url: str = "https://www.linkedin.com",
    ) -> None:
        self._identity_api_version = identity_api_version
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
        voyager_headers = {
            "Accept": "application/vnd.linkedin.normalized+json+2.1, application/json",
            "csrf-token": _voyager_csrf_token(voyager_csrf_token, voyager_jsessionid),
        }
        voyager_cookies: dict[str, str] = {}
        if voyager_li_at is not None:
            voyager_cookies["li_at"] = voyager_li_at
        if voyager_jsessionid is not None:
            voyager_cookies["JSESSIONID"] = voyager_jsessionid
        self._voyager_client = (
            httpx.Client(
                base_url=voyager_base_url,
                transport=transport,
                timeout=timeout,
                headers={key: value for key, value in voyager_headers.items() if value is not None},
                cookies=voyager_cookies,
            )
            if voyager_cookies
            else None
        )
        self._media_upload_timeout = media_upload_timeout
        self._video_wait_timeout = video_wait_timeout
        self._video_wait_interval = video_wait_interval

    def close(self) -> None:
        self._client.close()
        self._upload_client.close()
        if self._voyager_client is not None:
            self._voyager_client.close()

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

    def create_reshare_post(
        self,
        *,
        author: str,
        commentary: str,
        reshared_post_urn: str,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        payload = _post_payload(
            author=author,
            commentary=commentary,
            visibility=visibility,
            reshare_context={"parent": reshared_post_urn},
        )

        response = self._client.post("/rest/posts", json=payload)
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        post_id = response.headers.get("x-restli-id") or body.get("id")
        return PostCreationResult(post_id=post_id, response=body)

    def create_poll_post(
        self,
        *,
        author: str,
        commentary: str,
        question: str,
        options: list[str],
        duration: str,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        payload = _post_payload(
            author=author,
            commentary=commentary,
            visibility=visibility,
            content={
                "poll": {
                    "question": question,
                    "options": [{"text": option} for option in options],
                    "settings": {"duration": duration},
                }
            },
        )

        response = self._client.post("/rest/posts", json=payload)
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        post_id = response.headers.get("x-restli-id") or body.get("id")
        return PostCreationResult(post_id=post_id, response=body)

    def get_post(self, post_urn: str, *, view_context: str | None = None) -> dict[str, Any]:
        encoded_post_urn = quote(post_urn, safe="")
        params: list[tuple[str, str | int | float | None]] | None = None
        if view_context:
            params = [("viewContext", view_context)]

        response = self._client.get(f"/rest/posts/{encoded_post_urn}", params=params)
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def list_posts(
        self,
        *,
        author: str,
        count: int = 10,
        start: int = 0,
        sort_by: str = "LAST_MODIFIED",
        view_context: str | None = None,
    ) -> dict[str, Any]:
        params: list[tuple[str, str | int | float | None]] = [
            ("author", author),
            ("q", "author"),
            ("count", count),
            ("start", start),
            ("sortBy", sort_by),
        ]
        if view_context:
            params.append(("viewContext", view_context))

        response = self._client.get(
            "/rest/posts",
            params=params,
            headers={"X-RestLi-Method": "FINDER"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_posts(
        self,
        post_urns: list[str],
        *,
        view_context: str | None = None,
    ) -> dict[str, Any]:
        encoded_post_urns = ",".join(quote(post_urn, safe="") for post_urn in post_urns)
        path = f"/rest/posts?ids=List({encoded_post_urns})"
        if view_context:
            path = f"{path}&viewContext={view_context}"

        response = self._client.get(
            path,
            headers={"X-RestLi-Method": "BATCH_GET"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def get_image(self, image_urn: str) -> dict[str, Any]:
        encoded_image_urn = quote(image_urn, safe="")
        response = self._client.get(f"/rest/images/{encoded_image_urn}")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_images(self, image_urns: list[str]) -> dict[str, Any]:
        return self._batch_get_restli_entities("/rest/images", image_urns)

    def get_document(self, document_urn: str) -> dict[str, Any]:
        encoded_document_urn = quote(document_urn, safe="")
        response = self._client.get(f"/rest/documents/{encoded_document_urn}")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_documents(self, document_urns: list[str]) -> dict[str, Any]:
        return self._batch_get_restli_entities("/rest/documents", document_urns)

    def get_video(self, video_urn: str) -> dict[str, Any]:
        encoded_video_urn = quote(video_urn, safe="")
        response = self._client.get(f"/rest/videos/{encoded_video_urn}")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_videos(self, video_urns: list[str]) -> dict[str, Any]:
        return self._batch_get_restli_entities("/rest/videos", video_urns)

    def list_organization_access(
        self,
        *,
        count: int = 100,
        start: int = 0,
        role: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        params: list[tuple[str, str | int | float | None]] = [
            ("q", "roleAssignee"),
            ("count", count),
            ("start", start),
        ]
        if role:
            params.append(("role", role))
        if state:
            params.append(("state", state))

        response = self._client.get(
            "/rest/organizationAcls",
            params=params,
            headers={"X-RestLi-Method": "FINDER"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def list_organization_access_by_organization(
        self,
        *,
        organization: str,
        count: int = 100,
        start: int = 0,
        role: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        params: list[tuple[str, str | int | float | None]] = [
            ("q", "organization"),
            ("organization", organization),
            ("count", count),
            ("start", start),
        ]
        if role:
            params.append(("role", role))
        if state:
            params.append(("state", state))

        response = self._client.get(
            "/rest/organizationAcls",
            params=params,
            headers={"X-RestLi-Method": "FINDER"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def preflight_organization_author(
        self,
        *,
        role_assignee: str,
        organization: str,
    ) -> dict[str, Any]:
        elements: list[dict[str, Any]] = []
        start = 0
        count = 100
        while True:
            result = self.list_organization_access(
                count=count,
                start=start,
            )
            page_elements = result.get("elements")
            if not isinstance(page_elements, list):
                page_elements = []
            typed_page_elements = [
                element for element in page_elements if isinstance(element, dict)
            ]
            elements.extend(typed_page_elements)
            if len(page_elements) < count:
                break
            start += count

        matching = [
            element
            for element in elements
            if element.get("organization") == organization
            or element.get("organizationTarget") == organization
        ]
        roles = sorted(
            {
                role
                for element in matching
                for role in [element.get("role")]
                if isinstance(role, str) and role
            }
        )
        states = sorted(
            {
                state
                for element in matching
                for state in [element.get("state")]
                if isinstance(state, str) and state
            }
        )
        approved_roles = sorted(
            role
            for element in matching
            for role in [element.get("role")]
            if element.get("state") == "APPROVED" and isinstance(role, str)
        )
        can_create_organic_posts = self._organization_content_action_is_approved(
            impersonator=role_assignee,
            organization=organization,
            action_type="ORGANIC_SHARE_CREATE",
        )
        can_read_organization_posts = self._organization_content_action_is_approved(
            impersonator=role_assignee,
            organization=organization,
            action_type="ORGANIC_SHARE_VIEW_AS_AUTHOR",
        )
        can_edit_organic_posts = self._organization_content_action_is_approved(
            impersonator=role_assignee,
            organization=organization,
            action_type="ORGANIC_SHARE_EDIT",
        )
        can_delete_organic_posts = self._organization_content_action_is_approved(
            impersonator=role_assignee,
            organization=organization,
            action_type="ORGANIC_SHARE_DELETE",
        )

        return {
            "organization": organization,
            "roleAssignee": role_assignee,
            "aclApprovedRoles": approved_roles,
            "roles": roles,
            "states": states,
            "canCreateOrganicPosts": can_create_organic_posts,
            "canReadOrganizationPosts": can_read_organization_posts,
            "canEditOrganicPosts": can_edit_organic_posts,
            "canDeleteOrganicPosts": can_delete_organic_posts,
        }

    def _organization_content_action_is_approved(
        self,
        *,
        impersonator: str,
        organization: str,
        action_type: str,
    ) -> bool:
        response = self._client.get(
            f"/rest/organizationAuthorizations/"
            f"{_organization_content_authorization_key(impersonator=impersonator, organization=organization, action_type=action_type)}"
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        status = body.get("status")
        return isinstance(status, dict) and "com.linkedin.organization.Approved" in status

    def create_comment(
        self,
        *,
        target_urn: str,
        actor: str,
        text: str,
        parent_comment: str | None = None,
        attributes: list[dict[str, object]] | None = None,
        content_image_urn: str | None = None,
    ) -> dict[str, Any]:
        if parent_comment is not None and content_image_urn is not None:
            raise ValueError("Replies do not support content entities on the official Comments API")

        social_action_target = parent_comment or target_urn
        encoded_target_urn = quote(social_action_target, safe="")
        message: dict[str, Any] = {"text": text}
        if attributes is not None:
            message["attributes"] = attributes

        payload: dict[str, Any] = {
            "actor": actor,
            "object": target_urn,
            "message": message,
        }
        if parent_comment is not None:
            payload["parentComment"] = parent_comment
        if content_image_urn is not None:
            payload["content"] = [{"entity": {"image": content_image_urn}}]

        response = self._client.post(
            f"/rest/socialActions/{encoded_target_urn}/comments",
            json=payload,
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def get_comment(self, target_urn: str, comment_id: str) -> dict[str, Any]:
        encoded_target_urn = quote(target_urn, safe="")
        encoded_comment_id = quote(comment_id, safe="")
        response = self._client.get(
            f"/rest/socialActions/{encoded_target_urn}/comments/{encoded_comment_id}"
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def list_comments(
        self,
        *,
        target_urn: str,
        count: int = 10,
        start: int = 0,
    ) -> dict[str, Any]:
        encoded_target_urn = quote(target_urn, safe="")
        response = self._client.get(
            f"/rest/socialActions/{encoded_target_urn}/comments",
            params=[("count", count), ("start", start)],
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_comments(self, target_urn: str, comment_ids: list[str]) -> dict[str, Any]:
        encoded_target_urn = quote(target_urn, safe="")
        encoded_comment_ids = ",".join(quote(comment_id, safe="") for comment_id in comment_ids)
        response = self._client.get(
            f"/rest/socialActions/{encoded_target_urn}/comments?ids=List({encoded_comment_ids})",
            headers={"X-RestLi-Method": "BATCH_GET"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def update_comment(
        self,
        *,
        target_urn: str,
        comment_id: str,
        text: str,
        actor: str | None = None,
        attributes: list[dict[str, object]] | None = None,
    ) -> None:
        _validate_social_action_thread_target(target_urn, operation="Comment updates")
        encoded_target_urn = quote(target_urn, safe="")
        encoded_comment_id = quote(comment_id, safe="")
        message_patch: dict[str, Any] = {"text": text}
        if attributes is not None:
            message_patch["attributes"] = attributes
        response = self._client.post(
            f"/rest/socialActions/{encoded_target_urn}/comments/{encoded_comment_id}",
            params={"actor": actor} if actor is not None else None,
            headers={"X-RestLi-Method": "PARTIAL_UPDATE"},
            json={"patch": {"message": {"$set": message_patch}}},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def delete_comment(
        self,
        *,
        target_urn: str,
        comment_id: str,
        actor: str | None = None,
    ) -> None:
        _validate_social_action_thread_target(target_urn, operation="Comment deletes")
        encoded_target_urn = quote(target_urn, safe="")
        encoded_comment_id = quote(comment_id, safe="")
        response = self._client.delete(
            f"/rest/socialActions/{encoded_target_urn}/comments/{encoded_comment_id}",
            params={"actor": actor} if actor is not None else None,
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def create_reaction(
        self,
        *,
        actor: str,
        root: str,
        reaction_type: str,
    ) -> dict[str, Any]:
        response = self._client.post(
            "/rest/reactions",
            params={"actor": actor},
            json={"root": root, "reactionType": reaction_type},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def get_reaction(self, *, actor: str, entity: str) -> dict[str, Any]:
        response = self._client.get(f"/rest/reactions/{_encoded_reaction_key(actor=actor, entity=entity)}")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_reactions(self, keys: list[tuple[str, str]]) -> dict[str, Any]:
        encoded_keys = ",".join(
            _reaction_key(actor=actor, entity=entity, encode=True)
            for actor, entity in keys
        )
        response = self._client.get(
            f"/rest/reactions?ids=List({encoded_keys})",
            headers={"X-RestLi-Method": "BATCH_GET"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def list_reactions(
        self,
        *,
        entity: str,
        count: int = 10,
        start: int = 0,
        sort: str = "REVERSE_CHRONOLOGICAL",
    ) -> dict[str, Any]:
        response = self._client.get(
            f"/rest/reactions/{_encoded_entity_key(entity)}?q=entity&sort=(value:{sort})&count={count}&start={start}",
            headers={"X-RestLi-Method": "FINDER"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def delete_reaction(self, *, actor: str, entity: str) -> None:
        response = self._client.delete(f"/rest/reactions/{_encoded_reaction_key(actor=actor, entity=entity)}")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def get_social_metadata(self, entity_urn: str) -> dict[str, Any]:
        encoded_entity_urn = quote(entity_urn, safe="")
        response = self._client.get(f"/rest/socialMetadata/{encoded_entity_urn}")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def batch_get_social_metadata(self, entity_urns: list[str]) -> dict[str, Any]:
        return self._batch_get_restli_entities("/rest/socialMetadata", entity_urns)

    def update_social_metadata_comments_state(
        self,
        *,
        entity_urn: str,
        actor: str,
        comments_state: str,
    ) -> None:
        _validate_social_metadata_thread_target(entity_urn)
        encoded_entity_urn = quote(entity_urn, safe="")
        response = self._client.post(
            f"/rest/socialMetadata/{encoded_entity_urn}",
            params={"actor": actor},
            headers={"X-RestLi-Method": "PARTIAL_UPDATE"},
            json={"patch": {"$set": {"commentsState": comments_state}}},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def delete_post(self, post_urn: str) -> None:
        encoded_post_urn = quote(post_urn, safe="")
        response = self._client.delete(
            f"/rest/posts/{encoded_post_urn}",
            headers={"X-RestLi-Method": "DELETE"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def update_post(
        self,
        post_urn: str,
        *,
        commentary: str | None = None,
        content_call_to_action_label: str | None = None,
        content_landing_page: str | None = None,
        lifecycle_state: str | None = None,
    ) -> None:
        encoded_post_urn = quote(post_urn, safe="")
        patch_set: dict[str, str] = {}
        if commentary is not None:
            patch_set["commentary"] = commentary
        if content_call_to_action_label is not None:
            patch_set["contentCallToActionLabel"] = content_call_to_action_label
        if content_landing_page is not None:
            patch_set["contentLandingPage"] = content_landing_page
        if lifecycle_state is not None:
            patch_set["lifecycleState"] = lifecycle_state

        response = self._client.post(
            f"/rest/posts/{encoded_post_urn}",
            headers={"X-RestLi-Method": "PARTIAL_UPDATE"},
            json={"patch": {"$set": patch_set}},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def get_userinfo(self) -> dict[str, Any]:
        response = self._client.get("/v2/userinfo")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def get_profile_identity(self) -> dict[str, Any]:
        response = self._client.get("/v2/me")
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def get_identity_profile(self) -> dict[str, Any]:
        response = self._client.get(
            "/rest/identityMe",
            headers={"Linkedin-Version": self._required_identity_api_version()},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)

    def get_employment_history(self) -> list[dict[str, object]]:
        response = self._client.get("/v2/me", params={"projection": "(positions)"})
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))
        return normalize_positions_payload(_response_json(response))

    def get_current_employment(self) -> list[dict[str, object]]:
        response = self._client.get(
            "/rest/identityMe",
            headers={"Linkedin-Version": self._required_identity_api_version()},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))
        return normalize_current_position(_response_json(response))

    def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]:
        response = self._required_voyager_client().get(
            f"/voyager/api/identity/profiles/{quote(public_identifier, safe='')}/profileView"
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))
        return normalize_voyager_profile_payload(_response_json(response))

    def _required_identity_api_version(self) -> str:
        if self._identity_api_version is None:
            raise ValueError("identity API version is required for `/rest/identityMe` requests")
        return self._identity_api_version

    def _required_voyager_client(self) -> httpx.Client:
        if self._voyager_client is None:
            raise ValueError("Voyager session cookies are required for `/voyager/api` requests")
        return self._voyager_client

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

    def create_image_post_from_asset(
        self,
        *,
        author: str,
        commentary: str,
        image_urn: str,
        alt_text: str | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        media: dict[str, Any] = {"id": image_urn}
        if alt_text:
            media["altText"] = alt_text

        return self._create_media_post(
            author=author,
            commentary=commentary,
            visibility=visibility,
            media=media,
        )

    def create_document_post(
        self,
        *,
        author: str,
        commentary: str,
        document_path: Path,
        title: str,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        document_urn, upload_url = self._initialize_document_upload(owner=author)
        self._upload_file(upload_url=upload_url, file_path=Path(document_path))
        self._wait_for_asset_availability(
            path_prefix="/rest/documents",
            asset_urn=document_urn,
            label="Document",
        )

        return self._create_media_post(
            author=author,
            commentary=commentary,
            visibility=visibility,
            media={"id": document_urn, "title": title},
        )

    def create_document_post_from_asset(
        self,
        *,
        author: str,
        commentary: str,
        document_urn: str,
        title: str,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        return self._create_media_post(
            author=author,
            commentary=commentary,
            visibility=visibility,
            media={"id": document_urn, "title": title},
        )

    def create_article_post(
        self,
        *,
        author: str,
        commentary: str,
        article_url: str,
        title: str,
        description: str | None = None,
        thumbnail_image_urn: str | None = None,
        thumbnail_image_path: Path | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        article: dict[str, Any] = {
            "source": article_url,
            "title": title,
        }
        if description:
            article["description"] = description
        if thumbnail_image_path is not None:
            thumbnail_image_urn, upload_url = self._initialize_image_upload(owner=author)
            self._upload_image(upload_url=upload_url, image_path=Path(thumbnail_image_path))
        if thumbnail_image_urn:
            article["thumbnail"] = thumbnail_image_urn

        payload = _post_payload(
            author=author,
            commentary=commentary,
            visibility=visibility,
            content={"article": article},
        )
        response = self._client.post("/rest/posts", json=payload)
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        post_id = response.headers.get("x-restli-id") or body.get("id")
        return PostCreationResult(post_id=post_id, response=body)

    def create_multi_image_post(
        self,
        *,
        author: str,
        commentary: str,
        image_paths: list[Path],
        alt_texts: list[str] | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        image_urns: list[str] = []
        for image_path in image_paths:
            image_urn, upload_url = self._initialize_image_upload(owner=author)
            self._upload_image(upload_url=upload_url, image_path=Path(image_path))
            image_urns.append(image_urn)

        return self.create_multi_image_post_from_assets(
            author=author,
            commentary=commentary,
            visibility=visibility,
            image_urns=image_urns,
            alt_texts=alt_texts,
        )

    def create_multi_image_post_from_assets(
        self,
        *,
        author: str,
        commentary: str,
        image_urns: list[str],
        alt_texts: list[str] | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        _validate_multi_image_count(image_urns)
        images = _build_multi_image_images(image_urns=image_urns, alt_texts=alt_texts)

        payload = _post_payload(
            author=author,
            commentary=commentary,
            visibility=visibility,
            content={"multiImage": {"images": images}},
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
        captions_path: Path | None = None,
        thumbnail_path: Path | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        video_urn, upload_token, upload_instructions, captions_upload_url, thumbnail_upload_url = self._initialize_video_upload(
            owner=author,
            video_path=Path(video_path),
            upload_captions=captions_path is not None,
            upload_thumbnail=thumbnail_path is not None,
        )
        uploaded_part_ids = self._upload_video_parts(
            upload_instructions=upload_instructions,
            video_path=Path(video_path),
        )
        if captions_path and captions_upload_url:
            self._upload_file(
                upload_url=captions_upload_url,
                file_path=Path(captions_path),
                content_type="text/vtt",
            )
        if thumbnail_path and thumbnail_upload_url:
            self._upload_file(
                upload_url=thumbnail_upload_url,
                file_path=Path(thumbnail_path),
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

    def create_video_post_from_asset(
        self,
        *,
        author: str,
        commentary: str,
        video_urn: str,
        title: str | None = None,
        visibility: str = "PUBLIC",
    ) -> PostCreationResult:
        media: dict[str, Any] = {"id": video_urn}
        if title:
            media["title"] = title

        return self._create_media_post(
            author=author,
            commentary=commentary,
            visibility=visibility,
            media=media,
        )

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
        self._upload_file(upload_url=upload_url, file_path=image_path)

    def _initialize_document_upload(self, *, owner: str) -> tuple[str, str]:
        response = self._client.post(
            "/rest/documents?action=initializeUpload",
            json={"initializeUploadRequest": {"owner": owner}},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        body = _response_json(response)
        value = body.get("value")
        if not isinstance(value, dict):
            raise LinkedInApiError(response.status_code, "Missing upload initialization payload")

        document_urn = value.get("document")
        upload_url = value.get("uploadUrl")
        if not isinstance(document_urn, str) or not isinstance(upload_url, str):
            raise LinkedInApiError(response.status_code, "Missing document upload metadata")

        return document_urn, upload_url

    def _upload_file(
        self,
        *,
        upload_url: str,
        file_path: Path,
        content_type: str | None = None,
    ) -> None:
        resolved_content_type = content_type or mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        response = self._upload_client.put(
            upload_url,
            content=file_path.read_bytes(),
            headers={"Content-Type": resolved_content_type},
            timeout=self._media_upload_timeout,
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

    def _initialize_video_upload(
        self,
        *,
        owner: str,
        video_path: Path,
        upload_captions: bool = False,
        upload_thumbnail: bool = False,
    ) -> tuple[str, str, list[dict[str, Any]], str | None, str | None]:
        response = self._client.post(
            "/rest/videos?action=initializeUpload",
            json={
                "initializeUploadRequest": {
                    "owner": owner,
                    "fileSizeBytes": video_path.stat().st_size,
                    "uploadCaptions": upload_captions,
                    "uploadThumbnail": upload_thumbnail,
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
        captions_upload_url = value.get("captionsUploadUrl")
        thumbnail_upload_url = value.get("thumbnailUploadUrl")
        if not isinstance(video_urn, str) or not isinstance(upload_token, str):
            raise LinkedInApiError(response.status_code, "Missing video upload metadata")
        if not isinstance(upload_instructions, list) or not upload_instructions:
            raise LinkedInApiError(response.status_code, "Missing video upload instructions")
        if captions_upload_url is not None and not isinstance(captions_upload_url, str):
            raise LinkedInApiError(response.status_code, "Invalid captions upload metadata")
        if thumbnail_upload_url is not None and not isinstance(thumbnail_upload_url, str):
            raise LinkedInApiError(response.status_code, "Invalid thumbnail upload metadata")

        return (
            video_urn,
            upload_token,
            upload_instructions,
            captions_upload_url if isinstance(captions_upload_url, str) else None,
            thumbnail_upload_url if isinstance(thumbnail_upload_url, str) else None,
        )

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
        self._wait_for_asset_availability(
            path_prefix="/rest/videos",
            asset_urn=video_urn,
            label="Video",
            failure_reason_key="processingFailureReason",
        )

    def _wait_for_asset_availability(
        self,
        *,
        path_prefix: str,
        asset_urn: str,
        label: str,
        failure_reason_key: str | None = None,
    ) -> None:
        deadline = time.monotonic() + self._video_wait_timeout
        encoded_asset_urn = quote(asset_urn, safe="")

        while True:
            response = self._client.get(f"{path_prefix}/{encoded_asset_urn}")
            if response.is_error:
                raise LinkedInApiError(response.status_code, _extract_error_message(response))

            body = _response_json(response)
            status = body.get("status")
            if status == "AVAILABLE":
                return
            if status == "PROCESSING_FAILED":
                message = f"{label} processing failed"
                if failure_reason_key:
                    reason = body.get(failure_reason_key)
                    if isinstance(reason, str) and reason:
                        message = f"{message}: {reason}"
                raise LinkedInApiError(response.status_code, message)
            if status not in {"WAITING_UPLOAD", "PROCESSING"}:
                raise LinkedInApiError(response.status_code, f"Unexpected {label.lower()} status: {status!r}")
            if time.monotonic() >= deadline:
                raise LinkedInApiError(response.status_code, f"Timed out waiting for {label.lower()} processing")
            time.sleep(self._video_wait_interval)

    def _create_media_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        media: dict[str, Any],
    ) -> PostCreationResult:
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

    def _batch_get_restli_entities(self, path_prefix: str, urns: list[str]) -> dict[str, Any]:
        encoded_urns = ",".join(quote(urn, safe="") for urn in urns)
        response = self._client.get(
            f"{path_prefix}?ids=List({encoded_urns})",
            headers={"X-RestLi-Method": "BATCH_GET"},
        )
        if response.is_error:
            raise LinkedInApiError(response.status_code, _extract_error_message(response))

        return _response_json(response)


def _post_payload(
    *,
    author: str,
    commentary: str,
    visibility: str,
    content: dict[str, Any] | None = None,
    reshare_context: dict[str, Any] | None = None,
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
    if reshare_context is not None:
        payload["reshareContext"] = reshare_context
    return payload


def _build_multi_image_images(
    *,
    image_urns: list[str],
    alt_texts: list[str] | None = None,
) -> list[dict[str, Any]]:
    _validate_multi_image_count(image_urns)

    if alt_texts is not None and len(alt_texts) != len(image_urns):
        raise ValueError("multi-image alt text count must match the number of image URNs")

    images: list[dict[str, Any]] = []
    for index, image_urn in enumerate(image_urns):
        image: dict[str, Any] = {"id": image_urn}
        if alt_texts is not None:
            image["altText"] = alt_texts[index]
        images.append(image)
    return images


def _validate_multi_image_count(image_urns: list[str]) -> None:
    if not MIN_MULTI_IMAGE_COUNT <= len(image_urns) <= MAX_MULTI_IMAGE_COUNT:
        raise ValueError("multi-image posts require 2 to 20 images")


def _validate_social_action_thread_target(target_urn: str, *, operation: str) -> None:
    if _is_comment_urn(target_urn):
        raise ValueError(f"{operation} require a share or ugcPost URN, not a comment URN")


def _validate_social_metadata_thread_target(entity_urn: str) -> None:
    if _is_comment_urn(entity_urn):
        raise ValueError("Comments-state updates require a thread URN, not a comment URN")


def _is_comment_urn(urn: str) -> bool:
    return urn.startswith("urn:li:comment:")


def _organization_content_authorization_key(
    *,
    impersonator: str,
    organization: str,
    action_type: str,
) -> str:
    return (
        f"(impersonator:{quote(impersonator, safe='')},"
        f"organization:{quote(organization, safe='')},"
        f"action:(organizationContentAuthorizationAction:(actionType:{action_type})))"
    )


def _reaction_key(*, actor: str, entity: str, encode: bool) -> str:
    actor_value = quote(actor, safe="") if encode else actor
    entity_value = quote(entity, safe="") if encode else entity
    return f"(actor:{actor_value},entity:{entity_value})"


def _encoded_reaction_key(*, actor: str, entity: str) -> str:
    return _reaction_key(actor=actor, entity=entity, encode=True)


def _encoded_entity_key(entity: str) -> str:
    return f"(entity:{quote(entity, safe='')})"


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


def _voyager_csrf_token(csrf_token: str | None, jsessionid: str | None) -> str | None:
    if csrf_token is not None:
        return csrf_token.strip('"')
    if jsessionid is not None:
        return jsessionid.strip('"')
    return None


def _normalize_etag(value: str) -> str:
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value
