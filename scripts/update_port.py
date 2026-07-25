#!/usr/bin/env python3
"""Bump any port in this registry to a new upstream GitHub release and
add the corresponding entry to the vcpkg version database
(versions/baseline.json, versions/<first-letter>-/<port>.json).

Works for any port whose portfile.cmake fetches sources with
vcpkg_from_github(). The upstream repo is auto-detected from the port's
existing REPO line unless overridden with --repo.

Usage:
    python3 scripts/update_port.py <port> <tag> [--repo <owner/name>] [--commit]

Examples:
    python3 scripts/update_port.py docraft v1.0.0-beta.4
    python3 scripts/update_port.py docraft v1.0.0-beta.4 --commit
    python3 scripts/update_port.py someport v2.3.0 --repo someorg/somerepo

Requires: git, Python 3.8+ (standard library only).
Bootstraps its own copy of the vcpkg tool under .vcpkg-tool/ if VCPKG_ROOT
is not set and no bootstrapped copy exists yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vcpkg_tool import resolve_vcpkg_exe  # noqa: E402

USER_AGENT = "vcpkg-registry-update-script"


def run(cmd, **kwargs):
    print("+", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, **kwargs)


def detect_upstream_repo(portfile_text: str) -> str | None:
    match = re.search(
        r"vcpkg_from_github\s*\((.*?)\)", portfile_text, re.DOTALL
    )
    if not match:
        return None
    block = match.group(1)
    repo_match = re.search(r"REPO\s+(\S+)", block)
    return repo_match.group(1) if repo_match else None


def verify_tag_exists(repo: str, tag: str) -> None:
    url = f"https://api.github.com/repos/{repo}/git/refs/tags/{tag}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        urllib.request.urlopen(request)
    except urllib.error.HTTPError as exc:
        print(
            f"error: tag '{tag}' not found on https://github.com/{repo} "
            f"(HTTP {exc.code})",
            file=sys.stderr,
        )
        sys.exit(1)


def download_and_hash(repo: str, tag: str) -> str:
    url = f"https://github.com/{repo}/archive/{tag}.tar.gz"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha512()
    with urllib.request.urlopen(request) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def update_vcpkg_json(vcpkg_json_path: Path, tag: str) -> None:
    data = json.loads(vcpkg_json_path.read_text(encoding="utf-8"))
    data["version-string"] = tag
    vcpkg_json_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def update_portfile_sha512(portfile_path: Path, new_sha512: str) -> None:
    text = portfile_path.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r"SHA512 [0-9a-fA-F]+", f"SHA512 {new_sha512}", text
    )
    if count == 0:
        print(f"error: no SHA512 line found in {portfile_path}", file=sys.stderr)
        sys.exit(1)
    portfile_path.write_text(new_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bump a port to a new upstream release.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("port", help="Port name (directory under ports/)")
    parser.add_argument("tag", help="Upstream git tag / release to bump to")
    parser.add_argument(
        "--repo", help="Override the auto-detected owner/repo on GitHub"
    )
    parser.add_argument(
        "--commit", action="store_true", help="Commit the staged changes"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    port_dir = repo_root / "ports" / args.port
    vcpkg_json_path = port_dir / "vcpkg.json"
    portfile_path = port_dir / "portfile.cmake"

    if not vcpkg_json_path.is_file() or not portfile_path.is_file():
        print(
            f"error: port '{args.port}' not found "
            f"(expected {vcpkg_json_path} and {portfile_path})",
            file=sys.stderr,
        )
        sys.exit(1)

    upstream_repo = args.repo or detect_upstream_repo(portfile_path.read_text())
    if not upstream_repo:
        print(
            f"error: could not auto-detect the upstream GitHub repo from {portfile_path}\n"
            "       (only ports using vcpkg_from_github() are supported); pass --repo <owner/name>",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"==> Port '{args.port}' upstream repo: {upstream_repo}")

    print(f"==> Verifying tag '{args.tag}' exists on {upstream_repo}")
    verify_tag_exists(upstream_repo, args.tag)

    print(f"==> Downloading release archive for {args.tag} and computing SHA512")
    new_sha512 = download_and_hash(upstream_repo, args.tag)
    print(f"    SHA512: {new_sha512}")

    print("==> Updating vcpkg.json version-string")
    update_vcpkg_json(vcpkg_json_path, args.tag)

    print("==> Updating portfile.cmake SHA512")
    update_portfile_sha512(portfile_path, new_sha512)

    vcpkg_exe = resolve_vcpkg_exe(repo_root)

    print("==> Staging port changes (git tree hash is computed from the git index)")
    run(["git", "add", str(port_dir)], cwd=repo_root)

    print("==> Adding version entry with vcpkg x-add-version")
    run(
        [
            str(vcpkg_exe),
            "x-add-version",
            args.port,
            f"--x-builtin-ports-root={repo_root / 'ports'}",
            f"--x-builtin-registry-versions-dir={repo_root / 'versions'}",
            "--overwrite-version",
        ],
        cwd=repo_root,
    )

    run(["git", "add", str(repo_root / "versions")], cwd=repo_root)

    print("\n==> Done. Changes staged:")
    run(
        ["git", "status", "--short", str(port_dir), str(repo_root / "versions")],
        cwd=repo_root,
    )

    if args.commit:
        run(["git", "commit", "-m", f"Update {args.port} to {args.tag}"], cwd=repo_root)
        print("==> Committed.")
    else:
        print("\nReview the staged changes, then commit, e.g.:")
        print(f'  git commit -m "Update {args.port} to {args.tag}"')


if __name__ == "__main__":
    main()
