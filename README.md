# linkedin-cli

Small CLI for publishing plain-text LinkedIn posts with the current `POST /rest/posts` API.

## Scope

This project is intentionally narrow:

- publish a text post as a member or organization
- use the current LinkedIn `Posts API`
- stay easy to read and easy to fork

It does not try to automate OAuth in a fragile way. You bring your own access token and author URN.

## Install

```bash
uv sync
```

## Usage

Set the required environment variables:

```bash
export LINKEDIN_ACCESS_TOKEN="..."
export LINKEDIN_AUTHOR_URN="urn:li:person:YOUR_ID"
export LINKEDIN_API_VERSION="202505"
```

Then publish a post:

```bash
uv run linkedin-cli post "Hello from the new Posts API"
```

You can also pass values as flags:

```bash
uv run linkedin-cli post \
  --access-token "..." \
  --author "urn:li:person:YOUR_ID" \
  --api-version "202505" \
  "Shipping a tiny CLI."
```

## LinkedIn requirements

According to the official LinkedIn docs, posting on behalf of a member requires:

- OAuth 2.0 member authentication
- the `w_member_social` scope
- a valid `Linkedin-Version` header in `YYYYMM` format

Official docs:

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05)

## Development

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check
```
