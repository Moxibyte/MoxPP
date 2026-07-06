"""
Will build your project
Compiles the project dependent on your system (MSBuild / Makefile)

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
import moxwin
import mox

import os
import re
import sys
import glob
import argparse
import platform
import subprocess

def WindowsBuild(conf):
    # Find MSBuild
    vswhere = moxwin.FindLatestVisualStudio()
    vspath = moxwin.GetVisualStudioPath(vswhere)
    msbuild = f'{vspath}\\MSBuild\\Current\\Bin\\MSBuild.exe'

    # Find solution file
    slnFiles = glob.glob('*.sln') + glob.glob('*.slnx')
    if len(slnFiles) == 0:
        print('No solution file found! Building not possible!')
        sys.exit(1)

    # Run build
    mox.RunChecked((
        msbuild, slnFiles[0],
        f'-p:Configuration={conf}'
    ))

def DistributeDlls(conf):
    # Distribute shared libraries into the build output directory.
    # The premake pre/post-build hooks may not fire correctly in all
    # Premake5 backends (e.g. xcode4), so we ensure distribution here as well.
    # The target architecture is derived from the generated output folders
    # because on cross builds it differs from the build machine architecture.
    for output_dir in glob.glob(os.path.join('.', 'build', f'*-{conf}', 'bin')):
        premake_arch = os.path.basename(os.path.dirname(output_dir)).rsplit(f'-{conf}', 1)[0]
        dlls_src = os.path.join('.', 'dlls', f'{conf}-{premake_arch}')
        if os.path.isdir(dlls_src):
            subprocess.run([sys.executable, './scripts/dist_dlls.py', dlls_src, output_dir], check=False)

def LinuxBuild(conf):
    # Run the makefile
    mox.RunChecked((
        'make', f'config={conf.lower()}', 'all'
    ))

    # Safety net in case the gmake postbuild hook did not fire
    DistributeDlls(conf)

def MacosBuild(conf):
    # Find workspace
    workspace = glob.glob('*.xcworkspace')
    if len(workspace) == 0:
        print('No xcode workspace file found! Building not possible!')
        sys.exit(1)

    # Find all schemes
    schemesCall = subprocess.check_output((
        'xcodebuild',
        '-list',
        '-workspace', workspace[0]
    ), text=True)
    schemesString = re.search(r"Schemes:\s*(.*)", schemesCall, re.M | re.S).group(1)
    schemes = re.findall(r"\S+", schemesString)

    # Build
    for scheme in schemes:
        mox.RunChecked((
            'xcodebuild',
            '-workspace', workspace[0],
            '-scheme', scheme,
            '-configuration', conf,
            'build'
        ))

    # Safety net in case the xcode4 postbuild hook did not fire
    DistributeDlls(conf)

def VerifyBuildArtifacts(conf):
    # Guards against build tools that report success without producing output
    artifacts = glob.glob(os.path.join('.', 'build', f'*-{conf}', 'bin', '*'))
    if len(artifacts) == 0:
        print(f'No build artifacts found in ./build/*-{conf}/bin/! The build did not produce any output!')
        sys.exit(1)

if __name__ == '__main__':
    # Configuration from cli
    p = argparse.ArgumentParser(prog="build.py", allow_abbrev=False)
    p.add_argument("--conf", default="Release", help="Build configuration (default: Release)")
    args = p.parse_args()

    # Run build step
    pf = platform.system().lower()
    if pf == "windows":
        WindowsBuild(args.conf)
    elif pf == "darwin":
        MacosBuild(args.conf)
    else:
        LinuxBuild(args.conf)

    # Make sure the build actually produced binaries
    VerifyBuildArtifacts(args.conf)
