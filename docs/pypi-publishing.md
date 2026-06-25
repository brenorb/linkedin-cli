# PyPI publishing

This repository is wired to publish `licli` to PyPI directly from GitHub Actions using a stored PyPI API token.

The GitHub-side workflow is:

- workflow file: `.github/workflows/release.yml`
- job: `publish-pypi`
- secret: `PYPI_API_TOKEN`

## One-time GitHub setup

Before the workflow can publish, GitHub needs a repository secret named `PYPI_API_TOKEN` whose value is a PyPI API token that can upload `licli`.

## Release flow

After the secret exists, publishing is:

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
