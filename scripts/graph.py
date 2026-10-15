"""
Project execution script
This script will run the compiled application in the proper way.

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
import mox

import re
import os
import platform
import argparse
import subprocess

if __name__ == '__main__':
    # Cli
    p = argparse.ArgumentParser(prog="graph.py", allow_abbrev=False)
    p.add_argument("--arch", default=platform.machine().lower(), help="Alternative (cross compile) architecture")
    p.add_argument("--vs-version", choices=["2017", "2019", "2022", "2026"], help="Forces a visual studio version")
    args = p.parse_args()

    arch = args.arch
    vsVersion = args.vs_version

    # Create temp folder
    tempFolder = str(os.path.abspath("./dependencies/conan-temp"))
    os.makedirs(tempFolder, exist_ok=True)

    # Generate conan profiles
    os.makedirs("./profiles/", exist_ok=True)
    cpp_version = re.search(r'(\d+)', mox.ExtractLuaDef("./mox.lua", "cmox_cpp_version")).group(1)
    mox.ProfileGen("./profiles/build", platform.machine().lower(), cpp_version, tempFolder, vsVersion)
    mox.ProfileGen(f"./profiles/host_{arch}", arch, cpp_version, tempFolder, vsVersion)

    with open(f'./dependencies_{ platform.system() }.html', "w") as outfile:
        subprocess.run((
            "conan", "graph", "info", 
            "./conanfile.py", 
            "--format=html", 
            f'--profile:host=./profiles/host_{arch}', 
            f'--profile:build=./profiles/build',
        ), stdout=outfile)
