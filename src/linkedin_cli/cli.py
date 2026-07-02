from __future__ import annotations

import argparse
import inspect
import json
import os
import shlex
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, Protocol, cast

from linkedin_cli.browser_profile import load_employment_history_from_chrome_profile
from linkedin_cli.browser_session import SUPPORTED_BROWSERS, load_voyager_session_from_browser
from linkedin_cli.client import (
    DEFAULT_API_VERSION,
    DEFAULT_IDENTITY_API_VERSION,
    MAX_MULTI_IMAGE_COUNT,
    MIN_MULTI_IMAGE_COUNT,
    LinkedInApiError,
    LinkedInClient,
)
from linkedin_cli.employment import filter_employment_history


class LinkedInPostClient(Protocol):
    def create_text_post(self, *, author: str, commentary: str, visibility: str) -> object: ...
    def create_poll_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        question: str,
        options: list[str],
        duration: str,
    ) -> object: ...
    def create_reshare_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        reshared_post_urn: str,
    ) -> object: ...
    def create_image_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        image_path: Path,
        alt_text: str | None = None,
    ) -> object: ...
    def create_image_post_from_asset(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        image_urn: str,
        alt_text: str | None = None,
    ) -> object: ...
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
    ) -> object: ...
    def create_video_post_from_asset(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        video_urn: str,
        title: str | None = None,
    ) -> object: ...
    def create_document_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        document_path: Path,
        title: str,
    ) -> object: ...
    def create_document_post_from_asset(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        document_urn: str,
        title: str,
    ) -> object: ...
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
    ) -> object: ...
    def create_multi_image_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        image_paths: list[Path],
        alt_texts: list[str] | None = None,
    ) -> object: ...
    def create_multi_image_post_from_assets(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        image_urns: list[str],
        alt_texts: list[str] | None = None,
    ) -> object: ...
    def get_post(self, post_urn: str, *, view_context: str | None = None) -> dict[str, Any]: ...
    def list_posts(
        self,
        *,
        author: str,
        count: int,
        start: int,
        sort_by: str,
        view_context: str | None = None,
    ) -> dict[str, Any]: ...
    def batch_get_posts(
        self,
        post_urns: list[str],
        *,
        view_context: str | None = None,
    ) -> dict[str, Any]: ...
    def delete_post(self, post_urn: str) -> None: ...
    def update_post(
        self,
        post_urn: str,
        *,
        commentary: str | None = None,
        content_call_to_action_label: str | None = None,
        content_landing_page: str | None = None,
        lifecycle_state: str | None = None,
    ) -> None: ...
    def get_image(self, image_urn: str) -> dict[str, Any]: ...
    def batch_get_images(self, image_urns: list[str]) -> dict[str, Any]: ...
    def get_document(self, document_urn: str) -> dict[str, Any]: ...
    def batch_get_documents(self, document_urns: list[str]) -> dict[str, Any]: ...
    def get_video(self, video_urn: str) -> dict[str, Any]: ...
    def batch_get_videos(self, video_urns: list[str]) -> dict[str, Any]: ...
    def get_userinfo(self) -> dict[str, Any]: ...
    def get_profile_identity(self) -> dict[str, Any]: ...
    def get_identity_profile(self) -> dict[str, Any]: ...
    def get_employment_history(self) -> list[dict[str, object]]: ...
    def get_current_employment(self) -> list[dict[str, object]]: ...
    def get_voyager_employment_history(self, public_identifier: str) -> list[dict[str, object]]: ...
    def list_organization_access(
        self,
        *,
        count: int,
        start: int,
        role: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]: ...
    def list_organization_access_by_organization(
        self,
        *,
        organization: str,
        count: int,
        start: int,
        role: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]: ...
    def preflight_organization_author(
        self,
        *,
        role_assignee: str,
        organization: str,
    ) -> dict[str, Any]: ...
    def create_comment(
        self,
        *,
        target_urn: str,
        actor: str,
        text: str,
        parent_comment: str | None = None,
        attributes: list[dict[str, object]] | None = None,
        content_image_urn: str | None = None,
    ) -> dict[str, Any]: ...
    def get_comment(self, target_urn: str, comment_id: str) -> dict[str, Any]: ...
    def list_comments(self, *, target_urn: str, count: int, start: int) -> dict[str, Any]: ...
    def batch_get_comments(self, target_urn: str, comment_ids: list[str]) -> dict[str, Any]: ...
    def update_comment(
        self,
        *,
        target_urn: str,
        comment_id: str,
        text: str,
        actor: str | None = None,
        attributes: list[dict[str, object]] | None = None,
    ) -> None: ...
    def delete_comment(
        self,
        *,
        target_urn: str,
        comment_id: str,
        actor: str | None = None,
    ) -> None: ...
    def create_reaction(
        self,
        *,
        actor: str,
        root: str,
        reaction_type: str,
    ) -> dict[str, Any]: ...
    def get_reaction(self, *, actor: str, entity: str) -> dict[str, Any]: ...
    def batch_get_reactions(self, keys: list[tuple[str, str]]) -> dict[str, Any]: ...
    def list_reactions(
        self,
        *,
        entity: str,
        count: int,
        start: int,
        sort: str,
    ) -> dict[str, Any]: ...
    def delete_reaction(self, *, actor: str, entity: str) -> None: ...
    def get_social_metadata(self, entity_urn: str) -> dict[str, Any]: ...
    def batch_get_social_metadata(self, entity_urns: list[str]) -> dict[str, Any]: ...
    def update_social_metadata_comments_state(
        self,
        *,
        entity_urn: str,
        actor: str,
        comments_state: str,
    ) -> None: ...


ClientFactory = Callable[..., object]

POST_ACTIONS = {"create", "get", "list", "delete", "edit", "batch-get"}
POST_VIEW_CONTEXTS = ("AUTHOR", "READER")
POST_SORT_OPTIONS = ("LAST_MODIFIED", "CREATED")
POST_LIST_MAX_COUNT = 100
REACTION_SORT_OPTIONS = ("CHRONOLOGICAL", "REVERSE_CHRONOLOGICAL", "RELEVANCE")
COMMENTS_STATE_OPTIONS = ("OPEN", "CLOSED")
ORGANIZATION_ACCESS_STATES = ("APPROVED", "REQUESTED", "REVOKED", "REJECTED")
BROWSER_CHOICES = SUPPORTED_BROWSERS


