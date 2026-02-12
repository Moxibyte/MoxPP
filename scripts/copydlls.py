"""
Script that copies all conan .dll/.so files to a dedicated directory

Copyright (c) 2026 Moxibyte GmbH

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
import mox
import shutil
import platform
import argparse
from pathlib import Path


def copy_binaries(source_root, debug_dest, release_dest, conan_arch):
    source_root = Path(source_root).resolve()
    debug_dest = Path(debug_dest).resolve()
    release_dest = Path(release_dest).resolve()

    if not source_root.exists():
        print(f"Source directory does not exist: {source_root}")
        return

    # Determine file extension based on platform
    system = platform.system().lower()
    if system == "windows":
        binary_ext = ".dll"
    elif system == "darwin":
        binary_ext = ".dylib"
    elif system == "linux":
        binary_ext = ".so*"
    else:
        print(f"Unsupported platform: {system}")
        return

    for lib_dir in source_root.glob("host/*/*"):  # libname/libversion
        for build_type in ["Debug", "Release"]:
            build_path = lib_dir / build_type
            if not build_path.exists():
                continue

            dll_dirs = ( "bin", "lib" )
            for dll_dir in dll_dirs:
                platform_path = build_path / conan_arch / dll_dir
                if platform_path.exists():
                    dest_dir = debug_dest if build_type == "Debug" else release_dest
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    for binary_file in platform_path.rglob(f"*{binary_ext}"):
                        dest_file = dest_dir / binary_file.name
                        dest_file.parent.mkdir(parents=True, exist_ok=True)

                        if os.name == "nt" or not binary_file.is_symlink():
                            shutil.copy2(binary_file, dest_file)
                            print(f"Copied {binary_file} -> {dest_file}")
                            continue

                        # POSIX + symlink: try to recreate the link; if not possible, materialize it
                        link_text = os.readlink(binary_file)  # keep relative target if it was relative
                        try:
                            if dest_file.exists() or dest_file.is_symlink():
                                dest_file.unlink()
                            os.symlink(link_text, dest_file)
                            print(f"Linked {binary_file} -> {dest_file} ({link_text})")
                        except OSError:
                            shutil.copy2(binary_file.resolve(), dest_file)
                            print(f"Copied (materialized) {binary_file} -> {dest_file}")

if __name__ == "__main__":
    # Cli
    p = argparse.ArgumentParser(prog="copydlls.py", allow_abbrev=False)
    p.add_argument("arch", nargs="?", default=platform.machine().lower(), help="Alternative (cross compile) architecture")
    args = p.parse_args()


    # Resolve architecture
    hostArch = mox.GetPlatformInfo(args.arch)

    # Example usage
    source_directory = "./dependencies/full_deploy"
    debug_output_directory = f"./dlls/Debug-{hostArch['premake_arch']}"
    release_output_directory = f"./dlls/Release-{hostArch['premake_arch']}"

    copy_binaries(source_directory, debug_output_directory, release_output_directory, hostArch["conan_arch"])
