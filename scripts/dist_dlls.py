"""
Script that distributes dll to the build folder

Copyright (c) 2025 Moxibyte GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import sys
import shutil
import hashlib
import platform
import argparse
from pathlib import Path

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="dist_dlls.py", allow_abbrev=False)
    p.add_argument("src", help="Source path")
    p.add_argument("dst", help="Destination path")
    args = p.parse_args()

    src = Path(args.src).resolve()
    dst = Path(args.dst).resolve()

    if not src.is_dir():
        print(f"Error: Source directory '{src}' does not exist.")
        sys.exit(1)

    def _copy_file(src_file, dest_file):
        """Copy one file, preserving symlinks on POSIX."""
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        if dest_file.exists():
            return
        if os.name == "nt" or not src_file.is_symlink():
            shutil.copy2(src_file, dest_file)
            print(f"Copied {src_file} -> {dest_file}")
            return
        # POSIX + symlink: try to recreate the link; if not possible, materialize it
        link_text = os.readlink(src_file)
        try:
            if dest_file.exists() or dest_file.is_symlink():
                dest_file.unlink()
            os.symlink(link_text, dest_file)
            print(f"Linked {src_file} -> {dest_file} ({link_text})")
        except OSError:
            shutil.copy2(src_file.resolve(), dest_file)
            print(f"Copied (materialized) {src_file} -> {dest_file}")

    # Mirror entire src tree into dst, preserving hierarchy
    for src_file in src.rglob("*"):
        if src_file.is_file():
            _copy_file(src_file, dst / src_file.relative_to(src))
