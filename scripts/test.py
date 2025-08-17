"""
Automatic generation script
Will completely setup, build and deploy your project

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
import sys
import argparse
import platform
import subprocess

if __name__ == '__main__':
    # Configuration
    p = argparse.ArgumentParser(prog="configure.py", allow_abbrev=False)
    p.add_argument("--conf", default="Release", help="Build configuration (default: Release)")
    p.add_argument("--arch", default=platform.machine().lower(), help="Alternative (cross compile) architecture")
    args = p.parse_args()

    conf = args.conf

    # Init project
    subprocess.run((sys.executable, './scripts/mox.py', 'init', '--arch', args.arch))

    # Build project
    subprocess.run((sys.executable, './scripts/mox.py', 'build', '--conf', args.conf))

    # Run test
    test_result = subprocess.run((sys.executable, './scripts/mox.py', 'run', '--conf', args.conf, '--arch', args.arch, 'unittest')).returncode

    # Exit with result
    sys.exit(test_result)