def build_parser(
    *,
    explicit_post_actions: bool = False,
    prog: str | None = None,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Publish and manage LinkedIn posts with the official API.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    post_parser = subparsers.add_parser("post", help="Publish or manage posts")
    if explicit_post_actions:
        post_subparsers = post_parser.add_subparsers(dest="post_command", required=True)
        create_parser = post_subparsers.add_parser("create", help="Publish a post")
        _add_post_create_arguments(create_parser)
        create_parser.set_defaults(post_command="create")

        get_parser = post_subparsers.add_parser("get", help="Read a post by URN")
        get_parser.add_argument("post_urn", help="Post URN, for example urn:li:share:123")
        _add_access_token_argument(get_parser)
        _add_api_version_argument(get_parser)
        _add_view_context_argument(get_parser)
        get_parser.set_defaults(post_command="get")

        list_parser = post_subparsers.add_parser("list", help="List posts for an author")
        list_parser.add_argument("--author", help="Author URN, for example urn:li:person:abc123")
        _add_access_token_argument(list_parser)
        _add_api_version_argument(list_parser)
        list_parser.add_argument("--count", type=int, default=10, help="Number of posts to fetch")
        list_parser.add_argument("--start", type=int, default=0, help="Pagination offset")
        list_parser.add_argument(
            "--sort-by",
            choices=POST_SORT_OPTIONS,
            default="LAST_MODIFIED",
            help="Sort order for the official author finder.",
        )
        _add_view_context_argument(list_parser)
        list_parser.set_defaults(post_command="list")

        batch_get_parser = post_subparsers.add_parser(
            "batch-get",
            help="Read multiple posts by URN",
        )
        batch_get_parser.add_argument("post_urns", nargs="+", help="One or more post URNs")
        _add_access_token_argument(batch_get_parser)
        _add_api_version_argument(batch_get_parser)
        _add_view_context_argument(batch_get_parser)
        batch_get_parser.set_defaults(post_command="batch-get")

        delete_parser = post_subparsers.add_parser("delete", help="Delete a post by URN")
        delete_parser.add_argument("post_urn", help="Post URN, for example urn:li:share:123")
        _add_access_token_argument(delete_parser)
        _add_api_version_argument(delete_parser)
        delete_parser.set_defaults(post_command="delete")

        edit_parser = post_subparsers.add_parser("edit", help="Partially update a post")
        edit_parser.add_argument("post_urn", help="Post URN, for example urn:li:share:123")
        _add_access_token_argument(edit_parser)
        _add_api_version_argument(edit_parser)
        edit_parser.add_argument("--text", dest="edited_commentary", help="Replacement post text")
        edit_parser.add_argument("--cta-label", help="Content call-to-action label")
        edit_parser.add_argument("--landing-page", help="Landing page URL for the content CTA")
        edit_parser.add_argument("--lifecycle-state", help="Replacement post lifecycle state")
        edit_parser.set_defaults(post_command="edit")
    else:
        _add_post_create_arguments(post_parser)
        post_parser.set_defaults(post_command="create")

    image_parser = subparsers.add_parser("image", help="Inspect LinkedIn image assets")
    image_subparsers = image_parser.add_subparsers(dest="image_command", required=True)
    image_get_parser = image_subparsers.add_parser("get", help="Read an image asset by URN")
    image_get_parser.add_argument("image_urn", help="Image URN, for example urn:li:image:123")
    _add_access_token_argument(image_get_parser)
    _add_api_version_argument(image_get_parser)
    image_get_parser.set_defaults(image_command="get")
    image_list_parser = image_subparsers.add_parser(
        "list",
        help="Batch read image assets by URN",
    )
    image_list_parser.add_argument("--id", dest="image_urns", action="append", required=True, help="Image URN to fetch")
    _add_access_token_argument(image_list_parser)
    _add_api_version_argument(image_list_parser)
    image_list_parser.set_defaults(image_command="list")

    document_parser = subparsers.add_parser("document", help="Inspect LinkedIn document assets")
    document_subparsers = document_parser.add_subparsers(dest="document_command", required=True)
    document_get_parser = document_subparsers.add_parser("get", help="Read a document asset by URN")
    document_get_parser.add_argument(
        "document_urn",
        help="Document URN, for example urn:li:document:123",
    )
    _add_access_token_argument(document_get_parser)
    _add_api_version_argument(document_get_parser)
    document_get_parser.set_defaults(document_command="get")
    document_list_parser = document_subparsers.add_parser(
        "list",
        help="Batch read document assets by URN",
    )
    document_list_parser.add_argument(
        "--id",
        dest="document_urns",
        action="append",
        required=True,
        help="Document URN to fetch",
    )
    _add_access_token_argument(document_list_parser)
    _add_api_version_argument(document_list_parser)
    document_list_parser.set_defaults(document_command="list")

    video_parser = subparsers.add_parser("video", help="Inspect LinkedIn video assets")
    video_subparsers = video_parser.add_subparsers(dest="video_command", required=True)
    video_get_parser = video_subparsers.add_parser("get", help="Read a video asset by URN")
    video_get_parser.add_argument("video_urn", help="Video URN, for example urn:li:video:123")
    _add_access_token_argument(video_get_parser)
    _add_api_version_argument(video_get_parser)
    video_get_parser.set_defaults(video_command="get")
    video_list_parser = video_subparsers.add_parser(
        "list",
        help="Batch read video assets by URN",
    )
    video_list_parser.add_argument("--id", dest="video_urns", action="append", required=True, help="Video URN to fetch")
    _add_access_token_argument(video_list_parser)
    _add_api_version_argument(video_list_parser)
    video_list_parser.set_defaults(video_command="list")

    organization_parser = subparsers.add_parser(
        "organization",
        help="Inspect LinkedIn organization access-control assignments",
    )
    organization_subparsers = organization_parser.add_subparsers(
        dest="organization_command",
        required=True,
    )
    organization_list_parser = organization_subparsers.add_parser(
        "list",
        help="List organization access rows for the authenticated viewer",
    )
    organization_list_parser.add_argument(
        "--role",
        help="Optional role filter for organization access records.",
    )
    organization_list_parser.add_argument(
        "--state",
        choices=ORGANIZATION_ACCESS_STATES,
        help="Optional state filter for organization access records.",
    )
    organization_list_parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of access rows to fetch.",
    )
    organization_list_parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Pagination offset for access rows.",
    )
    _add_access_token_argument(organization_list_parser)
    _add_api_version_argument(organization_list_parser)
    organization_list_parser.set_defaults(organization_command="list")

    organization_preflight_parser = organization_subparsers.add_parser(
        "preflight",
        help="Summarize whether the authenticated member can post as an organization",
    )
    organization_preflight_parser.add_argument(
        "organization_urn",
        help="Organization URN, for example urn:li:organization:2414183",
    )
    organization_preflight_parser.add_argument(
        "--member",
        help="Member URN, for example urn:li:person:abc123",
    )
    _add_access_token_argument(organization_preflight_parser)
    _add_api_version_argument(organization_preflight_parser)
    organization_preflight_parser.set_defaults(organization_command="preflight")

    organization_members_parser = organization_subparsers.add_parser(
        "members",
        help="List members with access to an organization",
    )
    organization_members_parser.add_argument(
        "organization_urn",
        help="Organization URN, for example urn:li:organization:2414183",
    )
    organization_members_parser.add_argument(
        "--role",
        help="Optional role filter for organization access records.",
    )
    organization_members_parser.add_argument(
        "--state",
        choices=ORGANIZATION_ACCESS_STATES,
        help="Optional state filter for organization access records.",
    )
    organization_members_parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of access rows to fetch.",
    )
    organization_members_parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Pagination offset for access rows.",
    )
    _add_access_token_argument(organization_members_parser)
    _add_api_version_argument(organization_members_parser)
    organization_members_parser.set_defaults(organization_command="members")

    comment_parser = subparsers.add_parser("comment", help="Inspect LinkedIn comments")
    comment_subparsers = comment_parser.add_subparsers(dest="comment_command", required=True)
    comment_get_parser = comment_subparsers.add_parser("get", help="Read a comment by target URN and ID")
    comment_get_parser.add_argument("target_urn", help="Root share or ugcPost URN for the social action")
    comment_get_parser.add_argument("comment_id", help="Comment ID within the social action")
    _add_access_token_argument(comment_get_parser)
    _add_api_version_argument(comment_get_parser)
    comment_get_parser.set_defaults(comment_command="get")
    comment_create_parser = comment_subparsers.add_parser("create", help="Create a comment on a root entity")
    comment_create_parser.add_argument("target_urn", help="Root share or ugcPost URN")
    comment_create_parser.add_argument("--actor", required=True, help="Actor URN")
    comment_create_parser.add_argument("--parent-comment", help="Optional parent comment URN for replies")
    comment_create_parser.add_argument("--attributes-json", type=Path, help="Path to a JSON array of LinkedIn comment attributes")
    comment_create_parser.add_argument("--content-image-urn", help="Existing LinkedIn image URN to attach to the comment")
    comment_create_parser.add_argument("text", nargs="+", help="Comment text")
    _add_access_token_argument(comment_create_parser)
    _add_api_version_argument(comment_create_parser)
    comment_create_parser.set_defaults(comment_command="create")
    comment_list_parser = comment_subparsers.add_parser(
        "list",
        help="List comments for a root entity or comment URN",
    )
    comment_list_parser.add_argument("target_urn", help="Root share/post/comment URN")
    comment_list_parser.add_argument("--count", type=int, default=10, help="Number of comments to fetch")
    comment_list_parser.add_argument("--start", type=int, default=0, help="Pagination offset")
    _add_access_token_argument(comment_list_parser)
    _add_api_version_argument(comment_list_parser)
    comment_list_parser.set_defaults(comment_command="list")
    comment_batch_get_parser = comment_subparsers.add_parser(
        "batch-get",
        help="Read multiple comments under the same social action",
    )
    comment_batch_get_parser.add_argument("target_urn", help="Root share or comment URN")
    comment_batch_get_parser.add_argument("comment_ids", nargs="+", help="One or more comment IDs")
    _add_access_token_argument(comment_batch_get_parser)
    _add_api_version_argument(comment_batch_get_parser)
    comment_batch_get_parser.set_defaults(comment_command="batch-get")
    comment_edit_parser = comment_subparsers.add_parser("edit", help="Edit a comment by ID")
    comment_edit_parser.add_argument("target_urn", help="Root share or ugcPost URN for the social action")
    comment_edit_parser.add_argument("comment_id", help="Comment ID within the social action")
    comment_edit_parser.add_argument("--actor", help="Optional actor URN; required for some org flows")
    comment_edit_parser.add_argument("--attributes-json", type=Path, help="Path to a JSON array of LinkedIn comment attributes")
    comment_edit_parser.add_argument("--text", dest="comment_text", nargs="+", required=True, help="Replacement comment text")
    _add_access_token_argument(comment_edit_parser)
    _add_api_version_argument(comment_edit_parser)
    comment_edit_parser.set_defaults(comment_command="edit")
    comment_delete_parser = comment_subparsers.add_parser("delete", help="Delete a comment by ID")
    comment_delete_parser.add_argument("target_urn", help="Root share or ugcPost URN for the social action")
    comment_delete_parser.add_argument("comment_id", help="Comment ID within the social action")
    comment_delete_parser.add_argument("--actor", help="Optional actor URN; required for some org flows")
    _add_access_token_argument(comment_delete_parser)
    _add_api_version_argument(comment_delete_parser)
    comment_delete_parser.set_defaults(comment_command="delete")

    reaction_parser = subparsers.add_parser("reaction", help="Create LinkedIn reactions")
    reaction_subparsers = reaction_parser.add_subparsers(dest="reaction_command", required=True)
    reaction_create_parser = reaction_subparsers.add_parser("create", help="Create a reaction on a root entity")
    reaction_create_parser.add_argument("--actor", required=True, help="Actor URN, for example urn:li:person:abc123")
    reaction_create_parser.add_argument("--root", required=True, help="Root URN, for example urn:li:share:123")
    reaction_create_parser.add_argument(
        "--type",
        dest="reaction_type",
        required=True,
        help="LinkedIn reaction type, for example LIKE or PRAISE.",
    )
    _add_access_token_argument(reaction_create_parser)
    _add_api_version_argument(reaction_create_parser)
    reaction_create_parser.set_defaults(reaction_command="create")
    reaction_get_parser = reaction_subparsers.add_parser("get", help="Read a reaction by actor/entity key")
    reaction_get_parser.add_argument("--actor", required=True, help="Actor URN")
    reaction_get_parser.add_argument("--entity", required=True, help="Entity URN")
    _add_access_token_argument(reaction_get_parser)
    _add_api_version_argument(reaction_get_parser)
    reaction_get_parser.set_defaults(reaction_command="get")
    reaction_list_parser = reaction_subparsers.add_parser("list", help="List reactions for one entity")
    reaction_list_parser.add_argument("entity", help="Entity URN")
    reaction_list_parser.add_argument("--count", type=int, default=10, help="Number of reactions to fetch")
    reaction_list_parser.add_argument("--start", type=int, default=0, help="Pagination offset")
    reaction_list_parser.add_argument(
        "--sort",
        choices=REACTION_SORT_OPTIONS,
        default="REVERSE_CHRONOLOGICAL",
        help="Reaction sort order.",
    )
    _add_access_token_argument(reaction_list_parser)
    _add_api_version_argument(reaction_list_parser)
    reaction_list_parser.set_defaults(reaction_command="list")
    reaction_batch_get_parser = reaction_subparsers.add_parser(
        "batch-get",
        help="Read multiple reactions by actor/entity key",
    )
    reaction_batch_get_parser.add_argument(
        "--key",
        dest="reaction_keys",
        action="append",
        nargs=2,
        metavar=("ACTOR_URN", "ENTITY_URN"),
        required=True,
        help="Reaction key pair; repeat the flag.",
    )
    _add_access_token_argument(reaction_batch_get_parser)
    _add_api_version_argument(reaction_batch_get_parser)
    reaction_batch_get_parser.set_defaults(reaction_command="batch-get")
    reaction_delete_parser = reaction_subparsers.add_parser("delete", help="Delete a reaction by actor/entity key")
    reaction_delete_parser.add_argument("--actor", required=True, help="Actor URN")
    reaction_delete_parser.add_argument("--entity", required=True, help="Entity URN")
    _add_access_token_argument(reaction_delete_parser)
    _add_api_version_argument(reaction_delete_parser)
    reaction_delete_parser.set_defaults(reaction_command="delete")

    social_metadata_parser = subparsers.add_parser(
        "social-metadata",
        help="Inspect LinkedIn social metadata for a root entity",
    )
    social_metadata_subparsers = social_metadata_parser.add_subparsers(
        dest="social_metadata_command",
        required=True,
    )
    social_metadata_get_parser = social_metadata_subparsers.add_parser(
        "get",
        help="Read social metadata by entity URN",
    )
    social_metadata_get_parser.add_argument(
        "entity_urn",
        help="Entity URN, for example urn:li:share:123",
    )
    _add_access_token_argument(social_metadata_get_parser)
    _add_api_version_argument(social_metadata_get_parser)
    social_metadata_get_parser.set_defaults(social_metadata_command="get")
    social_metadata_batch_get_parser = social_metadata_subparsers.add_parser(
        "batch-get",
        help="Read social metadata for multiple entity URNs",
    )
    social_metadata_batch_get_parser.add_argument("entity_urns", nargs="+", help="One or more entity URNs")
    _add_access_token_argument(social_metadata_batch_get_parser)
    _add_api_version_argument(social_metadata_batch_get_parser)
    social_metadata_batch_get_parser.set_defaults(social_metadata_command="batch-get")
    social_metadata_update_parser = social_metadata_subparsers.add_parser(
        "set-comments-state",
        help="Open or close comments on a thread; closing deletes existing comments",
    )
    social_metadata_update_parser.add_argument("entity_urn", help="Thread URN, for example a share or ugcPost URN")
    social_metadata_update_parser.add_argument("--actor", required=True, help="Actor URN performing the update")
    social_metadata_update_parser.add_argument(
        "--state",
        dest="comments_state",
        choices=COMMENTS_STATE_OPTIONS,
        required=True,
        help="New comments state. LinkedIn deletes existing comments when switching to CLOSED.",
    )
    _add_access_token_argument(social_metadata_update_parser)
    _add_api_version_argument(social_metadata_update_parser)
    social_metadata_update_parser.set_defaults(social_metadata_command="set-comments-state")

    profile_parser = subparsers.add_parser("profile", help="Read supported LinkedIn profile data")
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command", required=True)
    whoami_parser = profile_subparsers.add_parser("whoami", help="Read the authenticated member profile")
    whoami_parser.add_argument(
        "--source",
        choices=("userinfo", "profile-api", "identity-me"),
        default="userinfo",
        help="Official LinkedIn API source.",
    )
    _add_access_token_argument(whoami_parser)
    _add_api_version_argument(whoami_parser)
    _add_identity_api_version_argument(whoami_parser)
    employment_parser = profile_subparsers.add_parser(
        "employment-history",
        help="Read employment data from supported LinkedIn profile APIs",
    )
    employment_parser.add_argument(
        "--source",
        choices=("profile-api", "identity-me", "voyager-private"),
        default="profile-api",
        help="LinkedIn profile source.",
    )
    employment_parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Return only employment records overlapping the last N years.",
    )
    employment_parser.add_argument(
        "--public-id",
        default=None,
        help="LinkedIn public profile identifier, for example `brenorb`. Required for `--source voyager-private`.",
    )
    employment_parser.add_argument(
        "--li-at",
        default=None,
        help="LinkedIn `li_at` session cookie for `--source voyager-private`.",
    )
    employment_parser.add_argument(
        "--jsessionid",
        default=None,
        help="LinkedIn `JSESSIONID` session cookie for `--source voyager-private`.",
    )
    employment_parser.add_argument(
        "--csrf-token",
        default=None,
        help="Voyager CSRF token. If omitted, the value is derived from `--jsessionid`.",
    )
    employment_parser.add_argument(
        "--browser",
        choices=BROWSER_CHOICES,
        default=None,
        help="Load `li_at` and `JSESSIONID` from a local browser profile for `--source voyager-private`.",
    )
    employment_parser.add_argument(
        "--cookie-file",
        type=Path,
        default=None,
        help="Override the browser cookie database path used with `--browser`.",
    )
    _add_access_token_argument(employment_parser)
    _add_api_version_argument(employment_parser)
    _add_identity_api_version_argument(employment_parser)
    voyager_session_parser = profile_subparsers.add_parser(
        "voyager-session",
        help="Read LinkedIn Voyager web-session cookies from a local browser profile",
    )
    voyager_session_parser.add_argument(
        "--browser",
        choices=BROWSER_CHOICES,
        default="chrome",
        help="Browser profile to read. Defaults to Chrome.",
    )
    voyager_session_parser.add_argument(
        "--cookie-file",
        type=Path,
        default=None,
        help="Override the browser cookie database path.",
    )
    voyager_session_parser.add_argument(
        "--public-id",
        default=None,
        help="Optional LinkedIn public profile identifier to include in the exported output.",
    )
    voyager_session_parser.add_argument(
        "--format",
        choices=("env", "json"),
        default="env",
        help="Output format. `env` prints export statements; `json` prints structured fields.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    client_factory: ClientFactory | None = None,
) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser(
        explicit_post_actions=_uses_explicit_post_action(argv_list),
        prog=Path(sys.argv[0]).name if argv is None else None,
    )
    args = parser.parse_args(argv_list)
    environment = dict(os.environ if env is None else env)

    if args.command == "post":
        return _run_post(args, environment, client_factory or _default_client_factory)
    if args.command == "image":
        return _run_image(args, environment, client_factory or _default_client_factory)
    if args.command == "document":
        return _run_document(args, environment, client_factory or _default_client_factory)
    if args.command == "video":
        return _run_video(args, environment, client_factory or _default_client_factory)
    if args.command == "organization":
        return _run_organization(args, environment, client_factory or _default_client_factory)
    if args.command == "comment":
        return _run_comment(args, environment, client_factory or _default_client_factory)
    if args.command == "reaction":
        return _run_reaction(args, environment, client_factory or _default_client_factory)
    if args.command == "social-metadata":
        return _run_social_metadata(args, environment, client_factory or _default_client_factory)
    if args.command == "profile" and args.profile_command == "whoami":
        return _run_profile_whoami(args, environment, client_factory or _default_client_factory)
    if args.command == "profile" and args.profile_command == "employment-history":
        return _run_employment_history(args, environment, client_factory or _default_client_factory)
    if args.command == "profile" and args.profile_command == "voyager-session":
        return _run_profile_voyager_session(args, environment)

    parser.error(f"unknown command: {args.command}")
    return 2


