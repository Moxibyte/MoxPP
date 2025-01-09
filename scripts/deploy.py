"""
The deployment script is written minimal by default!
Add your own code to the main "function"

The script is by default called with "Release" in the first argument

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
import os
import sys
import zipfile

if __name__ == '__main__':
    # Configuration for the build
    conf = 'Release'
    if len(sys.argv) > 1:
        conf = sys.argv[1]

    # Architecture
    arch = mox.GetPlatformInfo()["premake_arch"]

    # Work directory's
    tempDir = f'./temp/{conf}/'
    deployDir = f'./deploy/{conf}/'
    os.makedirs(tempDir, exist_ok=True)
    os.makedirs(deployDir, exist_ok=True)

    # We will do a quick copy from the out folder
    # TODO: Add your own implementation
    with zipfile.ZipFile(f'{deployDir}package.zip', 'w') as zip_file:
        for file in os.listdir(f'./build/{arch}-{conf}/bin'):
            path = f'./build/{arch}-{conf}/bin/{file}'
            if os.path.isfile(path):
                zip_file.write(path, file)
