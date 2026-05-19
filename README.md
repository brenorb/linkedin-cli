# linkedin-cli

Small CLI for publishing LinkedIn posts with the current `POST /rest/posts` API.

## Scope

This project is intentionally narrow:

- publish a text post as a member or organization
- publish an image post as a member or organization
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
export LINKEDIN_API_VERSION="YYYYMM"
```

Then publish a post:

```bash
uv run linkedin-cli post "Hello from the new Posts API"
```

Publish a post with an image:

```bash
uv run linkedin-cli post \
  --image /absolute/path/to/banner.png \
  --alt-text "Bitdevs BSB event banner" \
  "Hello from the new Posts API"
```

You can also pass values as flags:

```bash
uv run linkedin-cli post \
  --access-token "..." \
  --author "urn:li:person:YOUR_ID" \
  --api-version "YYYYMM" \
  "Shipping a tiny CLI."
```

## Docs

- [docs/onboarding.md](docs/onboarding.md) for the full step-by-step setup flow
- [docs/credentials.md](docs/credentials.md) for the local env file layout and variable reference

## LinkedIn requirements

According to the official LinkedIn docs, posting on behalf of a member requires:

- OAuth 2.0 member authentication
- the `w_member_social` scope
- a valid `Linkedin-Version` header in `YYYYMM` format

For image posts, this project uses LinkedIn's Images API to initialize an upload, uploads the binary to the returned `uploadUrl`, and then creates the post with the returned `urn:li:image:...`.

Official docs:

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Sign In with LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05)
- [URNs and IDs](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/urns?context=linkedin%2Fcontext)

## Development

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check
```
