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
import platform
import argparse

if __name__ == '__main__':
    # Configuration for the build
    p = argparse.ArgumentParser(prog="deploy.py", allow_abbrev=False)
    p.add_argument("--conf", default="Release", help="Build configuration (default: Release)")
    p.add_argument("--arch", default=platform.machine().lower(), help="Alternative (cross compile) architecture")
    args = p.parse_args()

    # Detect version and architecture
    version = mox.GetAppVersion()
    arch = mox.GetPlatformInfo(args.arch)["premake_arch"]

    # TODO: Add your own implementation
    #       We do some quick example here

    # Simple zip archive with the software (dumb copy)
    # Also add the msvc redists via "AddMSVCRedists" call (does nothing is not on windows!)
    zipArchive = mox.MDZip(mox.AutomaticFilename("moxpp", version, f'{args.arch}-{args.conf}', "zip"))
    zipArchive.AddFolder(f'./build/{args.arch}-{args.conf}/bin', '')
    # zipArchive.AddMSVCRedists() <-- Add this when you want to distribute redists
    zipArchive.Deploy()

    # Source archive
    srcArchive = mox.MDSrc(mox.AutomaticFilename("moxpp_src", version, f'{args.arch}-{args.conf}', "zip"))
    srcArchive.Deploy()