def _run_post(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    post_command = cast(str, args.post_command)
    access_token = _configured_value(getattr(args, "access_token", None), env.get("LINKEDIN_ACCESS_TOKEN"))
    api_version = _configured_value(getattr(args, "api_version", None), env.get("LINKEDIN_API_VERSION"))
    author = _configured_value(getattr(args, "author", None), env.get("LINKEDIN_AUTHOR_URN"))
    resolved_api_version = api_version or DEFAULT_API_VERSION

    missing: list[str] = []
    if access_token is None:
        missing.append("access token")
    if _post_requires_author(post_command) and author is None:
        missing.append("author URN")

    if missing:
        print(f"Missing required configuration: {', '.join(missing)}.", file=sys.stderr)
        return 2

    if post_command == "create" and args.alt_text and not (args.image or args.image_urn):
        print("Missing required configuration: alt text requires an image.", file=sys.stderr)
        return 2

    if post_command == "create" and _post_create_has_conflicting_media(args):
        print("Missing required configuration: choose either an image or a video, not both.", file=sys.stderr)
        return 2

    if post_command == "create" and args.reshare_post_urn and _post_create_has_attached_media(args):
        print(
            "Missing required configuration: reshare posts cannot also attach image or video media.",
            file=sys.stderr,
        )
        return 2

    if post_command == "create" and args.image and args.image_urn:
        print("Missing required configuration: choose either an image path or an image URN, not both.", file=sys.stderr)
        return 2

    if post_command == "create" and args.article_thumbnail and args.article_thumbnail_urn:
        print(
            "Missing required configuration: choose either an article thumbnail path or URN, not both.",
            file=sys.stderr,
        )
        return 2

    if post_command == "create" and args.article_url and not args.article_title:
        print("Missing required configuration: article posts require an article title.", file=sys.stderr)
        return 2

    if post_command == "create" and args.multi_image and args.multi_image_urn:
        print(
            "Missing required configuration: choose either multi-image paths or multi-image URNs, not both.",
            file=sys.stderr,
        )
        return 2

    if post_command == "create" and args.video and args.video_urn:
        print("Missing required configuration: choose either a video path or a video URN, not both.", file=sys.stderr)
        return 2

    if post_command == "create" and (args.document or args.document_urn) and not args.document_title:
        print("Missing required configuration: document posts require a document title.", file=sys.stderr)
        return 2

    if (
        post_command == "create"
        and args.multi_image
        and not MIN_MULTI_IMAGE_COUNT <= len(args.multi_image) <= MAX_MULTI_IMAGE_COUNT
    ):
        print("Missing required configuration: multi-image posts require 2 to 20 images.", file=sys.stderr)
        return 2

    if (
        post_command == "create"
        and args.multi_image_urn
        and not MIN_MULTI_IMAGE_COUNT <= len(args.multi_image_urn) <= MAX_MULTI_IMAGE_COUNT
    ):
        print("Missing required configuration: multi-image posts require 2 to 20 images.", file=sys.stderr)
        return 2

    if post_command == "create" and args.multi_image_alt_text:
        total_images = len(args.multi_image or []) + len(args.multi_image_urn or [])
        if total_images == 0:
            print("Missing required configuration: multi-image alt text requires multi-image content.", file=sys.stderr)
            return 2
        if len(args.multi_image_alt_text) != total_images:
            print(
                "Missing required configuration: multi-image alt text count must match the number of images.",
                file=sys.stderr,
            )
            return 2
    if post_command == "create" and args.poll_question:
        if len(args.poll_option or []) < 2:
            print("Missing required configuration: poll posts require at least two poll options.", file=sys.stderr)
            return 2
    elif post_command == "create" and args.poll_option:
        print("Missing required configuration: poll options require a poll question.", file=sys.stderr)
        return 2

    if post_command == "list" and args.count > POST_LIST_MAX_COUNT:
        print(
            f"Missing required configuration: count must be <= {POST_LIST_MAX_COUNT}.",
            file=sys.stderr,
        )
        return 2

    if post_command == "edit" and not _post_edit_has_changes(args):
        print("Missing required configuration: provide at least one editable field.", file=sys.stderr)
        return 2

    client = cast(
        LinkedInPostClient,
        client_factory(access_token=access_token, api_version=resolved_api_version),
    )
    try:
        if post_command == "create":
            assert author is not None
            result = _create_post(client, args, author=author)
            post_id = getattr(result, "post_id", None)
            if post_id:
                print(f"Created post {post_id}")
            else:
                print("Created post")
            return 0

        if post_command == "get":
            result = client.get_post(args.post_urn, view_context=args.view_context)
            print(json.dumps(result, indent=2))
            return 0

        if post_command == "list":
            assert author is not None
            result = client.list_posts(
                author=author,
                count=args.count,
                start=args.start,
                sort_by=args.sort_by,
                view_context=args.view_context,
            )
            print(json.dumps(result, indent=2))
            return 0

        if post_command == "batch-get":
            result = client.batch_get_posts(args.post_urns, view_context=args.view_context)
            print(json.dumps(result, indent=2))
            return 0

        if post_command == "delete":
            client.delete_post(args.post_urn)
            print(f"Deleted post {args.post_urn}")
            return 0

        if post_command == "edit":
            client.update_post(
                args.post_urn,
                commentary=args.edited_commentary,
                content_call_to_action_label=args.cta_label,
                content_landing_page=args.landing_page,
                lifecycle_state=args.lifecycle_state,
            )
            print(f"Updated post {args.post_urn}")
            return 0

        raise AssertionError(f"Unsupported post command: {post_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_employment_history(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2
    public_identifier = _configured_public_identifier(args, env)
    voyager_fallback_available = _has_voyager_fallback(args, env, require_public_id=True)
    browser_profile_fallback_available = _has_browser_profile_fallback(args, env, require_public_id=True)
    access_token_available = _configured_value(getattr(args, "access_token", None), env.get("LINKEDIN_ACCESS_TOKEN")) is not None
    try:
        if args.source == "identity-me":
            records = client.get_current_employment()
        elif args.source == "voyager-private":
            if public_identifier is None:
                print("Missing required configuration: public profile identifier.", file=sys.stderr)
                return 2
            records = _voyager_employment_with_browser_fallback(
                client=client,
                public_identifier=public_identifier,
                browser_profile_fallback_available=browser_profile_fallback_available,
            )
        else:
            records = _employment_history_with_fallback(
                client=client,
                source=args.source,
                public_identifier=public_identifier,
                voyager_fallback_available=voyager_fallback_available,
                browser_profile_fallback_available=browser_profile_fallback_available,
                prefer_voyager=not access_token_available,
            )
        filtered = filter_employment_history(records, years=args.years, today=date.today())
    except (LinkedInApiError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)

    print(json.dumps(filtered, indent=2))
    return 0


def _add_post_create_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("commentary", nargs="+", help="Post text")
    parser.add_argument("--poll-question", help="Question for a LinkedIn poll post")
    parser.add_argument("--poll-option", action="append", help="Poll option text; repeat the flag")
    parser.add_argument(
        "--poll-duration",
        default=None,
        help="Poll duration token from the LinkedIn API. Defaults to THREE_DAYS.",
    )
    parser.add_argument("--reshare-post-urn", help="Existing LinkedIn post URN to reshare")
    parser.add_argument("--image", type=Path, help="Path to an image to upload and attach")
    parser.add_argument("--image-urn", help="Existing LinkedIn image asset URN to reuse")
    parser.add_argument("--multi-image", action="append", type=Path, help="Path to an image for a multi-image post; repeat the flag")
    parser.add_argument("--multi-image-urn", action="append", help="Existing LinkedIn image asset URN for a multi-image post; repeat the flag")
    parser.add_argument("--multi-image-alt-text", action="append", help="Alt text for each multi-image entry; repeat in image order")
    parser.add_argument("--document", type=Path, help="Path to a document to upload and attach")
    parser.add_argument("--document-urn", help="Existing LinkedIn document asset URN to reuse")
    parser.add_argument("--document-title", help="Title for the uploaded document")
    parser.add_argument("--article-url", help="External article URL to attach")
    parser.add_argument("--article-title", help="Title for the attached article")
    parser.add_argument("--article-description", help="Description for the attached article")
    parser.add_argument("--article-thumbnail", type=Path, help="Path to an image to upload for the article thumbnail")
    parser.add_argument("--article-thumbnail-urn", help="Existing LinkedIn image asset URN for the article thumbnail")
    parser.add_argument("--alt-text", help="Alt text for the uploaded image")
    parser.add_argument("--video", type=Path, help="Path to a video to upload and attach")
    parser.add_argument("--video-urn", help="Existing LinkedIn video asset URN to reuse")
    parser.add_argument("--video-title", help="Title for the uploaded video")
    parser.add_argument("--video-captions", type=Path, help="Path to a WebVTT captions file to upload with the video")
    parser.add_argument("--video-thumbnail", type=Path, help="Path to an image thumbnail to upload with the video")
    parser.add_argument("--author", help="Author URN, for example urn:li:person:abc123")
    _add_access_token_argument(parser)
    _add_api_version_argument(parser)
    parser.add_argument("--visibility", default="PUBLIC", help="LinkedIn post visibility")


def _add_access_token_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--access-token", help="OAuth access token")


def _add_api_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--api-version",
        default=None,
        help=f"LinkedIn API version in YYYYMM format. Defaults to {DEFAULT_API_VERSION}.",
    )


def _add_identity_api_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--identity-api-version",
        default=None,
        help=(
            "Verified on LinkedIn `/rest/identityMe` release-track version, for example "
            f"{DEFAULT_IDENTITY_API_VERSION}. Required when `--source identity-me` is used."
        ),
    )


