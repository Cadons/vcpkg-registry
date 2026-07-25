"""Shared helper: resolve a usable vcpkg executable.

Uses $VCPKG_ROOT/vcpkg(.exe) if set; otherwise bootstraps a private copy
under .vcpkg-tool/ (gitignored) the first time it's needed and reuses it
on later runs. Works on Windows, macOS and Linux.
"""

import os
import platform
import subprocess
from pathlib import Path

VCPKG_GIT_URL = "https://github.com/microsoft/vcpkg.git"


def _exe_name() -> str:
    return "vcpkg.exe" if platform.system() == "Windows" else "vcpkg"


def resolve_vcpkg_exe(repo_root: Path) -> Path:
    exe_name = _exe_name()

    vcpkg_root = os.environ.get("VCPKG_ROOT")
    if vcpkg_root:
        candidate = Path(vcpkg_root) / exe_name
        if candidate.is_file():
            return candidate

    tool_dir = repo_root / ".vcpkg-tool"
    exe = tool_dir / exe_name
    if not exe.is_file():
        print("==> Bootstrapping vcpkg tool into .vcpkg-tool/ (no VCPKG_ROOT set)")
        if not tool_dir.is_dir():
            subprocess.run(
                ["git", "clone", "--depth", "1", VCPKG_GIT_URL, str(tool_dir)],
                check=True,
            )
        if platform.system() == "Windows":
            bootstrap = tool_dir / "bootstrap-vcpkg.bat"
            subprocess.run([str(bootstrap), "-disableMetrics"], check=True, shell=True)
        else:
            bootstrap = tool_dir / "bootstrap-vcpkg.sh"
            subprocess.run(["bash", str(bootstrap), "-disableMetrics"], check=True)

    return exe
