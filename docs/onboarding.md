# LinkedIn onboarding

This guide walks through the full member-posting setup for `lkdn` without exposing your token to anyone else.

The published PyPI package is `lkdn`. The documented command names are `lkdn` and `linkedin`.

It covers:

1. creating a LinkedIn app
2. configuring OAuth
3. exchanging an authorization code for a token
4. deriving `LINKEDIN_AUTHOR_URN`
5. saving local environment variables
6. verifying text, image, and video posts
7. verifying article, document, and multi-image posts
8. verifying organization preflight and the authenticated member identity

Employment-data support is separate and more constrained:

- `profile employment-history --source identity-me` uses the Verified on LinkedIn `GET /rest/identityMe` endpoint.
- Current position on `identityMe` requires Plus tier and the `r_primary_current_experience` scope.
- Multi-position history through the older Profile API depends on restricted access to `positions` under `r_fullprofile`, which LinkedIn documents as closed.
- `profile employment-history --source voyager-private` uses the logged-in LinkedIn web session against `https://www.linkedin.com/voyager/api/identity/profiles/{publicId}/profileView` and expects `li_at` plus `JSESSIONID` or a matching CSRF token.
- `profile employment-history --source voyager-private --browser chrome` can pull those cookies from a local Chromium-family browser profile when you do not want to export them manually.
- `profile employment-history --public-id <id> --browser chrome` now falls back through official API, Voyager, and finally the live Chrome profile page. On macOS, that last step needs `View > Developer > Allow JavaScript from Apple Events` enabled in Chrome.

Post-management support also splits along member versus organization and read versus write permissions:

- `post` and `post create` use the official Posts API create flow.
- `post --poll-question ...` uses the official organic poll support on the Posts API.
- `post --reshare-post-urn` uses the official Posts API reshare flow.
- `post --article-url ...` uses the official article content support on the Posts API, with either an image URN or a local thumbnail upload.
- `post --document ...` uses the official Documents API upload flow plus post creation.
- `post --multi-image ...` uses the official MultiImage post support on the Posts API after image uploads.
- `post --multi-image-urn ...` reuses existing image URNs and supports per-image alt text.
- `post edit` also exposes lifecycle-state updates on the official partial-update surface.
- `post edit` uses LinkedIn's official Rest.li partial-update flow.
- `post delete` uses the official `DELETE /rest/posts/{encodedPostUrn}` flow.
- `post get`, `post batch-get`, and `post list` use the official read surface on `/rest/posts`, which has stricter permissions than write.
- `comment get`, `comment list`, `comment batch-get`, `comment create`, `comment edit`, and `comment delete` use the official Comments API on `/rest/socialActions/.../comments`.
- `reaction create`, `reaction get`, `reaction list`, `reaction batch-get`, and `reaction delete` use the official Reactions API on `/rest/reactions`.
- `social-metadata get`, `social-metadata batch-get`, and `social-metadata set-comments-state` use the official Social Metadata API on `/rest/socialMetadata`.
- `image get`, `image list`, `document get`, `document list`, `video get`, and `video list` use direct URN reads or Rest.li batch-get on the official asset APIs.
- `organization list` and `organization members` use the official organization ACL finder to discover which orgs the authenticated viewer can act for.
- `organization preflight` uses the ACL finder for context and the official organization-authorizations endpoint for exact org-authorization checks on post-management actions.
- `profile whoami` defaults to OIDC `GET /v2/userinfo` and derives `urn:li:person:{sub}` for convenience.

## Command matrix

