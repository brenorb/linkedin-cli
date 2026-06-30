# Credentials and local environment

This project expects three environment variables at runtime:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`
- `LINKEDIN_API_VERSION`

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

# Must be YYYYMM, not YYYYMMDD.
export LINKEDIN_API_VERSION='202604'
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
- `post get` and `post delete` do not read `LINKEDIN_AUTHOR_URN`; they only need the post URN plus `LINKEDIN_ACCESS_TOKEN`.
- `LINKEDIN_API_VERSION` must use `YYYYMM`.
- A value such as `20250501` is invalid and will cause `426 Requested version ... is not active`.
- Active versions change over time. If a version stops working, update it to a currently active `YYYYMM`.

See [onboarding.md](onboarding.md) for the full step-by-step setup flow.
