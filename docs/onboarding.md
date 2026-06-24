# LinkedIn onboarding

This guide walks through the full member-posting setup for `licli` without exposing your token to anyone else.

It covers:

1. creating a LinkedIn app
2. configuring OAuth
3. exchanging an authorization code for a token
4. deriving `LINKEDIN_AUTHOR_URN`
5. saving local environment variables
6. verifying text, image, and video posts

Employment-data support is separate and more constrained:

- `profile employment-history --source identity-me` uses the Verified on LinkedIn `GET /rest/identityMe` endpoint.
- Current position on `identityMe` requires Plus tier and the `r_primary_current_experience` scope.
- Multi-position history through the older Profile API depends on restricted access to `positions` under `r_fullprofile`, which LinkedIn documents as closed.

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
mkdir -p ~/.config/licli
chmod 700 ~/.config/licli
```

```bash
cat > ~/.config/licli/env.sh <<'EOF'
export LINKEDIN_CLIENT_ID='YOUR_CLIENT_ID'
export LINKEDIN_CLIENT_SECRET='YOUR_CLIENT_SECRET'
export LINKEDIN_REDIRECT_URI='http://localhost:8000/callback'
export LINKEDIN_SCOPE='w_member_social openid profile email'
export LINKEDIN_API_VERSION='202604'
EOF

chmod 600 ~/.config/licli/env.sh
source ~/.config/licli/env.sh
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

printf "export LINKEDIN_ACCESS_TOKEN='%s'\n" "$LINKEDIN_ACCESS_TOKEN" >> ~/.config/licli/env.sh
chmod 600 ~/.config/licli/env.sh
source ~/.config/licli/env.sh
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
  printf "export LINKEDIN_ID_TOKEN='%s'\n" "$LINKEDIN_ID_TOKEN" >> ~/.config/licli/env.sh
  source ~/.config/licli/env.sh
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

printf "export LINKEDIN_AUTHOR_URN='urn:li:person:%s'\n" "$LINKEDIN_PERSON_ID" >> ~/.config/licli/env.sh
source ~/.config/licli/env.sh
```

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

printf "export LINKEDIN_AUTHOR_URN='urn:li:person:%s'\n" "$LINKEDIN_PERSON_ID" >> ~/.config/licli/env.sh
source ~/.config/licli/env.sh
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

## 8. Post a text post

```bash
cd /Users/breno/Documents/code/PROJECTS/linkedin-cli
source ~/.config/licli/env.sh

uv run licli post "Hello from the LinkedIn Posts API"
```

## 9. Post an image post

```bash
cd /Users/breno/Documents/code/PROJECTS/linkedin-cli
source ~/.config/licli/env.sh

uv run licli post \
  --image /absolute/path/to/banner.png \
  --alt-text "Descriptive alt text" \
  "Hello from the LinkedIn Posts API"
```

## 10. Post a video post

```bash
cd /Users/breno/Documents/code/PROJECTS/linkedin-cli
source ~/.config/licli/env.sh

uv run licli post \
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

The `Linkedin-Version` header must be in `YYYYMM` format only.

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
uv run licli post --api-version 202604 ...
```

then your local env file still has an invalid or stale version. Update `~/.config/licli/env.sh`.

## Official docs

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Sign In with LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-06)
- [Videos API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api?view=li-lms-2026-06)
- [URNs and IDs](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/urns?context=linkedin%2Fcontext)