| Command | Works for member URNs | Works for organization URNs | Required scope family |
| --- | --- | --- | --- |
| `lkdn post ...` / `lkdn post create ...` | Yes | Yes | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post --poll-question ...` | Yes | Yes | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post --reshare-post-urn ...` | Yes | Yes | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post --article-url ...` | Yes | Yes | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post --document ...` | Yes | Yes, but org-owned uploads are stricter | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post --multi-image ...` | Yes | Yes, for the post itself | `w_member_social` for members, `w_organization_social` for organizations; company-owned image uploads can additionally require `ADMINISTRATOR` or `DIRECT_SPONSORED_CONTENT_POSTER` |
| `lkdn post --multi-image-urn ...` | Yes | Yes, for the post itself | `w_member_social` for members, `w_organization_social` for organizations; org-owned image assets still follow LinkedIn's stricter image-owner rules |
| `lkdn post edit <post-urn>` | Yes | Yes | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post delete <post-urn>` | Yes | Yes | `w_member_social` for members, `w_organization_social` for organizations |
| `lkdn post get <post-urn>` | Only when LinkedIn has granted restricted member read access | Yes, when your app has organization read access | `r_member_social` for members, `r_organization_social` for organizations |
| `lkdn post batch-get <post-urn>...` | Only when LinkedIn has granted restricted member read access | Yes, when your app has organization read access | `r_member_social` for members, `r_organization_social` for organizations |
| `lkdn post list [--author ...]` | Only when LinkedIn has granted restricted member read access | Yes, when your app has organization read access | `r_member_social` for members, `r_organization_social` for organizations |
| `lkdn comment get ...` / `lkdn comment list ...` / `lkdn comment batch-get ...` | Only when LinkedIn has granted restricted member feed-read access | Yes, when your app has organization feed-read access | `r_member_social_feed` for members, `r_organization_social_feed` for organizations |
| `lkdn comment create ...` / `lkdn comment edit ...` / `lkdn comment delete ...` | Yes | Yes | `w_member_social_feed` for members, `w_organization_social_feed` for organizations |
| `lkdn reaction create ...` / `lkdn reaction delete ...` | Yes | Yes | `w_member_social_feed` for members, `w_organization_social_feed` for organizations |
| `lkdn reaction get ...` / `lkdn reaction list ...` / `lkdn reaction batch-get ...` | Only when LinkedIn has granted restricted member feed-read access | Yes, when your app has organization feed-read access | `r_member_social_feed` for members, `r_organization_social_feed` for organizations |
| `lkdn social-metadata get ...` / `lkdn social-metadata batch-get ...` | Only when LinkedIn has granted restricted member feed-read access | Yes, when your app has organization feed-read access | `r_member_social_feed` for members, `r_organization_social_feed` for organizations |
| `lkdn social-metadata set-comments-state ...` | Yes | Yes | `w_member_social_feed` for members, `w_organization_social_feed` for organizations; closing a thread deletes its existing comments |
| `lkdn document get ...` / `lkdn document list ...` | Person-owned reads require owner access | Company-owned reads require stronger org access | LinkedIn documents company-owned document GETs for `ADMINISTRATOR` or `DIRECT_SPONSORED_CONTENT_POSTER`, plus separate sponsored-account flows |
| `lkdn organization list` / `lkdn organization members` | Uses the authenticated viewer/admin context to inspect org access | N/A | `r_organization_admin` or `rw_organization_admin` |
| `lkdn organization preflight` | Uses the authenticated viewer plus a matching member URN to inspect one org's post-management authorization state | N/A | Restricted `rw_organization_admin` plus ACL discovery access; does not verify separate Posts API OAuth scopes |
| `lkdn profile whoami` | Works with OIDC `userinfo`, `profile-api`, or `identity-me` depending on your app access | N/A | `userinfo` uses `openid profile`; `profile-api` uses `/v2/me`; `identity-me` needs the Verified on LinkedIn product plus `r_profile_basicinfo`, and it follows a separate release track from the `YYYYMM` Marketing API versions. |

Notes:

