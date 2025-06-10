# Github Actions

## Branch Protection Rules

### Create a privileged Github App to bypass branch protection rules

- Create a [user or organisation app][create-github-app]
  - require the repository `contents:write` permission
  - download the created private key
  - note the app id (not the client id)
- create a repo/org variable `RELEASE_APP_ID` with the value of the app id
- create a repo/org secret `RELEASE_APP_SECRET` with the value of the private key

### Definition

Create new _branch ruleset_:

- name: `protect main`
- bypass list: add the Github app; allow always
- target branches: include `default`
- rules
  - restrict deletions
  - require linear history
  - require a pull request before merging
  - require status checks to pass
    - add `style checks`
    - add `test suite`

## Workflows

### [Pull Request](./workflows/pull-request.yml)

Runs the test suite with pytest and checks style using the defined
[pre-commit](../.pre-commit-config.yaml) setup.

### [Tag and Release](./workflows//tag-n-release.yml)

On merge, commitizen will create a new tag based on the conventional commits and update the
[changelog](../CHANGELOG.md). A Github release based on the tag and changelog is also created.

## Actions

### [Bootstrap](./actions/bootstrap/action.yml)

Custom action to install uv, set up python - with caching - and create the virtual env containing
the project dependencies.

### [Pre-Commit](./actions/pre-commit/action.yml)

Custom action to run pre-commit and caching the pre-commit env based on the config file.

[create-github-app]: https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app