def _add_view_context_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--view-context",
        choices=POST_VIEW_CONTEXTS,
        default=None,
        help="Optional LinkedIn post view context. Defaults to LinkedIn's API default.",
    )


def _uses_explicit_post_action(argv: Sequence[str]) -> bool:
    return len(argv) >= 2 and argv[0] == "post" and argv[1] in POST_ACTIONS


def _post_requires_author(post_command: str) -> bool:
    return post_command in {"create", "list"}


def _post_edit_has_changes(args: argparse.Namespace) -> bool:
    return any(
        (
            getattr(args, "edited_commentary", None),
            getattr(args, "cta_label", None),
            getattr(args, "landing_page", None),
            getattr(args, "lifecycle_state", None),
        )
    )


def _post_create_has_conflicting_media(args: argparse.Namespace) -> bool:
    sources = [
        bool(args.poll_question),
        bool(args.image or args.image_urn),
        bool(args.multi_image or args.multi_image_urn),
        bool(args.document or args.document_urn),
        bool(args.article_url),
        bool(args.video or args.video_urn),
    ]
    return sum(sources) > 1


def _post_create_has_attached_media(args: argparse.Namespace) -> bool:
    return bool(
        args.poll_question
        or args.multi_image_urn
        or args.multi_image_alt_text
        or
        args.image
        or args.image_urn
        or args.multi_image
        or args.document
        or args.document_urn
        or args.video
        or args.video_urn
        or args.article_url
    )


