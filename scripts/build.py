"""
Will build your project
Compiles the project dependent on your system (MSBuild / Makefile)

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
import moxwin

import sys
import glob
import subprocess

def WindowsBuild(conf):
    # Find MSBuild
    vswhere = moxwin.FindLatestVisualStudio()
    vspath = moxwin.GetVisualStudioPath(vswhere)
    msbuild = f'{vspath}\\MSBuild\\Current\\Bin\\MSBuild.exe'

    # Find solution file
    slnFiles = glob.glob('*.sln')
    if len(slnFiles) == 0:
        print('No solution file found! Building not possible!')
        return

    # Run build
    subprocess.run((
        msbuild, slnFiles[0],
        f'-p:Configuration={conf}' 
    ))

def LinuxBuild(conf):
    # Run the makefile
    subprocess.run((
        'make', f'config={conf.lower()}', 'all'
    ))

if __name__ == '__main__':
    # Configuration from cli
    conf = 'Release'
    if len(sys.argv) > 1:
        conf = sys.argv[1]

    # Run build step
    if sys.platform.startswith('linux'):
        LinuxBuild(conf)
    else:
        WindowsBuild(conf)
