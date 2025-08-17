"""
Root mox.py script
This will automatically call other scripts with the mox.bat / mox.sh / mox.py shortcut

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
import os.path
import argparse
import subprocess

def ScriptPath(script):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, f"{script}.py")

if __name__ == '__main__':
    # Process arguments
    p = argparse.ArgumentParser(prog="mox.py", allow_abbrev=False)
    p.add_argument("script", nargs="?", default="autogen", help="Script name without .py")
    args, passthrough = p.parse_known_args()


    # Validate script
    path = ScriptPath(args.script)
    if os.path.isfile(path):
        returncode = subprocess.run((sys.executable, path, *passthrough)).returncode
        sys.exit(returncode)
    else:
        print(f'Script "{script}" not found!')
        print(f'')
        print(f'Available scripts:')
        for file in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            if file.endswith('.py') and file != 'mox.py':
                print(f'- {file[0:-3]}')
        sys.exit(-1)
