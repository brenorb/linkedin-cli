# linkedin-cli

Small CLI for supported LinkedIn API workflows.

## Scope

This project is intentionally narrow:

- publish a text post as a member or organization
- publish an image post as a member or organization
- publish a video post as a member or organization
- read employment data from official LinkedIn profile APIs when your app tier and scopes allow it
- use the current LinkedIn `Posts API`
- stay easy to read and easy to fork

It does not try to automate OAuth in a fragile way. You bring your own access token and author URN.
It does not scrape LinkedIn pages or rely on undocumented web endpoints.

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

Publish a post with a video:

```bash
uv run linkedin-cli post \
  --video /absolute/path/to/clip.mp4 \
  --video-title "Linus on abstraction" \
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

Read employment data through official profile APIs:

```bash
uv run linkedin-cli profile employment-history
```

Use the Verified on LinkedIn `identityMe` endpoint instead:

```bash
uv run linkedin-cli profile employment-history --source identity-me
```

Limit output to a different lookback window:

```bash
uv run linkedin-cli profile employment-history --years 3
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

For video posts, this project uses LinkedIn's Videos API to initialize the upload, uploads each instructed part, finalizes the upload, waits for the asset to become `AVAILABLE`, and then creates the post with the returned `urn:li:video:...`.

For employment data, the official API surface is constrained:

- `GET /rest/identityMe` can return only the member's current position, and only on the Plus tier with the `r_primary_current_experience` scope.
- `positions` on the Profile API are part of the older `r_fullprofile` permission set, and LinkedIn documents that access to `r_fullprofile` is closed.
- This means `profile employment-history` is only useful if your app already has the required restricted profile access; otherwise LinkedIn will return limited data or a permission error.

Official docs:

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Sign In with LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-06)
- [Videos API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api?view=li-lms-2026-06)
- [Profile API](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api)
- [Full Profile Fields](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/profile/full-profile)
- [Profile Details API (`/identityMe`)](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/verified-on-linkedin/api-reference/identity-me)
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
