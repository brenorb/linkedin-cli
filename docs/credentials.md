# Credentials and local environment

This project expects three environment variables at runtime:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`
- `LINKEDIN_API_VERSION`

Some commands also use:

- `LINKEDIN_MEMBER_URN` for `organization preflight`

Recommended local setup:

```bash
mkdir -p ~/.config/licli
chmod 700 ~/.config/licli
```

Store secrets in a local shell file that is not part of the repo:

```bash
cat > ~/.config/licli/env.sh <<'EOF'
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
EOF

chmod 600 ~/.config/licli/env.sh
```

Load it when needed:

```bash
source ~/.config/licli/env.sh
```

Good storage options:

- `~/.config/licli/env.sh`
- `~/.zshrc` if you want values loaded in every shell
- another local secrets file that you source manually

Avoid storing tokens in tracked repo files.

## Notes

- `LINKEDIN_AUTHOR_URN` can look like `urn:li:person:abc123` or `urn:li:organization:123456`, depending on whether `post create` or `post list` should act as a member or organization.
- `LINKEDIN_MEMBER_URN` should stay in member form, for example `urn:li:person:abc123`, because `organization preflight` uses it to build the official `organizationAuthorizations` impersonator key. It must match the authenticated viewer.
- `post get` and `post delete` do not read `LINKEDIN_AUTHOR_URN`; they only need the post URN plus `LINKEDIN_ACCESS_TOKEN`.
- `comment get`, `reaction create`, and `social-metadata get` also do not read `LINKEDIN_AUTHOR_URN`.
- `uv run licli profile whoami` is the fastest way in this repo to derive the member-form `LINKEDIN_AUTHOR_URN` from OIDC `userinfo`.
- `uv run licli organization preflight "urn:li:organization:123456"` is the fastest way in this repo to confirm whether the current member URN can create, read-as-author, edit, or delete organic org posts.
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

See [onboarding.md](onboarding.md) for the full step-by-step setup flow.

The published PyPI package is `lkdn`. The CLI entrypoints are `licli`, `lkdn`, and `linkedin`.