def _configured_value(cli_value: str | None, env_value: str | None) -> str | None:
    for value in (cli_value, env_value):
        if value is not None and value != "":
            return value
    return None


def _configured_public_identifier(args: argparse.Namespace, env: Mapping[str, str]) -> str | None:
    return _configured_value(
        getattr(args, "public_id", None),
        env.get("LINKEDIN_PROFILE_PUBLIC_ID") or env.get("LINKEDIN_VOYAGER_PUBLIC_ID"),
    )


def _configured_cookie_file(args: argparse.Namespace, env: Mapping[str, str]) -> Path | None:
    path_value = _configured_value(
        str(getattr(args, "cookie_file", "")) if getattr(args, "cookie_file", None) is not None else None,
        env.get("LINKEDIN_VOYAGER_COOKIE_FILE"),
    )
    return Path(path_value) if path_value is not None else None


def _configured_browser_session(
    args: argparse.Namespace,
    env: Mapping[str, str],
) -> tuple[str, str, str] | None:
    browser = _configured_browser(args, env)
    if browser is None:
        return None

    try:
        session = load_voyager_session_from_browser(
            browser=browser,
            cookie_file=_configured_cookie_file(args, env),
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return None

    return session.li_at, session.jsessionid, session.csrf_token


def _has_voyager_fallback(
    args: argparse.Namespace,
    env: Mapping[str, str],
    *,
    require_public_id: bool,
) -> bool:
    has_session = any(
        value is not None
        for value in (
            _configured_value(getattr(args, "li_at", None), env.get("LINKEDIN_VOYAGER_LI_AT")),
            _configured_value(getattr(args, "jsessionid", None), env.get("LINKEDIN_VOYAGER_JSESSIONID")),
            _configured_value(getattr(args, "csrf_token", None), env.get("LINKEDIN_VOYAGER_CSRF_TOKEN")),
            _configured_value(getattr(args, "browser", None), env.get("LINKEDIN_VOYAGER_BROWSER")),
        )
    )
    if not has_session:
        return False
    if not require_public_id:
        return True
    return _configured_public_identifier(args, env) is not None


def _has_browser_profile_fallback(
    args: argparse.Namespace,
    env: Mapping[str, str],
    *,
    require_public_id: bool,
) -> bool:
    if _configured_browser(args, env) != "chrome":
        return False
    if not require_public_id:
        return True
    return _configured_public_identifier(args, env) is not None


def _configured_browser(args: argparse.Namespace, env: Mapping[str, str]) -> str | None:
    return _configured_value(getattr(args, "browser", None), env.get("LINKEDIN_VOYAGER_BROWSER"))


def _read_json_file(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _create_post(
    client: LinkedInPostClient,
    args: argparse.Namespace,
    *,
    author: str,
) -> object:
    commentary = " ".join(args.commentary)
    if args.poll_question:
        return client.create_poll_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            question=args.poll_question,
            options=args.poll_option or [],
            duration=args.poll_duration or "THREE_DAYS",
        )
    if args.reshare_post_urn:
        return client.create_reshare_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            reshared_post_urn=args.reshare_post_urn,
        )
    if args.multi_image:
        return client.create_multi_image_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            image_paths=args.multi_image,
            alt_texts=args.multi_image_alt_text,
        )
    if args.multi_image_urn:
        return client.create_multi_image_post_from_assets(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            image_urns=args.multi_image_urn,
            alt_texts=args.multi_image_alt_text,
        )
    if args.image:
        return client.create_image_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            image_path=args.image,
            alt_text=args.alt_text,
        )
    if args.image_urn:
        return client.create_image_post_from_asset(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            image_urn=args.image_urn,
            alt_text=args.alt_text,
        )
    if args.document:
        return client.create_document_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            document_path=args.document,
            title=args.document_title,
        )
    if args.document_urn:
        return client.create_document_post_from_asset(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            document_urn=args.document_urn,
            title=args.document_title,
        )
    if args.article_url:
        return client.create_article_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            article_url=args.article_url,
            title=args.article_title,
            description=args.article_description,
            thumbnail_image_path=args.article_thumbnail,
            thumbnail_image_urn=args.article_thumbnail_urn,
        )
    if args.video:
        if args.video_captions is not None or args.video_thumbnail is not None:
            return client.create_video_post(
                author=author,
                commentary=commentary,
                visibility=args.visibility,
                video_path=args.video,
                title=args.video_title,
                captions_path=args.video_captions,
                thumbnail_path=args.video_thumbnail,
            )
        return client.create_video_post(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            video_path=args.video,
            title=args.video_title,
        )
    if args.video_urn:
        return client.create_video_post_from_asset(
            author=author,
            commentary=commentary,
            visibility=args.visibility,
            video_urn=args.video_urn,
            title=args.video_title,
        )
    return client.create_text_post(
        author=author,
        commentary=commentary,
        visibility=args.visibility,
    )