- `LINKEDIN_AUTHOR_URN` is used by `post create` and `post list`. It can be either `urn:li:person:...` or `urn:li:organization:...`.
- `LINKEDIN_MEMBER_URN` is used by `organization preflight`. It should always be `urn:li:person:...` and must match the authenticated viewer.
- `post get` and `post delete` only need the post URN plus a valid access token and API version.
- `comment get`, `comment list`, `comment batch-get`, `reaction ...`, and `social-metadata ...` also work without `LINKEDIN_AUTHOR_URN`; they use explicit URNs in the command itself.
- `comment create`, `comment edit`, and `comment delete` also do not need `LINKEDIN_AUTHOR_URN`.
- `comment create` requires explicit `--actor`.
- `comment create --parent-comment ...` supports replies, but LinkedIn does not allow reply content entities, so `--content-image-urn` is only valid on non-reply comments.
- `comment edit` and `comment delete` accept optional `--actor`, which some org flows require.
- `post edit` supports commentary plus the content CTA fields exposed by LinkedIn's partial-update surface.
- `post batch-get` is the supported multi-read surface for posts. `post list` remains the `q=author` finder and LinkedIn documents `100` as its max count.
- `image list`, `document list`, and `video list` are batch-get-by-URN helpers. They are not owner discovery commands because LinkedIn documents sponsored-account-specific finders for those asset APIs.
- `image get` and `image list` are not implied by basic member-posting access. LinkedIn documents `/rest/images` reads separately and explicitly warns that `w_member_social` alone is not enough for image GETs.
- `document get/list` and `video get/list` also have owner-type-specific rules. Company-owned assets can require `ADMINISTRATOR` or `DIRECT_SPONSORED_CONTENT_POSTER`, while person-owned reads are generally owner-scoped.
- LinkedIn's role model is stricter for company-owned `image`, `document`, and `video` uploads than for plain org post creation. A content admin may be able to create a text org post but still fail on company-owned media uploads.
- `organization preflight` paginates through ACL pages before deciding; it does not stop at the first 100 rows and accepts both `organization` and `organizationTarget` ACL response shapes.
- `organization preflight` now treats ACL rows as inventory only. The returned booleans come from official `organizationAuthorizations` checks for `ORGANIC_SHARE_CREATE`, `ORGANIC_SHARE_VIEW_AS_AUTHOR`, `ORGANIC_SHARE_EDIT`, and `ORGANIC_SHARE_DELETE`.
- The preflight response therefore includes `roles`, `states`, `aclApprovedRoles`, `canCreateOrganicPosts`, `canReadOrganizationPosts`, `canEditOrganicPosts`, and `canDeleteOrganicPosts`.
- Those booleans reflect org authorization only. They do not prove that the token also has `w_organization_social` or `r_organization_social`.
- It is normal for `post create` to work while `post get` or `post list` return `403`, because LinkedIn treats read scopes as more restricted than write scopes.
- The newer comments, reactions, and social-metadata endpoints use the `*_social_feed` scope family, not the Posts API `*_social` scopes.
- `reaction delete` and `social-metadata set-comments-state` are feed-write operations even though they do not create a post.
- `comment edit`, `comment delete`, and `social-metadata set-comments-state` are intentionally stricter about thread targeting than read commands: they require a thread URN, not a comment URN.
- `social-metadata set-comments-state --state CLOSED` is destructive on the official API: LinkedIn deletes the thread's existing comments when it closes comments.
- For organization authors, feed-write roles are not identical to org post-write roles. LinkedIn documents `RECRUITING_POSTER` on the feed-write side, while org post creation/editing uses the separate content-admin/posting role model.
- LinkedIn's current Posts API models mentions and annotations inline in the commentary text itself, so `lkdn` keeps commentary input as text rather than inventing a second mention DSL.
- For comment write operations, `lkdn` exposes the official mention/content payloads through `--attributes-json` and `--content-image-urn` instead of inventing a bespoke mention syntax.
- `organization preflight` is deliberately an organic-post capability helper. It does not promise that company-owned image/video/document uploads will succeed, because LinkedIn documents stricter asset-upload role gates for those APIs.
- If your post text starts with `create`, `get`, `list`, or `delete`, use `lkdn post create "..."` to avoid ambiguity.

## Prerequisites

- a LinkedIn account
- a LinkedIn developer app
- `uv`
- `python3`
- `curl`
- macOS `open` command if you want the browser step launched from the terminal

## 1. Create and configure the LinkedIn app

Open the [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps) and create or select an app.

The app should have:

- `Share on LinkedIn`
- `Sign In with LinkedIn`
- `Verified on LinkedIn` if you plan to use `profile whoami --source identity-me` or `profile employment-history --source identity-me`

The redirect URL should be exactly:

```text
http://localhost:8000/callback
```

Use that exact value. Do not change:

- protocol
- hostname
- port
- path
- trailing slash

If the redirect URI used during token exchange does not exactly match the one used during authorization, LinkedIn will reject the code exchange.

## 2. Prepare a local secrets file

Create a local env file:

```bash
mkdir -p ~/.config/lkdn
chmod 700 ~/.config/lkdn
```

```bash
cat > ~/.config/lkdn/env.sh <<'EOF'
export LINKEDIN_CLIENT_ID='YOUR_CLIENT_ID'
export LINKEDIN_CLIENT_SECRET='YOUR_CLIENT_SECRET'
export LINKEDIN_REDIRECT_URI='http://localhost:8000/callback'
export LINKEDIN_SCOPE='w_member_social openid profile email'
export LINKEDIN_API_VERSION='202606'
export LINKEDIN_IDENTITY_API_VERSION='202510.03'
EOF

chmod 600 ~/.config/lkdn/env.sh
source ~/.config/lkdn/env.sh
```

If you are preparing an organization-author flow, request the organization scopes that your app has actually been approved for. The common split is:

