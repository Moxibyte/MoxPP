"""
Project execution script
This script will run the compiled application in the proper way.

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
import sys
import subprocess

if __name__ == '__main__':
    argv_index = 1

    # Configuration
    conf = 'Release'
    if len(sys.argv) > argv_index:
        if sys.argv[argv_index].startswith('-c='):
            conf = sys.argv[argv_index][3::]
            argv_index += 1

    if len(sys.argv) > argv_index:
        # Executable name
        exe = sys.argv[argv_index]
        argv_index += 1

        # Arguments
        args = sys.argv[argv_index::]

	# Path to exe
        exepath = f'build/x86_64-{conf}/bin/{exe}'
        if sys.platform.startswith('linux'):
            exepath = '../' + exepath
        else:
            exepath = './' + exepath

        # Run executable
        subprocess.run(
            (exepath, *args), 
            cwd='./app'
        )
    else:
        print('No executable provided!')
