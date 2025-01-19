"""
The deployment script is written minimal by default!
Add your own code to the main "function"

The script is by default called with "Release" in the first argument

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
import mox
import os
import sys
import zipfile

if __name__ == '__main__':
    # Configuration for the build
    conf = 'Release'
    if len(sys.argv) > 1:
        conf = sys.argv[1]

    # Version detection
    version = mox.GetAppVersion()

    # Architecture
    arch = mox.GetPlatformInfo()["premake_arch"]

    # TODO: Add your own implementation
    #       We do some quick example here

    # Simple zip archive with the software (dumb copy)
    zipArchive = mox.MDZip(mox.AutomaticFilename("moxpp", version, conf, "zip"))
    zipArchive.AddFolder(f'./build/{arch}-{conf}/bin', '')
    zipArchive.Deploy()

    # Source archive
    srcArchive = mox.MDSrc(mox.AutomaticFilename("moxpp_src", version, conf, "zip"))
    srcArchive.Deploy()
