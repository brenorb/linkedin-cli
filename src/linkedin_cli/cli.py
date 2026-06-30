from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Protocol

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
    def create_video_post(
        self,
        *,
        author: str,
        commentary: str,
        visibility: str,
        video_path: Path,
        title: str | None = None,
    ) -> object: ...
    def get_employment_history(self) -> list[dict[str, object]]: ...
    def get_current_employment(self) -> list[dict[str, object]]: ...


class ClientFactory(Protocol):
    def __call__(self, *, access_token: str, api_version: str) -> LinkedInPostClient: ...


def build_parser(*, prog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Publish LinkedIn posts and inspect supported profile data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    post_parser = subparsers.add_parser("post", help="Publish a text post")
    post_parser.add_argument("commentary", nargs="+", help="Post text")
    post_parser.add_argument("--image", type=Path, help="Path to an image to upload and attach")
    post_parser.add_argument("--alt-text", help="Alt text for the uploaded image")
    post_parser.add_argument("--video", type=Path, help="Path to a video to upload and attach")
    post_parser.add_argument("--video-title", help="Title for the uploaded video")
    post_parser.add_argument("--author", help="Author URN, for example urn:li:person:abc123")
    post_parser.add_argument("--access-token", help="OAuth access token")
    post_parser.add_argument(
        "--api-version",
        default=None,
        help=f"LinkedIn API version in YYYYMM format. Defaults to {DEFAULT_API_VERSION}.",
    )
    post_parser.add_argument("--visibility", default="PUBLIC", help="LinkedIn post visibility")

    profile_parser = subparsers.add_parser("profile", help="Read supported LinkedIn profile data")
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command", required=True)
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
    parser = build_parser(prog=Path(sys.argv[0]).name if argv is None else None)
    args = parser.parse_args(argv)
    environment = dict(os.environ if env is None else env)

    if args.command == "post":
        return _run_post(args, environment, client_factory or _default_client_factory)
    if args.command == "profile" and args.profile_command == "employment-history":
        return _run_employment_history(args, environment, client_factory or _default_client_factory)

    parser.error(f"unknown command: {args.command}")
    return 2


def _run_post(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    access_token = args.access_token or env.get("LINKEDIN_ACCESS_TOKEN")
    author = args.author or env.get("LINKEDIN_AUTHOR_URN")
    api_version = args.api_version or env.get("LINKEDIN_API_VERSION") or DEFAULT_API_VERSION

    missing: list[str] = []
    if not access_token:
        missing.append("access token")
    if not author:
        missing.append("author URN")

    if missing:
        print(f"Missing required configuration: {', '.join(missing)}.", file=sys.stderr)
        return 2

    if args.alt_text and not args.image:
        print("Missing required configuration: alt text requires an image.", file=sys.stderr)
        return 2

    if args.image and args.video:
        print("Missing required configuration: choose either an image or a video, not both.", file=sys.stderr)
        return 2

    client = client_factory(access_token=access_token, api_version=api_version)
    try:
        commentary = " ".join(args.commentary)
        if args.image:
            result = client.create_image_post(
                author=author,
                commentary=commentary,
                visibility=args.visibility,
                image_path=args.image,
                alt_text=args.alt_text,
            )
        elif args.video:
            result = client.create_video_post(
                author=author,
                commentary=commentary,
                visibility=args.visibility,
                video_path=args.video,
                title=args.video_title,
            )
        else:
            result = client.create_text_post(
                author=author,
                commentary=commentary,
                visibility=args.visibility,
            )
    except LinkedInApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    post_id = getattr(result, "post_id", None)
    if post_id:
        print(f"Created post {post_id}")
    else:
        print("Created post")
    return 0


def _run_employment_history(
    args: argparse.Namespace,
    env: Mapping[str, str],
    client_factory: ClientFactory,
) -> int:
    access_token = env.get("LINKEDIN_ACCESS_TOKEN")
    api_version = env.get("LINKEDIN_API_VERSION") or DEFAULT_API_VERSION

    if not access_token:
        print("Missing required configuration: access token.", file=sys.stderr)
        return 2

    client = client_factory(access_token=access_token, api_version=api_version)
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
        close = getattr(client, "close", None)
        if callable(close):
            close()

    print(json.dumps(filtered, indent=2))
    return 0


def _default_client_factory(*, access_token: str, api_version: str) -> LinkedInClient:
    return LinkedInClient(access_token=access_token, api_version=api_version)
