"""
Script that copies all conan .dll/.so files to a dedicated directory

Copyright (c) 2025 Ludwig Füchsl

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
import shutil
import platform
from pathlib import Path


def copy_binaries(source_root, debug_dest, release_dest):
    source_root = Path(source_root).resolve()
    debug_dest = Path(debug_dest).resolve()
    release_dest = Path(release_dest).resolve()

    if not source_root.exists():
        print(f"Source directory does not exist: {source_root}")
        return

    # Determine file extension based on platform
    system = platform.system()
    if system == "Windows":
        binary_ext = ".dll"
    elif system == "Linux":
        binary_ext = ".so"
    else:
        print(f"Unsupported platform: {system}")
        return

    for lib_dir in source_root.glob("host/*/*"):  # libname/libversion
        for build_type in ["Debug", "Release"]:
            build_path = lib_dir / build_type
            if not build_path.exists():
                continue

            # Find the platform subdirectory (assuming only one exists)
            platforms = list(build_path.iterdir())
            if len(platforms) != 1:
                print(f"Skipping {lib_dir}, expected exactly one platform directory but found {len(platforms)}")
                continue

            dll_dirs = ( "bin", "lib" )
            for dll_dir in dll_dirs:
                platform_path = platforms[0] / dll_dir
                if platform_path.exists():
                    dest_dir = debug_dest if build_type == "Debug" else release_dest
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    for binary_file in platform_path.glob(f"*{binary_ext}"):
                        dest_file = dest_dir / binary_file.name
                        shutil.copy2(binary_file, dest_file)
                        print(f"Copied {binary_file} -> {dest_file}")

if __name__ == "__main__":
    # Example usage
    source_directory = "./dependencies/full_deploy"
    debug_output_directory = "./dlls/Debug"
    release_output_directory = "./dlls/Release"
    
    copy_binaries(source_directory, debug_output_directory, release_output_directory)              
