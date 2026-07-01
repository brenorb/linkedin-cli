# PyPI publishing

This repository is wired to publish `lkdn` to PyPI directly from GitHub Actions using PyPI trusted publishing via GitHub OIDC.

The GitHub-side workflow is:

- workflow file: `.github/workflows/release.yml`
- job: `publish-pypi`
- environment: `pypi`
- permission: `id-token: write`

## One-time setup

Before the workflow can publish, PyPI needs a pending trusted publisher configured for:

- project: `lkdn`
- owner: `brenorb`
- repository: `linkedin-cli`
- workflow: `release.yml`
- environment: `pypi`

## Release flow

After the trusted publisher exists, publishing is:

1. push a semver tag like `v0.1.0`
2. let GitHub Actions run `.github/workflows/release.yml`
3. the workflow will:
   - build `sdist` and wheel artifacts
   - attach them to the GitHub release
   - publish them to PyPI

## Intended install UX

```bash
uvx --from lkdn lkdn --help
uv tool install lkdn
lkdn --help
linkedin --help
```
