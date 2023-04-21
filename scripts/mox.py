"""
Root mox.py script
This will automatically call other scripts with the mox.bat / mox.sh / mox.py shortcut

Copyright (c) 2023 Moxibyte GmbH

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
import subprocess

def ScriptPath(script):
    return f'./scripts/{script}.py'

if __name__ == '__main__':
    # Process arguments
    args = sys.argv
    if len(args) > 1:
        script = args[1]
        args = args[2::]
    else:
        script = 'autogen'
        args = []    

    # Validate script
    path = ScriptPath(script)
    if os.path.isfile(path):
        subprocess.run((sys.executable, path, *args))
    else:
        print(f'Script "{script}" not found!')
        print(f'')
        print(f'Available scripts:')
        for file in os.listdir('./scripts'):
            if file.endswith('.py') and file != 'mox.py':
                print(f'- {file[0:-3]}')