def _run_image(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.image_command == "get":
            print(json.dumps(client.get_image(args.image_urn), indent=2))
            return 0
        if args.image_command == "list":
            print(json.dumps(client.batch_get_images(args.image_urns), indent=2))
            return 0
        raise AssertionError(f"Unsupported image command: {args.image_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_document(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.document_command == "get":
            print(json.dumps(client.get_document(args.document_urn), indent=2))
            return 0
        if args.document_command == "list":
            print(json.dumps(client.batch_get_documents(args.document_urns), indent=2))
            return 0
        raise AssertionError(f"Unsupported document command: {args.document_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_video(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.video_command == "get":
            print(json.dumps(client.get_video(args.video_urn), indent=2))
            return 0
        if args.video_command == "list":
            print(json.dumps(client.batch_get_videos(args.video_urns), indent=2))
            return 0
        raise AssertionError(f"Unsupported video command: {args.video_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_organization(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    if args.organization_command == "preflight":
        member_urn = _configured_value(getattr(args, "member", None), env.get("LINKEDIN_MEMBER_URN"))
        if member_urn is None:
            print("Missing required configuration: member URN.", file=sys.stderr)
            return 2

    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.organization_command == "list":
            result = client.list_organization_access(
                count=args.count,
                start=args.start,
                role=args.role,
                state=args.state,
            )
            print(json.dumps(result, indent=2))
            return 0
        if args.organization_command == "preflight":
            result = client.preflight_organization_author(
                role_assignee=member_urn,
                organization=args.organization_urn,
            )
            print(json.dumps(result, indent=2))
            return 0
        if args.organization_command == "members":
            result = client.list_organization_access_by_organization(
                organization=args.organization_urn,
                count=args.count,
                start=args.start,
                role=args.role,
                state=args.state,
            )
            print(json.dumps(result, indent=2))
            return 0
        raise AssertionError(f"Unsupported organization command: {args.organization_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_comment(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    if args.comment_command == "create" and args.parent_comment and args.content_image_urn:
        print(
            "Missing required configuration: reply comments cannot attach content entities.",
            file=sys.stderr,
        )
        return 2

    if args.comment_command in {"edit", "delete"} and _is_comment_urn(args.target_urn):
        print(
            "Missing required configuration: comment updates and deletes require a share or ugcPost URN, not a comment URN.",
            file=sys.stderr,
        )
        return 2

    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.comment_command == "create":
            print(
                json.dumps(
                    client.create_comment(
                        target_urn=args.target_urn,
                        actor=args.actor,
                        text=" ".join(args.text),
                        parent_comment=args.parent_comment,
                        attributes=cast(
                            list[dict[str, object]] | None,
                            _read_json_file(args.attributes_json) if args.attributes_json else None,
                        ),
                        content_image_urn=args.content_image_urn,
                    ),
                    indent=2,
                )
            )
            return 0
        if args.comment_command == "get":
            print(json.dumps(client.get_comment(args.target_urn, args.comment_id), indent=2))
            return 0
        if args.comment_command == "list":
            print(
                json.dumps(
                    client.list_comments(
                        target_urn=args.target_urn,
                        count=args.count,
                        start=args.start,
                    ),
                    indent=2,
                )
            )
            return 0
        if args.comment_command == "batch-get":
            print(json.dumps(client.batch_get_comments(args.target_urn, args.comment_ids), indent=2))
            return 0
        if args.comment_command == "edit":
            client.update_comment(
                target_urn=args.target_urn,
                comment_id=args.comment_id,
                text=" ".join(args.comment_text),
                actor=args.actor,
                attributes=cast(
                    list[dict[str, object]] | None,
                    _read_json_file(args.attributes_json) if args.attributes_json else None,
                ),
            )
            print(f"Updated comment {args.comment_id}")
            return 0
        if args.comment_command == "delete":
            client.delete_comment(
                target_urn=args.target_urn,
                comment_id=args.comment_id,
                actor=args.actor,
            )
            print(f"Deleted comment {args.comment_id}")
            return 0
        raise AssertionError(f"Unsupported comment command: {args.comment_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_reaction(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.reaction_command == "create":
            print(
                json.dumps(
                    client.create_reaction(
                        actor=args.actor,
                        root=args.root,
                        reaction_type=args.reaction_type,
                    ),
                    indent=2,
                )
            )
            return 0
        if args.reaction_command == "get":
            print(
                json.dumps(
                    client.get_reaction(
                        actor=args.actor,
                        entity=args.entity,
                    ),
                    indent=2,
                )
            )
            return 0
        if args.reaction_command == "list":
            print(
                json.dumps(
                    client.list_reactions(
                        entity=args.entity,
                        count=args.count,
                        start=args.start,
                        sort=args.sort,
                    ),
                    indent=2,
                )
            )
            return 0
        if args.reaction_command == "batch-get":
            print(
                json.dumps(
                    client.batch_get_reactions(
                        [(actor, entity) for actor, entity in args.reaction_keys]
                    ),
                    indent=2,
                )
            )
            return 0
        if args.reaction_command == "delete":
            client.delete_reaction(actor=args.actor, entity=args.entity)
            print(f"Deleted reaction {args.actor} -> {args.entity}")
            return 0
        raise AssertionError(f"Unsupported reaction command: {args.reaction_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_social_metadata(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    if args.social_metadata_command == "set-comments-state" and _is_comment_urn(args.entity_urn):
        print(
            "Missing required configuration: comments-state updates require a thread URN, not a comment URN.",
            file=sys.stderr,
        )
        return 2

    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.social_metadata_command == "get":
            print(json.dumps(client.get_social_metadata(args.entity_urn), indent=2))
            return 0
        if args.social_metadata_command == "batch-get":
            print(json.dumps(client.batch_get_social_metadata(args.entity_urns), indent=2))
            return 0
        if args.social_metadata_command == "set-comments-state":
            client.update_social_metadata_comments_state(
                entity_urn=args.entity_urn,
                actor=args.actor,
                comments_state=args.comments_state,
            )
            print(f"Updated social metadata {args.entity_urn}")
            return 0
        raise AssertionError(f"Unsupported social metadata command: {args.social_metadata_command}")
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _run_profile_whoami(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    client = _configured_client(args, env, client_factory)
    if client is None:
        return 2

    try:
        if args.source == "identity-me":
            result = client.get_identity_profile()
            member_id = result.get("id")
            if isinstance(member_id, str) and member_id:
                result = dict(result)
                result["person_urn"] = f"urn:li:person:{member_id}"
        elif args.source == "profile-api":
            result = client.get_profile_identity()
            member_id = result.get("id")
            if isinstance(member_id, str) and member_id:
                result = dict(result)
                result["person_urn"] = f"urn:li:person:{member_id}"
        else:
            result = client.get_userinfo()
            sub = result.get("sub")
            if isinstance(sub, str) and sub:
                result = dict(result)
                result["person_urn"] = f"urn:li:person:{sub}"
        print(json.dumps(result, indent=2))
        return 0
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)


def _configured_client(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> LinkedInPostClient | None:
    access_token = _configured_value(getattr(args, "access_token", None), env.get("LINKEDIN_ACCESS_TOKEN"))
    api_version = _configured_value(getattr(args, "api_version", None), env.get("LINKEDIN_API_VERSION"))
    identity_api_version = _configured_value(
        getattr(args, "identity_api_version", None),
        env.get("LINKEDIN_IDENTITY_API_VERSION"),
    )
    voyager_requested = getattr(args, "source", None) == "voyager-private" or _has_voyager_fallback(
        args,
        env,
        require_public_id=False,
    )
    voyager_li_at = _configured_value(getattr(args, "li_at", None), env.get("LINKEDIN_VOYAGER_LI_AT"))
    voyager_jsessionid = _configured_value(
        getattr(args, "jsessionid", None),
        env.get("LINKEDIN_VOYAGER_JSESSIONID"),
    )
    voyager_csrf_token = _configured_value(
        getattr(args, "csrf_token", None),
        env.get("LINKEDIN_VOYAGER_CSRF_TOKEN"),
    )
    if voyager_requested and (voyager_li_at is None or (voyager_csrf_token is None and voyager_jsessionid is None)):
        browser_session = _configured_browser_session(args, env)
        if browser_session is None and _configured_value(
            getattr(args, "browser", None),
            env.get("LINKEDIN_VOYAGER_BROWSER"),
        ) is not None:
            return None
        if browser_session is not None:
            browser_li_at, browser_jsessionid, browser_csrf_token = browser_session
            voyager_li_at = voyager_li_at or browser_li_at
            voyager_jsessionid = voyager_jsessionid or browser_jsessionid
            voyager_csrf_token = voyager_csrf_token or browser_csrf_token
    if getattr(args, "source", None) == "voyager-private":
        public_identifier = _configured_public_identifier(args, env)
        missing: list[str] = []
        if voyager_li_at is None:
            missing.append("voyager li_at session cookie")
        if voyager_csrf_token is None and voyager_jsessionid is None:
            missing.append("voyager CSRF token or JSESSIONID")
        if public_identifier is None:
            missing.append("public profile identifier")
        if missing:
            print(f"Missing required configuration: {', '.join(missing)}.", file=sys.stderr)
            return None
    can_use_voyager_without_access_token = (
        getattr(args, "command", None) == "profile"
        and getattr(args, "profile_command", None) == "employment-history"
        and _configured_public_identifier(args, env) is not None
        and voyager_li_at is not None
        and (voyager_csrf_token is not None or voyager_jsessionid is not None)
    )
    if access_token is None and not can_use_voyager_without_access_token:
        print("Missing required configuration: access token.", file=sys.stderr)
        return None
    if getattr(args, "source", None) == "identity-me" and identity_api_version is None:
        print(
            "Missing required configuration: identity API version.",
            file=sys.stderr,
        )
        return None
    factory_kwargs: dict[str, str] = {
        "access_token": access_token or "",
        "api_version": api_version or DEFAULT_API_VERSION,
    }
    if identity_api_version is not None and _client_factory_accepts_kwarg(
        client_factory,
        "identity_api_version",
    ):
        factory_kwargs["identity_api_version"] = identity_api_version
    if voyager_li_at is not None and _client_factory_accepts_kwarg(client_factory, "voyager_li_at"):
        factory_kwargs["voyager_li_at"] = voyager_li_at
    if voyager_jsessionid is not None and _client_factory_accepts_kwarg(client_factory, "voyager_jsessionid"):
        factory_kwargs["voyager_jsessionid"] = voyager_jsessionid
    if voyager_csrf_token is not None and _client_factory_accepts_kwarg(client_factory, "voyager_csrf_token"):
        factory_kwargs["voyager_csrf_token"] = voyager_csrf_token
    return cast(
        LinkedInPostClient,
        client_factory(**factory_kwargs),
    )


def _close_client(client: LinkedInPostClient) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


def _is_comment_urn(urn: str) -> bool:
    return urn.startswith("urn:li:comment:")


def _client_factory_accepts_kwarg(factory: ClientFactory, kwarg: str) -> bool:
    signature = inspect.signature(factory)
    if kwarg in signature.parameters:
        return True
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )


def _default_client_factory(
    *,
    access_token: str,
    api_version: str,
    identity_api_version: str | None = None,
    voyager_li_at: str | None = None,
    voyager_jsessionid: str | None = None,
    voyager_csrf_token: str | None = None,
) -> LinkedInClient:
    return LinkedInClient(
        access_token=access_token,
        api_version=api_version,
        identity_api_version=identity_api_version,
        voyager_li_at=voyager_li_at,
        voyager_jsessionid=voyager_jsessionid,
        voyager_csrf_token=voyager_csrf_token,
    )


def _run_profile_voyager_session(
    args: argparse.Namespace,
    env: Mapping[str, str],
) -> int:
    browser = _configured_value(getattr(args, "browser", None), env.get("LINKEDIN_VOYAGER_BROWSER")) or "chrome"
    cookie_file = _configured_cookie_file(args, env)
    public_identifier = _configured_public_identifier(args, env)
    try:
        session = load_voyager_session_from_browser(
            browser=browser,
            cookie_file=cookie_file,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        print(
            json.dumps(
                {
                    "browser": session.browser,
                    "li_at": session.li_at,
                    "jsessionid": session.jsessionid,
                    "csrf_token": session.csrf_token,
                    "public_id": public_identifier,
                },
                indent=2,
            )
        )
        return 0

    exports = {
        "LINKEDIN_VOYAGER_LI_AT": session.li_at,
        "LINKEDIN_VOYAGER_JSESSIONID": session.jsessionid,
        "LINKEDIN_VOYAGER_CSRF_TOKEN": session.csrf_token,
    }
    if public_identifier is not None:
        exports["LINKEDIN_PROFILE_PUBLIC_ID"] = public_identifier
    for key, value in exports.items():
        print(f"export {key}={shlex.quote(value)}")
    return 0


def _employment_history_with_fallback(
    *,
    client: LinkedInPostClient,
    source: str,
    public_identifier: str | None,
    voyager_fallback_available: bool,
    browser_profile_fallback_available: bool,
    prefer_voyager: bool,
) -> list[dict[str, object]]:
    if prefer_voyager and voyager_fallback_available and public_identifier is not None:
        return _voyager_employment_with_browser_fallback(
            client=client,
            public_identifier=public_identifier,
            browser_profile_fallback_available=browser_profile_fallback_available,
        )

    try:
        if source == "identity-me":
            official_records = client.get_current_employment()
        else:
            official_records = client.get_employment_history()
    except LinkedInApiError:
        if public_identifier is None or (
            not voyager_fallback_available and not browser_profile_fallback_available
        ):
            raise
        return _voyager_or_browser_employment_history(
            client=client,
            public_identifier=public_identifier,
            voyager_fallback_available=voyager_fallback_available,
            browser_profile_fallback_available=browser_profile_fallback_available,
        )

    if official_records or public_identifier is None:
        return official_records
    if not voyager_fallback_available and not browser_profile_fallback_available:
        return official_records
    return _voyager_or_browser_employment_history(
        client=client,
        public_identifier=public_identifier,
        voyager_fallback_available=voyager_fallback_available,
        browser_profile_fallback_available=browser_profile_fallback_available,
    )


def _voyager_employment_with_browser_fallback(
    *,
    client: LinkedInPostClient,
    public_identifier: str,
    browser_profile_fallback_available: bool,
) -> list[dict[str, object]]:
    try:
        return client.get_voyager_employment_history(public_identifier)
    except LinkedInApiError:
        if not browser_profile_fallback_available:
            raise
        return load_employment_history_from_chrome_profile(public_identifier)


def _voyager_or_browser_employment_history(
    *,
    client: LinkedInPostClient,
    public_identifier: str,
    voyager_fallback_available: bool,
    browser_profile_fallback_available: bool,
) -> list[dict[str, object]]:
    if voyager_fallback_available:
        return _voyager_employment_with_browser_fallback(
            client=client,
            public_identifier=public_identifier,
            browser_profile_fallback_available=browser_profile_fallback_available,
        )
    if browser_profile_fallback_available:
        return load_employment_history_from_chrome_profile(public_identifier)
    return []
