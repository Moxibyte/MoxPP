"""
Project execution script
This script will run the compiled application in the proper way.

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
import mox
import sys
import argparse
import platform
import subprocess

if __name__ == '__main__':
    p = argparse.ArgumentParser(prog="run.py", allow_abbrev=False)
    p.add_argument("--conf", default="Release", help="Build configuration (default: Release)")
    p.add_argument("--arch", default=platform.machine().lower(), help="Alternative (cross compile) architecture")
    p.add_argument("exe", nargs="?", help="Executable name in build/{arch}-{conf}/bin")
    args, passthrough = p.parse_known_args()

    conf = args.conf
    arch = mox.GetPlatformInfo(args.arch)["premake_arch"]

    if args.exe:
        exe = args.exe
        exepath = f'build/{arch}-{conf}/bin/{exe}'
        if sys.platform.startswith('linux'):
            exepath = '../' + exepath
        else:
            exepath = './' + exepath

        returncode = subprocess.run(
            (exepath, *passthrough),
            cwd='./app'
        ).returncode
        sys.exit(returncode)
    else:
        print('No executable provided!')
