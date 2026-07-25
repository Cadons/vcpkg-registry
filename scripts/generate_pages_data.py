#!/usr/bin/env python3
"""Generate docs/packages.json from the current state of ports/ and
versions/baseline.json, for the GitHub Pages site under docs/.

Usage:
    python3 scripts/generate_pages_data.py

Requires: Python 3.8+ (standard library only).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def normalize_dependency(dep) -> dict:
    if isinstance(dep, str):
        return {"name": dep, "host": False}
    return {"name": dep["name"], "host": bool(dep.get("host", False))}


def load_package(port_dir: Path, baseline: dict) -> dict:
    vcpkg_json = json.loads((port_dir / "vcpkg.json").read_text(encoding="utf-8"))
    name = vcpkg_json["name"]

    baseline_entry = baseline.get(name, {})
    version = (
        baseline_entry.get("baseline")
        or vcpkg_json.get("version-string")
        or vcpkg_json.get("version")
        or vcpkg_json.get("version-semver")
        or vcpkg_json.get("version-date")
        or ""
    )
    port_version = baseline_entry.get("port-version", vcpkg_json.get("port-version", 0))

    return {
        "name": name,
        "version": version,
        "port_version": port_version,
        "description": vcpkg_json.get("description", ""),
        "homepage": vcpkg_json.get("homepage", ""),
        "license": vcpkg_json.get("license", ""),
        "dependencies": [
            normalize_dependency(dep) for dep in vcpkg_json.get("dependencies", [])
        ],
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    ports_dir = repo_root / "ports"
    baseline_path = repo_root / "versions" / "baseline.json"
    out_path = repo_root / "docs" / "packages.json"

    if not ports_dir.is_dir():
        print(f"error: {ports_dir} not found", file=sys.stderr)
        sys.exit(1)

    baseline = json.loads(baseline_path.read_text(encoding="utf-8")).get("default", {})

    packages = sorted(
        (
            load_package(p, baseline)
            for p in ports_dir.iterdir()
            if p.is_dir() and (p / "vcpkg.json").is_file()
        ),
        key=lambda pkg: pkg["name"],
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")
    print(f"==> Wrote {len(packages)} package(s) to {out_path}")


if __name__ == "__main__":
    main()
