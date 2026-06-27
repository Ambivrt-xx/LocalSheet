#!/usr/bin/env python3
"""
LocalSheet — build script.
Produces a standalone, self-contained executable that users can download and run
without installing Python or any dependencies.

Usage:
    python build.py            # auto-detect platform (Windows .exe / macOS .app)
    python build.py --clean    # remove previous build artifacts first

Requirements:
    pip install pyinstaller
"""
import os
import sys
import shutil
import platform
import subprocess

APP_NAME = "LocalSheet"
ENTRY = "app.py"
PACKAGE = "src"


def _run(cmd):
    print(f"\n> {' '.join(cmd)}\n")
    subprocess.check_call(cmd)


def clean():
    for d in ("build", "dist", "__pycache__"):
        if os.path.isdir(d):
            print(f"Removing {d}/")
            shutil.rmtree(d, ignore_errors=True)
    spec = f"{APP_NAME}.spec"
    if os.path.isfile(spec):
        os.remove(spec)


def build():
    is_windows = platform.system() == "Windows"
    is_mac = platform.system() == "Darwin"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        f"--collect-all", PACKAGE,
        ENTRY,
    ]

    # Include an icon if present
    icon = "icon.ico" if is_windows else ("icon.icns" if is_mac else None)
    if icon and os.path.isfile(icon):
        cmd += ["--icon", icon]

    _run(cmd)

    if is_windows:
        out = os.path.join("dist", f"{APP_NAME}.exe")
    elif is_mac:
        out = os.path.join("dist", f"{APP_NAME}.app")
    else:
        out = os.path.join("dist", APP_NAME)

    print(f"\nBuild complete: {out}")
    print("  Zip this file/folder and share it for download.")


def main():
    if "--clean" in sys.argv:
        clean()
    build()


if __name__ == "__main__":
    main()