- member create/delete: `w_member_social`
- organization create/delete: `w_organization_social`
- member get/list: restricted `r_member_social`
- organization get/list: `r_organization_social`
- member comment/social-metadata read: restricted `r_member_social_feed`
- organization comment/social-metadata read: `r_organization_social_feed`
- member comment write: `w_member_social_feed`
- organization comment write: `w_organization_social_feed`
- member reaction write: `w_member_social_feed`
- organization reaction write: `w_organization_social_feed`
- member reaction delete and comments-state update: `w_member_social_feed`
- organization reaction delete and comments-state update: `w_organization_social_feed`
- organization ACL discovery: `r_organization_admin` or `rw_organization_admin`
- organization post preflight: restricted `rw_organization_admin`

Do not assume you can simply add the read scopes to a self-serve app; LinkedIn may not grant them.

For organization preflight and discovery, store the member URN separately when convenient:

```bash
export LINKEDIN_MEMBER_URN='urn:li:person:YOUR_ID'
```

## 3. Generate the authorization URL

```bash
STATE=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)

AUTH_URL=$(python3 - <<PY
import os, urllib.parse
params = {
    "response_type": "code",
    "client_id": os.environ["LINKEDIN_CLIENT_ID"],
    "redirect_uri": os.environ["LINKEDIN_REDIRECT_URI"],
    "scope": os.environ["LINKEDIN_SCOPE"],
    "state": "$STATE",
}
print("https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params))
PY
)

printf '%s\n' "$AUTH_URL"
open "$AUTH_URL"
```

## 4. Authorize and capture the code

After login and consent, LinkedIn will redirect the browser to something like:

```text
http://localhost:8000/callback?code=AQ...&state=...
```

The browser may show an error page because nothing is listening on `localhost:8000`. That is fine.

Copy the `code` value from the browser address bar immediately.

Important:

- the code is single-use
- the code expires quickly
- do not reuse an old code

## 5. Exchange the code for an access token

Run:

```bash
read -r LINKEDIN_AUTH_CODE

TOKEN_JSON=$(curl -sS -X POST 'https://www.linkedin.com/oauth/v2/accessToken' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=authorization_code' \
  --data-urlencode "code=$LINKEDIN_AUTH_CODE" \
  --data-urlencode "redirect_uri=$LINKEDIN_REDIRECT_URI" \
  --data-urlencode "client_id=$LINKEDIN_CLIENT_ID" \
  --data-urlencode "client_secret=$LINKEDIN_CLIENT_SECRET")

printf '%s\n' "$TOKEN_JSON" | python3 -m json.tool
```

You should get a JSON response containing:

- `access_token`
- `expires_in`
- `scope`
- `token_type`
- often `id_token`

Save the access token locally:

```bash
LINKEDIN_ACCESS_TOKEN=$(printf '%s' "$TOKEN_JSON" | python3 - <<'PY'
import sys, json
print(json.load(sys.stdin)["access_token"])
PY
)

printf "export LINKEDIN_ACCESS_TOKEN='%s'\n" "$LINKEDIN_ACCESS_TOKEN" >> ~/.config/lkdn/env.sh
chmod 600 ~/.config/lkdn/env.sh
source ~/.config/lkdn/env.sh
```

If `id_token` is present, save it too:

```bash
LINKEDIN_ID_TOKEN=$(printf '%s' "$TOKEN_JSON" | python3 - <<'PY'
import sys, json
data = json.load(sys.stdin)
print(data.get("id_token", ""))
PY
)

if [ -n "$LINKEDIN_ID_TOKEN" ]; then
  printf "export LINKEDIN_ID_TOKEN='%s'\n" "$LINKEDIN_ID_TOKEN" >> ~/.config/lkdn/env.sh
  source ~/.config/lkdn/env.sh
fi
```

## 6. Derive the author URN

### Preferred path: use `userinfo`

Use:

```bash
curl -sS https://api.linkedin.com/v2/userinfo \
  -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" \
  | python3 -m json.tool
```

Look for the `sub` field.

Then save it:

```bash
LINKEDIN_PERSON_ID=$(curl -sS https://api.linkedin.com/v2/userinfo \
  -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" \
  | python3 - <<'PY'
import sys, json
print(json.load(sys.stdin)["sub"])
PY
)

printf "export LINKEDIN_AUTHOR_URN='urn:li:person:%s'\n" "$LINKEDIN_PERSON_ID" >> ~/.config/lkdn/env.sh
source ~/.config/lkdn/env.sh
```

### Organization author URNs

For `post create` and `post list`, you can also set:

```bash
export LINKEDIN_AUTHOR_URN='urn:li:organization:123456'
```

Use this only when the access token is authorized to act on behalf of that organization.

### Fallback path: use `id_token`

If `userinfo` is not convenient, extract `sub` from the OIDC `id_token`:

```bash
python3 - <<'PY'
import os, json, base64
token = os.environ["LINKEDIN_ID_TOKEN"]
payload = token.split(".")[1]
payload += "=" * (-len(payload) % 4)
data = json.loads(base64.urlsafe_b64decode(payload))
print(json.dumps(data, indent=2))
PY
```

Then:

```bash
LINKEDIN_PERSON_ID=$(python3 - <<'PY'
import os, json, base64
token = os.environ["LINKEDIN_ID_TOKEN"]
payload = token.split(".")[1]
payload += "=" * (-len(payload) % 4)
data = json.loads(base64.urlsafe_b64decode(payload))
print(data["sub"])
PY
)

printf "export LINKEDIN_AUTHOR_URN='urn:li:person:%s'\n" "$LINKEDIN_PERSON_ID" >> ~/.config/lkdn/env.sh
source ~/.config/lkdn/env.sh
```

## 7. Verify the final environment

```bash
printf '%s\n' "$LINKEDIN_AUTHOR_URN"
test -n "$LINKEDIN_ACCESS_TOKEN" && echo "LINKEDIN_ACCESS_TOKEN set"
printf '%s\n' "$LINKEDIN_API_VERSION"
```

Expected:

- author URN looks like `urn:li:person:...`
- token is set
- API version is a six-digit `YYYYMM`
- identity API version, if set, may be a dotted Verified on LinkedIn release such as `202510.03`

You can also verify the authenticated member identity directly:

```bash
uv run lkdn profile whoami
```

That command calls OIDC `userinfo` by default and prints a derived `person_urn` that you can reuse as `LINKEDIN_AUTHOR_URN` for member posts.

If your app has Profile API access, you can use the older identity source directly:

```bash
uv run lkdn profile whoami --source profile-api
```

If your app has Verified on LinkedIn profile access, you can also force the alternate source:

```bash
uv run lkdn profile whoami --source identity-me --identity-api-version 202510.03
```

If LinkedIn returns `403 No valid API product assigned`, add the `Verified on LinkedIn` product to the app; scopes alone are not enough for `/rest/identityMe`.

It does not list organizations you can act for. LinkedIn treats that as an organization-admin concern, not as a basic identity concern.

## 8. Post a text post

```bash
cd /Users/breno/Documents/code/PROJECTS/linkedin-cli
source ~/.config/lkdn/env.sh

uv run lkdn post "Hello from the LinkedIn Posts API"
```

## 9. Post an image post

```bash
cd /Users/breno/Documents/code/PROJECTS/linkedin-cli
source ~/.config/lkdn/env.sh

uv run lkdn post \
  --image /absolute/path/to/banner.png \
  --alt-text "Descriptive alt text" \
  "Hello from the LinkedIn Posts API"
```

## 10. Post a video post

```bash
cd /Users/breno/Documents/code/PROJECTS/linkedin-cli
source ~/.config/lkdn/env.sh

uv run lkdn post \
  --video /absolute/path/to/clip.mp4 \
  --video-title "Linus on abstraction" \
  "Hello from the LinkedIn Posts API"
```

## Troubleshooting

### `invalid_request` during token exchange

Example:

```text
Unable to retrieve access token: appid/redirect uri/code verifier does not match authorization code. Or authorization code expired.
```

Common causes:

- redirect URI mismatch
- reused code
- expired code
- mixed PKCE / non-PKCE flow

Fix:

- start from a fresh authorization URL
- use a new code immediately
- verify the redirect URI exactly matches the one configured in the app

### `ACCESS_DENIED ... me.GET.NO_VERSION`

Using `/v2/me` may fail depending on product/scopes and versioning.

Use:

- `/v2/userinfo`
- or the `id_token`

to derive the member identifier instead.

### `426 Requested version ... is not active`

The shared Marketing API `Linkedin-Version` header must be in `YYYYMM` format.

Exception:

- Verified on LinkedIn `/rest/identityMe` uses its own release track and may require a dotted version such as `202510.03`

Bad:

```text
20250501
```

Good:

```text
202604
```

or another currently active `YYYYMM`.

If you hit this error:

- remove the day suffix
- pick a currently active `YYYYMM`
- update `LINKEDIN_API_VERSION`

### Posting works only when overriding `--api-version`

If the CLI works with:

```bash
uv run lkdn post --api-version 202604 ...
```

then your local env file still has an invalid or stale version. Update `~/.config/lkdn/env.sh`.

## Official docs

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Sign In with LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-06)
- [Videos API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api?view=li-lms-2026-06)
- [URNs and IDs](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/urns?context=linkedin%2Fcontext)
