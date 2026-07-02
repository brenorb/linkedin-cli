# lkdn

Small CLI for supported LinkedIn API workflows.

## Scope

This project is intentionally narrow:

- basic organic member or organization post management: create, edit, get, batch-get, list, delete, and reshare
- text, article, image, multi-image, poll, video, and document posts through the official LinkedIn API surfaces
- upload-time video captions and custom thumbnails
- reuse of existing image, video, and document assets by URN
- direct image, video, and document asset inspection by URN or batch-get by URN
- comment reads/writes, reaction reads/writes, and social-metadata reads/comment-state writes on official social-action APIs
- organization access-control discovery and organic-post preflight summaries
- `profile whoami` plus limited employment-data helpers when your app tier and scopes allow it
- stay easy to read and easy to fork

It does not try to automate OAuth in a fragile way. You bring your own access token and author URN.
It does not scrape LinkedIn pages or rely on undocumented web endpoints.

It also does not try to cover every official LinkedIn content surface. Out of scope for this CLI:

- targeted org posts
- dark posts and `adContext`
- sponsored-account media library discovery flows
- organization admin writes

## Install

```bash
uv sync
```

PyPI distribution: `lkdn`

Command names:

- `lkdn`
- `linkedin`

## Usage

Set the required environment variables:

```bash
export LINKEDIN_ACCESS_TOKEN="..."
export LINKEDIN_AUTHOR_URN="urn:li:person:YOUR_ID"
export LINKEDIN_API_VERSION="YYYYMM"
```

Then publish a post:

```bash
uv run lkdn post "Hello from the new Posts API"
```

The legacy `post` create flow still works, and there is now an explicit alias:

```bash
uv run lkdn post create "Hello from the new Posts API"
```

Publish a post with an image:

```bash
uv run lkdn post \
  --image /absolute/path/to/banner.png \
  --alt-text "Bitdevs BSB event banner" \
  "Hello from the new Posts API"
```

Publish a post with a video:

```bash
uv run lkdn post \
  --video /absolute/path/to/clip.mp4 \
  --video-title "Linus on abstraction" \
  "Hello from the new Posts API"
```

Publish a post with a video, captions, and a custom thumbnail:

```bash
uv run lkdn post \
  --video /absolute/path/to/clip.mp4 \
  --video-title "Linus on abstraction" \
  --video-captions /absolute/path/to/clip.vtt \
  --video-thumbnail /absolute/path/to/thumb.png \
  "Hello from the new Posts API"
```

Publish a post with a document:

```bash
uv run lkdn post \
  --document /absolute/path/to/deck.pdf \
  --document-title "June deck" \
  "Hello from the new Posts API"
```

Publish a post with an external article:

```bash
uv run lkdn post \
  --article-url "https://example.com/post" \
  --article-title "Deep systems" \
  --article-description "A long read" \
  --article-thumbnail-urn "urn:li:image:123456" \
  "Worth reading"
```

Or upload the article thumbnail from a local file instead of reusing a URN:

```bash
uv run lkdn post \
  --article-url "https://example.com/post" \
  --article-title "Deep systems" \
  --article-thumbnail /absolute/path/to/thumb.png \
  "Worth reading"
```

Publish a multi-image post:

```bash
uv run lkdn post \
  --multi-image /absolute/path/to/one.png \
  --multi-image /absolute/path/to/two.png \
  --multi-image-alt-text "First image" \
  --multi-image-alt-text "Second image" \
  "Photo dump"
```

Publish a poll post:

```bash
uv run lkdn post \
  --poll-question "Favorite color?" \
  --poll-option "Red" \
  --poll-option "Blue" \
  --poll-duration "THREE_DAYS" \
  "Vote now"
```

Reuse existing image URNs for a multi-image post with per-image alt text:

```bash
uv run lkdn post \
  --multi-image-urn "urn:li:image:123456" \
  --multi-image-urn "urn:li:image:789012" \
  --multi-image-alt-text "First image" \
  --multi-image-alt-text "Second image" \
  "Photo dump"
```

Reshare an existing post:

```bash
uv run lkdn post \
  --reshare-post-urn "urn:li:share:123456789" \
  "Worth reading"
```

Reuse an existing uploaded image or video asset:

```bash
uv run lkdn post \
  --image-urn "urn:li:image:123456" \
  --alt-text "Bitdevs BSB event banner" \
  "Hello from the new Posts API"
```

```bash
uv run lkdn post \
  --video-urn "urn:li:video:123456" \
  --video-title "Linus on abstraction" \
  "Hello from the new Posts API"
```

```bash
uv run lkdn post \
  --document-urn "urn:li:document:123456" \
  --document-title "June deck" \
  "Hello from the new Posts API"
```

You can also pass values as flags:

```bash
uv run lkdn post \
  --access-token "..." \
  --author "urn:li:person:YOUR_ID" \
  --api-version "YYYYMM" \
  "Shipping a tiny CLI."
```

List posts for the configured author:

```bash
uv run lkdn post list
```

List posts for an organization author explicitly:

```bash
uv run lkdn post list \
  --author "urn:li:organization:123456"
```

Read a post by URN:

```bash
uv run lkdn post get "urn:li:share:123456789"
```

Read multiple posts by URN:

```bash
uv run lkdn post batch-get "urn:li:share:123456789" "urn:li:share:987654321"
```

Inspect an image or video asset by URN:

```bash
uv run lkdn image get "urn:li:image:123456"
uv run lkdn document get "urn:li:document:123456"
uv run lkdn video get "urn:li:video:123456"
```

Batch-read multiple assets by URN:

```bash
uv run lkdn image list --id "urn:li:image:123456" --id "urn:li:image:789012"
uv run lkdn document list --id "urn:li:document:123456" --id "urn:li:document:789012"
uv run lkdn video list --id "urn:li:video:123456" --id "urn:li:video:789012"
```

Discover which organizations the authenticated member can act for:

```bash
uv run lkdn organization list
export LINKEDIN_MEMBER_URN="urn:li:person:YOUR_ID"
uv run lkdn organization members "urn:li:organization:123456"
uv run lkdn organization preflight "urn:li:organization:123456"
```

Inspect comments, reactions, and social metadata:

```bash
uv run lkdn comment get "urn:li:share:123456789" "456"
uv run lkdn comment list "urn:li:share:123456789"
uv run lkdn comment batch-get "urn:li:share:123456789" "456" "789"
uv run lkdn comment create "urn:li:share:123456789" --actor "urn:li:person:YOUR_ID" "Hello world"
uv run lkdn comment edit "urn:li:share:123456789" "456" --text "Updated comment"
uv run lkdn comment delete "urn:li:share:123456789" "456"
uv run lkdn reaction get --actor "urn:li:person:YOUR_ID" --entity "urn:li:share:123456789"
uv run lkdn reaction create --actor "urn:li:person:YOUR_ID" --root "urn:li:share:123456789" --type LIKE
uv run lkdn reaction list "urn:li:share:123456789"
uv run lkdn reaction batch-get --key "urn:li:person:YOUR_ID" "urn:li:share:123456789"
uv run lkdn reaction delete --actor "urn:li:person:YOUR_ID" --entity "urn:li:share:123456789"
uv run lkdn social-metadata get "urn:li:share:123456789"
uv run lkdn social-metadata batch-get "urn:li:share:123456789" "urn:li:comment:(urn:li:share:123456789,456)"
uv run lkdn social-metadata set-comments-state "urn:li:share:123456789" --actor "urn:li:person:YOUR_ID" --state CLOSED
```

Inspect the authenticated member identity:

```bash
uv run lkdn profile whoami
uv run lkdn profile whoami --source profile-api
uv run lkdn profile whoami --source identity-me --identity-api-version 202510.03
```

Edit a post's text or content CTA:

```bash
uv run lkdn post edit "urn:li:share:123456789" \
  --text "Edited text" \
  --cta-label LEARN_MORE \
  --landing-page "https://example.com"
```

Update a post lifecycle state through the official partial-update surface:

```bash
uv run lkdn post edit "urn:li:share:123456789" \
  --lifecycle-state PUBLISHED
```

Delete a post by URN:

```bash
uv run lkdn post delete "urn:li:share:123456789"
```

If your post text starts with a reserved action word such as `get`, `list`, or `delete`, use the explicit alias:

```bash
uv run lkdn post create "get ready for BitDevs tonight"
```

Read employment data through official profile APIs:

```bash
uv run lkdn profile employment-history
```

