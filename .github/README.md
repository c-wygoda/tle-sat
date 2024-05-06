# Github Actions

## Workflows

### [Pull Request](./workflows/pull-request.yml)

Runs the test suite with pytest and checks style using the defined
[pre-commit](../.pre-commit-config.yaml) setup.

### [Tag and Release](./workflows//tag-n-release.yml)

On merge, commitizen will create a new tag based on the conventional commits and update
the [changelog](../CHANGELOG.md). A Github release based on the tag and changelog is
also created.

## Actions

### [Bootstrap](./actions/bootstrap/action.yml)

Custom action to install poetry, set up python - with caching - and create the virtual
env containing the project dependencies.

### [Pre-Commit](./actions/pre-commit/action.yml)

Custom action to run pre-commit and caching the pre-commit env based on the config
file.
