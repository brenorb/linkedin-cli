# LinkedIn credentials

This CLI expects you to bring two values:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`

## 1. Create a LinkedIn app

Create or open an app in the [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps).

For member posting, make sure the app has access to:

- `Share on LinkedIn` for the `w_member_social` permission
- `Sign In with LinkedIn` so you can identify the authenticated member

Also configure a redirect URL on the app, for example:

```text
http://localhost:8000/callback
```

## 2. Run the OAuth member flow

Use LinkedIn's OAuth 2.0 member flow and request at least:

- `w_member_social`
- `openid profile email`

If you are using the older profile flow, `r_liteprofile` also works for retrieving the member id.

Once you exchange the authorization `code` for a token, that token becomes your:

```bash
export LINKEDIN_ACCESS_TOKEN="..."
```

## 3. Fetch your member id

Call the profile endpoint with the access token:

```bash
curl -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/me
```

The response includes an `id`, for example:

```json
{
  "id": "abc123"
}
```

Build the author URN from that id:

```bash
export LINKEDIN_AUTHOR_URN="urn:li:person:abc123"
```

## 4. Set the API version

The Posts API requires a `Linkedin-Version` header in `YYYYMM` format.

```bash
export LINKEDIN_API_VERSION="202505"
```

## 5. Where to store these values

Good options:

- export them in the current shell for one-off usage
- add them to `~/.zshrc` if you want them available in every shell
- keep them in a local secrets file such as `~/.env.linkedin` and source it manually

Avoid storing tokens in tracked repo files.

## Official docs

- [Getting access to LinkedIn APIs](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Sign In with LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-05)
- [URNs and IDs](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/urns?context=linkedin%2Fcontext)