If you also pass a LinkedIn public profile id plus `--browser chrome`, `lkdn` now tries the official API first, then Voyager, then the live Chrome profile page when the API paths are unavailable or empty:

```bash
uv run lkdn profile employment-history --public-id brenorb --browser chrome
```

Use the Verified on LinkedIn `identityMe` endpoint instead:

```bash
uv run lkdn profile employment-history --source identity-me
```

Limit output to a different lookback window:

```bash
uv run lkdn profile employment-history --years 3
```

Use the Voyager path directly only when you want to bypass the official API entirely:

```bash
uv run lkdn profile employment-history --source voyager-private --public-id brenorb
```

Load the Voyager cookies directly from your local Chrome profile instead of exporting them manually:

```bash
uv run lkdn profile employment-history --source voyager-private --browser chrome --public-id brenorb
```

On macOS, the last-resort Chrome page fallback needs `View > Developer > Allow JavaScript from Apple Events` enabled in Chrome.

Or print shell exports for the current browser session:

```bash
uv run lkdn profile voyager-session --browser chrome --public-id brenorb
```

## Docs

- [docs/onboarding.md](docs/onboarding.md) for the full step-by-step setup flow
- [docs/credentials.md](docs/credentials.md) for the local env file layout and variable reference
- [docs/pypi-publishing.md](docs/pypi-publishing.md) for the GitHub-to-PyPI release flow

## LinkedIn requirements

Command support differs depending on whether you are acting as a member or an organization, and whether the command is a write or a read:

