# vcpkg-registry

A custom [vcpkg](https://github.com/microsoft/vcpkg) registry hosting private/third-party ports, following the standard vcpkg registry layout:

```
ports/
  <port>/
    vcpkg.json
    portfile.cmake
versions/
  baseline.json
  <first-letter>-/
    <port>.json
scripts/
  update_port.py          # bump a port to a new upstream release
  update_versions_db.py   # (re)generate version DB entries without bumping
  lib/vcpkg_tool.py        # shared helper, not meant to be run directly
```

## Using this registry in a project

Add it to your project's `vcpkg-configuration.json` as a registry, and list the ports you want to pull from it:

```json
{
  "default-registry": {
    "kind": "builtin",
    "baseline": "<commit-sha-of-your-default-vcpkg-baseline>"
  },
  "registries": [
    {
      "kind": "git",
      "repository": "https://github.com/Cadons/vcpkg-registry",
      "baseline": "<commit-sha-of-this-repo-to-pin-to>",
      "packages": ["<port>"]
    }
  ]
}
```

- `baseline` for this registry must be a commit SHA from **this** repo (not a tag) — pick the commit whose `versions/baseline.json` has the port versions you want as the default. `vcpkg x-update-baseline --add-initial-baseline` can generate/refresh this for you from within your consuming project.
- `packages` lists which port names are resolved from this registry; anything else still comes from `default-registry`.

Then declare the dependency as usual in the consuming project's `vcpkg.json`:

```json
{
  "dependencies": ["<port>"]
}
```

To pin a specific version instead of whatever the baseline points to, use an override:

```json
{
  "dependencies": ["<port>"],
  "overrides": [
    { "name": "<port>", "version": "<version>" }
  ]
}
```

## Updating a port to a new upstream release

`scripts/update_port.py` is generic — it works for **any** port in `ports/` whose `portfile.cmake` fetches sources with `vcpkg_from_github()`. It:

1. verifies the given tag exists on the upstream GitHub repo,
2. downloads the release archive and computes its SHA512,
3. updates `version-string` in the port's `vcpkg.json` and `SHA512` in its `portfile.cmake`,
4. adds a new entry to the version database via `vcpkg x-add-version`.

```sh
python3 scripts/update_port.py <port> <tag> [--repo <owner/name>] [--commit]

# examples
python3 scripts/update_port.py <port> <tag>
python3 scripts/update_port.py <port> <tag> --commit
python3 scripts/update_port.py <port> <tag> --repo <owner>/<repo>   # override auto-detected repo
```

(On Windows, use `python` instead of `python3` if that's how it's set up on your `PATH`.)

Without `--commit`, changes are left staged in git for you to review (`git diff --staged`) before committing.

## Regenerating the version database

`scripts/update_versions_db.py` (re)generates `versions/baseline.json` and the per-port files under `versions/<letter>-/` from the **current** state of `ports/`, without touching any port's version or downloading anything upstream. Use it after:

- manually editing a port (e.g. fixing a portfile bug) without changing its version,
- adding a brand-new port to the registry for the first time,
- rebuilding the whole database from scratch.

```sh
python3 scripts/update_versions_db.py [--commit] [port ...]

# examples
python3 scripts/update_versions_db.py                 # regenerate for every port under ports/
python3 scripts/update_versions_db.py <port>          # regenerate for a single port
python3 scripts/update_versions_db.py --commit <port1> <port2>
```

## Adding a brand-new port

1. Create `ports/<port>/vcpkg.json` and `ports/<port>/portfile.cmake` by hand (see any existing port under `ports/` as a reference).
2. Run `python3 scripts/update_versions_db.py <port>` to generate its initial `versions/<letter>-/<port>.json` entry and add it to `versions/baseline.json`.
3. Review and commit.

## Requirements

- `git`
- Python 3.8+ (standard library only, no extra packages to install)

vcpkg itself doesn't need to be pre-installed: if `$VCPKG_ROOT` isn't set, a private copy of the vcpkg tool is bootstrapped once into `.vcpkg-tool/` (gitignored) and reused on subsequent runs. If you already have vcpkg installed, set `VCPKG_ROOT` to skip the bootstrap step. The scripts work the same way on Windows, macOS and Linux.
