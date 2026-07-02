# Credentials and local environment

This project expects three environment variables at runtime:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`
- `LINKEDIN_API_VERSION`

Some commands also use:

- `LINKEDIN_MEMBER_URN` for `organization preflight`

Recommended local setup:

```bash
mkdir -p ~/.config/lkdn
chmod 700 ~/.config/lkdn
```

Store secrets in a local shell file that is not part of the repo:

```bash
cat > ~/.config/lkdn/env.sh <<'EOF'
export LINKEDIN_CLIENT_ID='YOUR_CLIENT_ID'
export LINKEDIN_CLIENT_SECRET='YOUR_CLIENT_SECRET'
export LINKEDIN_REDIRECT_URI='http://localhost:8000/callback'
export LINKEDIN_SCOPE='w_member_social openid profile email'

# Fill these after completing OAuth.
export LINKEDIN_ACCESS_TOKEN=''
export LINKEDIN_AUTHOR_URN=''
export LINKEDIN_MEMBER_URN=''

# Must be YYYYMM, not YYYYMMDD.
export LINKEDIN_API_VERSION='202606'

# Required for `--source identity-me`: Verified on LinkedIn `/rest/identityMe` release track.
export LINKEDIN_IDENTITY_API_VERSION='202510.03'

# Required for `profile employment-history --source voyager-private`.
export LINKEDIN_PROFILE_PUBLIC_ID=''
export LINKEDIN_VOYAGER_LI_AT=''
export LINKEDIN_VOYAGER_JSESSIONID=''
# Optional if `LINKEDIN_VOYAGER_JSESSIONID` is set; otherwise provide it explicitly.
export LINKEDIN_VOYAGER_CSRF_TOKEN=''
# Optional browser-backed session loading for voyager-private.
export LINKEDIN_VOYAGER_BROWSER=''
export LINKEDIN_VOYAGER_COOKIE_FILE=''
EOF

chmod 600 ~/.config/lkdn/env.sh
```

Load it when needed:

```bash
source ~/.config/lkdn/env.sh
```

Good storage options:

- `~/.config/lkdn/env.sh`
- `~/.zshrc` if you want values loaded in every shell
- another local secrets file that you source manually

Avoid storing tokens in tracked repo files.

## Notes

- `LINKEDIN_AUTHOR_URN` can look like `urn:li:person:abc123` or `urn:li:organization:123456`, depending on whether `post create` or `post list` should act as a member or organization.
- `LINKEDIN_MEMBER_URN` should stay in member form, for example `urn:li:person:abc123`, because `organization preflight` uses it to build the official `organizationAuthorizations` impersonator key. It must match the authenticated viewer.
- `post get` and `post delete` do not read `LINKEDIN_AUTHOR_URN`; they only need the post URN plus `LINKEDIN_ACCESS_TOKEN`.
- `comment get`, `reaction create`, and `social-metadata get` also do not read `LINKEDIN_AUTHOR_URN`.
- `uv run lkdn profile whoami` is the fastest way in this repo to derive the member-form `LINKEDIN_AUTHOR_URN` from OIDC `userinfo`.
- `uv run lkdn organization preflight "urn:li:organization:123456"` is the fastest way in this repo to confirm whether the current member URN can create, read-as-author, edit, or delete organic org posts.
- `LINKEDIN_API_VERSION` must use `YYYYMM`.
- A value such as `20250501` is invalid and will cause `426 Requested version ... is not active`.
- Active versions change over time. If a version stops working, update it to a currently active `YYYYMM`.
- `LINKEDIN_IDENTITY_API_VERSION` is separate from the Marketing API versioning above. `identity-me` is on the Verified on LinkedIn release track, uses dotted versions such as `202510.03`, and should be chosen from current Verified on LinkedIn release notes rather than guessed from the Marketing API month.
- The example `LINKEDIN_SCOPE='w_member_social openid profile email'` is enough for basic member posting plus `profile whoami`.
- `post get`, `post list`, and `post batch-get` use the older Posts API read scopes: restricted `r_member_social` for members or `r_organization_social` for organizations.
- `comment get` and `social-metadata get` use the feed-read scopes instead: restricted `r_member_social_feed` for members or `r_organization_social_feed` for organizations.
- `reaction create` uses the feed-write scopes: `w_member_social_feed` for members or `w_organization_social_feed` for organizations.
- `comment list`, `comment batch-get`, `reaction get`, `reaction list`, `reaction batch-get`, and `social-metadata batch-get` stay in the same feed-read scope family as above.
- `reaction delete` and `social-metadata set-comments-state` stay in the same feed-write scope family as above.
- `comment create`, `comment edit`, and `comment delete` use the feed-write scopes from the official Comments API: `w_member_social_feed` for members or `w_organization_social_feed` for organizations.
- For org writers, LinkedIn's feed-write roles are not identical to org post-write roles. `RECRUITING_POSTER` can have feed-write access while `CONTENT_ADMIN` is documented on the Posts API side instead.
- `organization list` and `organization members` use organization-admin discovery scopes: `r_organization_admin` or `rw_organization_admin`.
- `organization preflight` additionally uses restricted `rw_organization_admin`, because LinkedIn exposes the action-level answers through `GET /rest/organizationAuthorizations/{key}` rather than through ACL rows alone.
- `profile whoami --source identity-me` uses `/rest/identityMe`, which requires the Verified on LinkedIn product on the app plus `r_profile_basicinfo` instead of OIDC `openid profile`. Development tier is admin-only, and Lite/Development versions should follow the Verified on LinkedIn release notes.
- `profile whoami --source profile-api` uses `/v2/me`, which is a different identity source from both OIDC `userinfo` and `identity-me`.
- `profile employment-history --public-id <id> --browser chrome` tries the official API first, then Voyager, then the live Chrome profile page when the API paths are unavailable or return no records.
- `profile employment-history --source voyager-private` uses the web-only Voyager endpoint under `https://www.linkedin.com/voyager/api/...`, not the official OAuth API host. It expects `LINKEDIN_PROFILE_PUBLIC_ID`, `LINKEDIN_VOYAGER_LI_AT`, and either `LINKEDIN_VOYAGER_JSESSIONID` or `LINKEDIN_VOYAGER_CSRF_TOKEN`.
- `profile employment-history --source voyager-private --browser chrome` can read those cookies from a local Chromium-family browser instead of from env vars. `LINKEDIN_VOYAGER_BROWSER` and `LINKEDIN_VOYAGER_COOKIE_FILE` are the env equivalents. On macOS, Python may prompt for access to the browser cookie store, and the Chrome page fallback needs `View > Developer > Allow JavaScript from Apple Events` enabled.

See [onboarding.md](onboarding.md) for the full step-by-step setup flow.

The published PyPI package is `lkdn`. The documented command names are `lkdn` and `linkedin`.