| Command | Member author | Organization author | Scope notes |
| --- | --- | --- | --- |
| `post` / `post create` text, article, single image, single video, reshare | Works with `w_member_social` | Works with `w_organization_social` | Organization posting also depends on the authenticated member being allowed to act for that organization. Company-owned image/video uploads are stricter than post creation and may additionally require `ADMINISTRATOR` or `DIRECT_SPONSORED_CONTENT_POSTER`. |
| `post create --multi-image` | Works with `w_member_social` | Works with `w_organization_social` for the post itself | Multi-image is organic only. LinkedIn requires 2 to 20 images. Per-image alt text now works both for uploaded local files and reused image URNs. Company-owned image uploads can still require `ADMINISTRATOR` or `DIRECT_SPONSORED_CONTENT_POSTER`. |
| `post create --multi-image-urn` | Works with `w_member_social` | Works with `w_organization_social` for the post itself | Same scope as multi-image upload, but reuses existing image URNs and supports per-image `altText`. Reusing org-owned image assets still depends on the stricter image-owner rules documented by LinkedIn. |
| `post create --poll ...` | Works with `w_member_social` | Works with `w_organization_social` | Polls are organic only; LinkedIn does not support sponsored poll creation on Posts API. |
| `post create --document ...` | Works with `w_member_social` | Works with `w_organization_social` for the post itself | Organization document uploads are stricter than post creation: LinkedIn documents `ADMIN` or `DIRECT_SPONSORED_CONTENT_POSTER` for company-owned document uploads. |
| `post edit` | Works with `w_member_social` | Works with `w_organization_social` | Uses LinkedIn's Rest.li partial update flow. This CLI supports commentary, lifecycle state, and content CTA updates. |
| `post delete` | Works with `w_member_social` | Works with `w_organization_social` | Same write scope family as create. |
| `post get` | Works only if LinkedIn has granted restricted `r_member_social` | Works only if LinkedIn has granted `r_organization_social` | Self-serve apps often do not have member read access even when posting works. |
| `post batch-get` | Works only if LinkedIn has granted restricted `r_member_social` | Works only if LinkedIn has granted `r_organization_social` | Uses Rest.li batch get on `/rest/posts`. |
| `post list` | Works only if LinkedIn has granted restricted `r_member_social` and you provide a member author URN | Works only if LinkedIn has granted `r_organization_social` and you provide an organization author URN | Uses the official `q=author` finder on `/rest/posts`. |
| `comment get` / `comment list` / `comment batch-get` | Works only if LinkedIn has granted restricted `r_member_social_feed` | Works only if LinkedIn has granted `r_organization_social_feed` | Uses the official Comments API under `/rest/socialActions/.../comments`. If the target URN is a comment URN, `comment list` resolves replies. |
| `comment create` / `comment edit` / `comment delete` | Works with `w_member_social_feed` | Works with `w_organization_social_feed` | Uses the official Comments API write surfaces. Nested replies are supported through `comment create --parent-comment ...`, but LinkedIn does not allow content entities on replies. Mention payloads stay exposed through `--attributes-json`, and `--content-image-urn` is limited to non-reply comments. |
| `reaction create` / `reaction delete` | Works with `w_member_social_feed` | Works with `w_organization_social_feed` | Uses `POST`/`DELETE /rest/reactions...`. These feed scopes are distinct from the Posts API write scopes. |
| `reaction get` / `reaction list` / `reaction batch-get` | Works only if LinkedIn has granted restricted `r_member_social_feed` | Works only if LinkedIn has granted `r_organization_social_feed` | Uses the official Reactions API composite-key read surfaces. |
| `social-metadata get` / `social-metadata batch-get` | Works only if LinkedIn has granted restricted `r_member_social_feed` | Works only if LinkedIn has granted `r_organization_social_feed` | Uses `GET /rest/socialMetadata...` for comment/reaction summary state. |
| `social-metadata set-comments-state` | Works with `w_member_social_feed` | Works with `w_organization_social_feed` | Uses the official Social Metadata partial-update flow to open or close thread comments. This write surface is limited to thread URNs such as shares or ugcPosts, not comment URNs, and LinkedIn deletes existing comments when a thread is switched to `CLOSED`. |
| `image get` / `image list` | Separate from basic member-posting access | Owner/admin gated | This CLI supports direct get and batch-get-by-URN, not owner discovery. LinkedIn documents `/rest/images` reads separately from ordinary member posting and explicitly warns that `w_member_social` alone is not enough for image GETs. |
| `document get` / `document list` | Person-owned reads require owner access | Company-owned reads require stronger org access | LinkedIn documents person-owned document GETs for the owner, company-owned document GETs for `ADMINISTRATOR` or `DIRECT_SPONSORED_CONTENT_POSTER`, and separate sponsored-account document flows. |
| `video get` / `video list` | Owner/admin gated | Owner/admin gated | This CLI supports direct get and batch-get-by-URN, not owner discovery. LinkedIn documents separate video permission checks plus owner/company gating. |
| `organization list` | Uses the authenticated viewer to inspect their own admin access | N/A | Requires `r_organization_admin` or `rw_organization_admin`. Calls the viewer-scoped `/rest/organizationAcls?q=roleAssignee` finder. |
| `organization preflight` | Uses the authenticated viewer plus a member URN for the authorization key | N/A | Requires both ACL discovery access and restricted `rw_organization_admin`, because it combines the viewer-scoped `/rest/organizationAcls?q=roleAssignee` finder with action-level reads on `/rest/organizationAuthorizations/{key}`. The supplied member URN must match the authenticated member, and the result does not verify Posts API OAuth scopes such as `w_organization_social` or `r_organization_social`. |
| `organization members` | Uses the authenticated member to inspect one organization | N/A | Requires `r_organization_admin` or `rw_organization_admin` and calls `/rest/organizationAcls?q=organization`. |
| `profile whoami` | Works with OIDC `userinfo`, the Profile API, or `identity-me` depending on your scopes | N/A | `userinfo` uses `openid profile`, `profile-api` uses `/v2/me`, and `identity-me` needs the Verified on LinkedIn product plus `r_profile_basicinfo`. `identity-me` also uses its own release track instead of the shared Marketing API `YYYYMM` versions. |

Practical consequence: create and delete can work while get and list still return `403` because the read scopes are more restricted than the write scopes.

According to the official LinkedIn docs, member posting requires OAuth 2.0 member authentication, `w_member_social`, and a valid `Linkedin-Version` header in `YYYYMM` format. Organization posting and deletion use the same Posts API surface but switch to organization scopes.

This CLI defaults `LINKEDIN_API_VERSION` to `202606`. If LinkedIn rotates active versions again, update that value or override it with the environment variable.

For Verified on LinkedIn profile reads, this CLI requires an explicit `LINKEDIN_IDENTITY_API_VERSION` or `--identity-api-version`. Use the current Verified on LinkedIn release notes to choose that value; `202510.03` is only the current documented example, not a universal safe default. That endpoint is on its own release track and should not be treated as a generic `YYYYMM` Marketing API version.

