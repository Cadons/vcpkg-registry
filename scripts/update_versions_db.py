#!/usr/bin/env python3
"""Regenerate vcpkg version database entries (versions/baseline.json,
versions/<first-letter>-/<port>.json) from the current state of ports/,
WITHOUT bumping any port to a new upstream release.

Use this after manually editing a port (e.g. fixing a portfile bug,
adding a brand new port, bumping a port by hand) instead of going
through update_port.py, or to (re)build the whole database from scratch.

Usage:
    python3 scripts/update_versions_db.py [--commit] [port ...]

With no port names, every port under ports/ is processed. Pass one or
more port names to only process those.

Examples:
    python3 scripts/update_versions_db.py                # all ports
    python3 scripts/update_versions_db.py docraft         # one port
    python3 scripts/update_versions_db.py --commit docraft someport

Requires: git, Python 3.8+ (standard library only).
Bootstraps its own copy of the vcpkg tool under .vcpkg-tool/ if VCPKG_ROOT
is not set and no bootstrapped copy exists yet.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vcpkg_tool import resolve_vcpkg_exe  # noqa: E402


def run(cmd, **kwargs):
    print("+", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate the vcpkg version database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "ports", nargs="*", help="Port names to process (default: all ports)"
    )
    parser.add_argument(
        "--commit", action="store_true", help="Commit the staged changes"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    ports_dir = repo_root / "ports"
    versions_dir = repo_root / "versions"

    ports = args.ports or sorted(
        p.name for p in ports_dir.iterdir() if p.is_dir()
    )
    if not ports:
        print(f"error: no ports found under {ports_dir}", file=sys.stderr)
        sys.exit(1)

    for port in ports:
        if not (ports_dir / port / "vcpkg.json").is_file():
            print(
                f"error: port '{port}' not found "
                f"(expected {ports_dir / port / 'vcpkg.json'})",
                file=sys.stderr,
            )
            sys.exit(1)

    vcpkg_exe = resolve_vcpkg_exe(repo_root)

    print("==> Staging ports/ (git tree hashes are computed from the git index)")
    run(["git", "add", str(ports_dir)], cwd=repo_root)

    print(f"==> Regenerating version database for: {', '.join(ports)}")
    for port in ports:
        run(
            [
                str(vcpkg_exe),
                "x-add-version",
                port,
                f"--x-builtin-ports-root={ports_dir}",
                f"--x-builtin-registry-versions-dir={versions_dir}",
                "--overwrite-version",
            ],
            cwd=repo_root,
        )

    run(["git", "add", str(versions_dir)], cwd=repo_root)

    print("\n==> Done. Changes staged:")
    run(["git", "status", "--short", str(ports_dir), str(versions_dir)], cwd=repo_root)

    if args.commit:
        run(["git", "commit", "-m", "Regenerate vcpkg version database"], cwd=repo_root)
        print("==> Committed.")
    else:
        print("\nReview the staged changes, then commit, e.g.:")
        print('  git commit -m "Regenerate vcpkg version database"')


if __name__ == "__main__":
    main()
