# Credentials and local environment

This project expects three environment variables at runtime:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`
- `LINKEDIN_API_VERSION`

Recommended local setup:

```bash
mkdir -p ~/.config/linkedin-cli
chmod 700 ~/.config/linkedin-cli
```

Store secrets in a local shell file that is not part of the repo:

```bash
cat > ~/.config/linkedin-cli/env.sh <<'EOF'
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

chmod 600 ~/.config/linkedin-cli/env.sh
```

Load it when needed:

```bash
source ~/.config/linkedin-cli/env.sh
```

Good storage options:

- `~/.config/linkedin-cli/env.sh`
- `~/.zshrc` if you want values loaded in every shell
- another local secrets file that you source manually

Avoid storing tokens in tracked repo files.

## Notes

- `LINKEDIN_AUTHOR_URN` should look like `urn:li:person:abc123`.
- `LINKEDIN_API_VERSION` must use `YYYYMM`.
- A value such as `20250501` is invalid and will cause `426 Requested version ... is not active`.
- Active versions change over time. If a version stops working, update it to a currently active `YYYYMM`.

See [onboarding.md](onboarding.md) for the full step-by-step setup flow.