For image posts, this project uses LinkedIn's Images API to initialize an upload, uploads the binary to the returned `uploadUrl`, and then creates the post with the returned `urn:li:image:...`.

For video posts, this project uses LinkedIn's Videos API to initialize the upload, uploads each instructed part, finalizes the upload, waits for the asset to become `AVAILABLE`, and then creates the post with the returned `urn:li:video:...`.

If you pass `--video-captions` or `--video-thumbnail`, this project also uploads the WebVTT captions file and/or thumbnail image to the upload URLs returned by the official Videos API before finalizing the asset.

For document posts, this project uses LinkedIn's Documents API to initialize the upload, uploads the binary to the returned `uploadUrl`, waits for the document to become `AVAILABLE`, and then creates the post with the returned `urn:li:document:...`.

For asset inspection, this project exposes direct read and Rest.li batch-get by asset URN. LinkedIn's general image/video discovery surfaces are tied to sponsored or media-library accounts, so this CLI does not pretend that member/org owner listing is broadly available.

For organization preflight, this project uses the official organization ACL finder only as context (`roles`, `states`, `aclApprovedRoles`) and then asks the official `organizationAuthorizations` endpoint for exact organization-authorization answers: `ORGANIC_SHARE_CREATE`, `ORGANIC_SHARE_VIEW_AS_AUTHOR`, `ORGANIC_SHARE_EDIT`, and `ORGANIC_SHARE_DELETE`. The returned booleans therefore reflect org authorization only; they do not prove that the token also has the separate Posts API OAuth scopes needed for `post create`, `post get`, or `post list`. The command still paginates beyond the first ACL page.

It is intentionally not a company-owned media-upload preflight for Images/Videos/Documents. LinkedIn documents stricter asset-upload role gates there, so this command is an organic-post capability helper, not a guarantee that org document/video/image uploads will succeed.

For comments, reactions, and social metadata, this project uses LinkedIn's newer feed-oriented APIs under `/rest/socialActions`, `/rest/reactions`, and `/rest/socialMetadata`. Those commands intentionally track the `*_social_feed` permission family rather than the Posts API's `*_social` scopes.

For organization authors, those feed-write roles are not identical to org post-write roles. LinkedIn documents `w_organization_social_feed` for `ADMINISTRATOR`, `DIRECT_SPONSORED_CONTENT_POSTER`, and `RECRUITING_POSTER`, while org post creation/editing uses a different role mix that includes content-admin privileges.

For commentary mentions and annotations, LinkedIn's current Posts API models them inline inside the commentary text itself rather than as a separate top-level CLI structure, so this project keeps commentary as text input.

For employment data, the official API surface is constrained:

- `GET /rest/identityMe` can return only the member's current position, and only on the Plus tier with the `r_primary_current_experience` scope.
- `GET /rest/identityMe` also requires the Verified on LinkedIn product on the app itself. LinkedIn documents `403 No valid API product assigned` when that product is missing.
- `positions` on the Profile API are part of the older `r_fullprofile` permission set, and LinkedIn documents that access to `r_fullprofile` is closed.
- This means `profile employment-history` is only useful if your app already has the required restricted profile access; otherwise LinkedIn will return limited data or a permission error.
- `--source voyager-private` instead reads `https://www.linkedin.com/voyager/api/identity/profiles/{publicId}/profileView` with LinkedIn web-session cookies (`li_at` plus `JSESSIONID` or a matching CSRF token). That flow is intentionally separate from the official OAuth API surface above.
- `--browser chrome` (or `profile voyager-session`) loads those cookies from a local Chromium-family browser via `browser-cookie3`. On macOS this may prompt for access to the browser cookie store.

Official docs:

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Sign In with LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-06)
- [Comments API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/comments-api?view=li-lms-2026-06)
- [Documents API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api?view=li-lms-2026-06)
- [MultiImage API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/multiimage-post-api?view=li-lms-2026-06)
- [Reactions API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/reactions-api?view=li-lms-2026-06)
- [Social Metadata API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/social-metadata-api?view=li-lms-2026-06)
- [Videos API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api?view=li-lms-2026-06)
- [Organization Access Control by Role](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-access-control-by-role?view=li-lms-2026-06)
- [Organization Authorizations](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-authorizations/organization-authorizations?view=li-lms-2026-06)
- [Sign In with LinkedIn using OpenID Connect](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
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
