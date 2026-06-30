# licli

Small CLI for supported LinkedIn API workflows.

## Scope

This project is intentionally narrow:

- basic organic member or organization post management: create, edit, get, batch-get, list, and delete
- image and video posting through the official upload flows
- reuse of existing image and video assets by URN
- direct image and video asset inspection by URN or batch-get by URN
- `profile whoami` plus limited employment-data helpers when your app tier and scopes allow it
- stay easy to read and easy to fork

It does not try to automate OAuth in a fragile way. You bring your own access token and author URN.
It does not scrape LinkedIn pages or rely on undocumented web endpoints.

It also does not try to cover every official LinkedIn content surface. Out of scope for this CLI:

- article or document posts
- polls
- multi-image or carousel posts
- reshares
- targeted org posts
- dark posts and `adContext`
- sponsored-account media library discovery flows
- organization admin discovery or authorization checks

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
uv run licli post "Hello from the new Posts API"
```

The legacy `post` create flow still works, and there is now an explicit alias:

```bash
uv run licli post create "Hello from the new Posts API"
```

Publish a post with an image:

```bash
uv run licli post \
  --image /absolute/path/to/banner.png \
  --alt-text "Bitdevs BSB event banner" \
  "Hello from the new Posts API"
```

Publish a post with a video:

```bash
uv run licli post \
  --video /absolute/path/to/clip.mp4 \
  --video-title "Linus on abstraction" \
  "Hello from the new Posts API"
```

Reuse an existing uploaded image or video asset:

```bash
uv run licli post \
  --image-urn "urn:li:image:123456" \
  --alt-text "Bitdevs BSB event banner" \
  "Hello from the new Posts API"
```

```bash
uv run licli post \
  --video-urn "urn:li:video:123456" \
  --video-title "Linus on abstraction" \
  "Hello from the new Posts API"
```

You can also pass values as flags:

```bash
uv run licli post \
  --access-token "..." \
  --author "urn:li:person:YOUR_ID" \
  --api-version "YYYYMM" \
  "Shipping a tiny CLI."
```

List posts for the configured author:

```bash
uv run licli post list
```

List posts for an organization author explicitly:

```bash
uv run licli post list \
  --author "urn:li:organization:123456"
```

Read a post by URN:

```bash
uv run licli post get "urn:li:share:123456789"
```

Read multiple posts by URN:

```bash
uv run licli post batch-get "urn:li:share:123456789" "urn:li:share:987654321"
```

Inspect an image or video asset by URN:

```bash
uv run licli image get "urn:li:image:123456"
uv run licli video get "urn:li:video:123456"
```

Batch-read multiple assets by URN:

```bash
uv run licli image list --id "urn:li:image:123456" --id "urn:li:image:789012"
uv run licli video list --id "urn:li:video:123456" --id "urn:li:video:789012"
```

Inspect the authenticated member identity:

```bash
uv run licli profile whoami
```

Edit a post's text or content CTA:

```bash
uv run licli post edit "urn:li:share:123456789" \
  --text "Edited text" \
  --cta-label LEARN_MORE \
  --landing-page "https://example.com"
```

Delete a post by URN:

```bash
uv run licli post delete "urn:li:share:123456789"
```

If your post text starts with a reserved action word such as `get`, `list`, or `delete`, use the explicit alias:

```bash
uv run licli post create "get ready for BitDevs tonight"
```

Read employment data through official profile APIs:

```bash
uv run licli profile employment-history
```

Use the Verified on LinkedIn `identityMe` endpoint instead:

```bash
uv run licli profile employment-history --source identity-me
```

Limit output to a different lookback window:

```bash
uv run licli profile employment-history --years 3
```

## Docs

- [docs/onboarding.md](docs/onboarding.md) for the full step-by-step setup flow
- [docs/credentials.md](docs/credentials.md) for the local env file layout and variable reference
- [docs/pypi-publishing.md](docs/pypi-publishing.md) for the GitHub-to-PyPI release flow

## LinkedIn requirements

Command support differs depending on whether you are acting as a member or an organization, and whether the command is a write or a read:

| Command | Member author | Organization author | Scope notes |
| --- | --- | --- | --- |
| `post` / `post create` | Works with `w_member_social` | Works with `w_organization_social` | Organization posting also depends on the authenticated member being allowed to act for that organization. |
| `post edit` | Works with `w_member_social` | Works with `w_organization_social` | Uses LinkedIn's Rest.li partial update flow. This CLI supports commentary and content CTA updates. |
| `post delete` | Works with `w_member_social` | Works with `w_organization_social` | Same write scope family as create. |
| `post get` | Works only if LinkedIn has granted restricted `r_member_social` | Works only if LinkedIn has granted `r_organization_social` | Self-serve apps often do not have member read access even when posting works. |
| `post batch-get` | Works only if LinkedIn has granted restricted `r_member_social` | Works only if LinkedIn has granted `r_organization_social` | Uses Rest.li batch get on `/rest/posts`. |
| `post list` | Works only if LinkedIn has granted restricted `r_member_social` and you provide a member author URN | Works only if LinkedIn has granted `r_organization_social` and you provide an organization author URN | Uses the official `q=author` finder on `/rest/posts`. |
| `image get` / `image list` | Depends on image read access; member write tokens may still fail on reads | Owner/admin gated | This CLI supports direct get and batch-get-by-URN, not owner discovery. |
| `video get` / `video list` | Owner/admin gated | Owner/admin gated | This CLI supports direct get and batch-get-by-URN, not owner discovery. |
| `profile whoami` | Works with OIDC `userinfo`; `identity-me` needs extra profile scopes | N/A | `userinfo` is the default and returns a derived `urn:li:person:...`. |

Practical consequence: create and delete can work while get and list still return `403` because the read scopes are more restricted than the write scopes.

According to the official LinkedIn docs, member posting requires OAuth 2.0 member authentication, `w_member_social`, and a valid `Linkedin-Version` header in `YYYYMM` format. Organization posting and deletion use the same Posts API surface but switch to organization scopes.

This CLI defaults `LINKEDIN_API_VERSION` to `202606`. If LinkedIn rotates active versions again, update that value or override it with the environment variable.

For image posts, this project uses LinkedIn's Images API to initialize an upload, uploads the binary to the returned `uploadUrl`, and then creates the post with the returned `urn:li:image:...`.

For video posts, this project uses LinkedIn's Videos API to initialize the upload, uploads each instructed part, finalizes the upload, waits for the asset to become `AVAILABLE`, and then creates the post with the returned `urn:li:video:...`.

For asset inspection, this project exposes direct read and Rest.li batch-get by asset URN. LinkedIn's general image/video discovery surfaces are tied to sponsored or media-library accounts, so this CLI does not pretend that member/org owner listing is broadly available.

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

Run type checks:

```bash
uv run ty check
```
