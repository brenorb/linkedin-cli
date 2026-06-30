from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, Protocol, cast

from linkedin_cli.client import DEFAULT_API_VERSION, LinkedInApiError, LinkedInClient
from linkedin_cli.employment import filter_employment_history


class LinkedInPostClient(Protocol):
    def create_text_post(self, *, author: str, commentary: str, visibility: str) -> object: ...
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
    ) -> None: ...
    def get_image(self, image_urn: str) -> dict[str, Any]: ...
    def batch_get_images(self, image_urns: list[str]) -> dict[str, Any]: ...
    def get_video(self, video_urn: str) -> dict[str, Any]: ...
    def batch_get_videos(self, video_urns: list[str]) -> dict[str, Any]: ...
    def get_userinfo(self) -> dict[str, Any]: ...
    def get_identity_profile(self) -> dict[str, Any]: ...
    def get_employment_history(self) -> list[dict[str, object]]: ...
    def get_current_employment(self) -> list[dict[str, object]]: ...


ClientFactory = Callable[..., object]

POST_ACTIONS = {"create", "get", "list", "delete", "edit", "batch-get"}
POST_VIEW_CONTEXTS = ("AUTHOR", "READER")
POST_SORT_OPTIONS = ("LAST_MODIFIED", "CREATED")
POST_LIST_MAX_COUNT = 100


def build_parser(*, explicit_post_actions: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="licli",
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

    profile_parser = subparsers.add_parser("profile", help="Read supported LinkedIn profile data")
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command", required=True)
    whoami_parser = profile_subparsers.add_parser("whoami", help="Read the authenticated member profile")
    whoami_parser.add_argument(
        "--source",
        choices=("userinfo", "identity-me"),
        default="userinfo",
        help="Official LinkedIn API source.",
    )
    employment_parser = profile_subparsers.add_parser(
        "employment-history",
        help="Read employment data from supported LinkedIn profile APIs",
    )
    employment_parser.add_argument(
        "--source",
        choices=("profile-api", "identity-me"),
        default="profile-api",
        help="Official LinkedIn API source.",
    )
    employment_parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Return only employment records overlapping the last N years.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    client_factory: ClientFactory | None = None,
) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser(explicit_post_actions=_uses_explicit_post_action(argv_list))
    args = parser.parse_args(argv_list)
    environment = dict(os.environ if env is None else env)

    if args.command == "post":
        return _run_post(args, environment, client_factory or _default_client_factory)
    if args.command == "image":
        return _run_image(args, environment, client_factory or _default_client_factory)
    if args.command == "video":
        return _run_video(args, environment, client_factory or _default_client_factory)
    if args.command == "profile" and args.profile_command == "whoami":
        return _run_profile_whoami(args, environment, client_factory or _default_client_factory)
    if args.command == "profile" and args.profile_command == "employment-history":
        return _run_employment_history(args, environment, client_factory or _default_client_factory)

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

    if post_command == "create" and args.image and args.image_urn:
        print("Missing required configuration: choose either an image path or an image URN, not both.", file=sys.stderr)
        return 2

    if post_command == "create" and args.video and args.video_urn:
        print("Missing required configuration: choose either a video path or a video URN, not both.", file=sys.stderr)
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
    access_token = _configured_value(None, env.get("LINKEDIN_ACCESS_TOKEN"))
    api_version = _configured_value(None, env.get("LINKEDIN_API_VERSION")) or DEFAULT_API_VERSION

    if access_token is None:
        print("Missing required configuration: access token.", file=sys.stderr)
        return 2

    client = cast(
        LinkedInPostClient,
        client_factory(access_token=access_token, api_version=api_version),
    )
    try:
        if args.source == "identity-me":
            records = client.get_current_employment()
        else:
            records = client.get_employment_history()
        filtered = filter_employment_history(records, years=args.years, today=date.today())
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        _close_client(client)

    print(json.dumps(filtered, indent=2))
    return 0


def _add_post_create_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("commentary", nargs="+", help="Post text")
    parser.add_argument("--image", type=Path, help="Path to an image to upload and attach")
    parser.add_argument("--image-urn", help="Existing LinkedIn image asset URN to reuse")
    parser.add_argument("--alt-text", help="Alt text for the uploaded image")
    parser.add_argument("--video", type=Path, help="Path to a video to upload and attach")
    parser.add_argument("--video-urn", help="Existing LinkedIn video asset URN to reuse")
    parser.add_argument("--video-title", help="Title for the uploaded video")
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
        )
    )


def _post_create_has_conflicting_media(args: argparse.Namespace) -> bool:
    has_image = bool(args.image or args.image_urn)
    has_video = bool(args.video or args.video_urn)
    return has_image and has_video


def _configured_value(cli_value: str | None, env_value: str | None) -> str | None:
    for value in (cli_value, env_value):
        if value is not None and value != "":
            return value
    return None


def _create_post(
    client: LinkedInPostClient,
    args: argparse.Namespace,
    *,
    author: str,
) -> object:
    commentary = " ".join(args.commentary)
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
    if args.video:
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
    if access_token is None:
        print("Missing required configuration: access token.", file=sys.stderr)
        return None
    return cast(
        LinkedInPostClient,
        client_factory(access_token=access_token, api_version=api_version or DEFAULT_API_VERSION),
    )


def _close_client(client: LinkedInPostClient) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


def _default_client_factory(*, access_token: str, api_version: str) -> LinkedInClient:
    return LinkedInClient(access_token=access_token, api_version=api_version)
