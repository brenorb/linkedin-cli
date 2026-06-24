# PyPI trusted publishing

This repository is wired to publish `licli` to PyPI directly from GitHub Actions.

The GitHub-side workflow is:

- workflow file: `.github/workflows/release.yml`
- job: `publish-pypi`
- permissions: `id-token: write`
- environment: `pypi`

## One-time PyPI setup

Before the workflow can publish, PyPI needs a trusted publisher entry that matches:

- PyPI project name: `licli`
- owner: `brenorb`
- repository: `linkedin-cli`
- workflow: `.github/workflows/release.yml`
- environment: `pypi`

For a brand-new project, create a pending trusted publisher for `licli` in PyPI before pushing the first release tag.

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
uvx licli --help
uv tool install licli
```
