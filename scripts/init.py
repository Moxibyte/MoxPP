"""
Project initialization script
This will initialize your VisualStudio solution / Your makefile

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
import moxwin

import os
import sys
import stat
import zipfile
import tarfile
import platform
import subprocess
import urllib.request

def GetExecutable(exe):
    if sys.platform.startswith('linux'):
        return exe
    else:
        return f'{exe}.exe'

def GetPremakeGenerator():
    if sys.platform.startswith('linux'):
        return 'gmake2'
    else:
        vswhere = moxwin.FindLatestVisualStudio()
        vsversion = moxwin.GetVisualStudioYearNumber(vswhere)
        return f'vs{vsversion}'

def GetPremakeDownloadUrl(version):
    baseUrl = f'https://github.com/premake/premake-core/releases/download/v{version}/premake-{version}'
    if sys.platform.startswith('linux'):
        return baseUrl + '-linux.tar.gz'
    else:
        return baseUrl + '-windows.zip'

def DownloadPremake(version = '5.0.0-beta4'):
    premakeDownloadUrl = GetPremakeDownloadUrl(version)
    premakeTargetFolder = './dependencies/premake5'
    premakeTargetZip = f'{premakeTargetFolder}/premake5.tmp'
    premakeTargetExe = f'{premakeTargetFolder}/{GetExecutable("premake5")}'

    if not os.path.exists(premakeTargetExe):
        print('Downloading premake5...')
        os.makedirs(premakeTargetFolder, exist_ok=True)
        urllib.request.urlretrieve(premakeDownloadUrl, premakeTargetZip)

        if premakeDownloadUrl.endswith('zip'):
            with zipfile.ZipFile(premakeTargetZip, 'r') as zipFile:
                zipFile.extract('premake5.exe', premakeTargetFolder)
        else:
            with tarfile.open(premakeTargetZip, 'r') as tarFile:
                tarFile.extractall(premakeTargetFolder, filter=tarfile.data_filter)
            os.chmod(premakeTargetExe, os.stat(premakeTargetExe).st_mode | stat.S_IEXEC)

def ConanBuild(conf, arch):
    return (
        'conan', 'install', '.', 
        '--build', 'missing', 
        '--output-folder=./dependencies', 
        '--deployer=full_deploy', 
        f'--settings=arch={arch}',
        f'--settings=build_type={conf}',
        '--settings=compiler.cppstd=20',
    )

if __name__ == '__main__':
    # Conan skip evaluation
    skipConan = False
    if len(sys.argv) > 1 and sys.argv[1] == 'skip_conan':
        skipConan = True

    # Download tool applications
    DownloadPremake()

    # Get system architecture
    arch = mox.GetPlatformInfo()
    print(f'Generating project on { platform.machine().lower() } for conan={ arch["conan_arch"] } and premake={arch["premake_arch"]}')

    # Version detection
    version = mox.GetAppVersion()
    print(f'Version is { version }')

    # Generate conan project
    if not skipConan:
        subprocess.run(ConanBuild('Debug', arch["conan_arch"]))
        subprocess.run(ConanBuild('Release', arch["conan_arch"]))

    # Run premake5
    premakeGenerator = GetPremakeGenerator()
    subprocess.run((
        './dependencies/premake5/premake5', 
        f'--mox_conan_arch={ arch["conan_arch"] }',
        f'--mox_premake_arch={ arch["premake_arch"] }',
        f'--mox_version={ version }',
        '--file=./scripts/premake5.lua', 
        premakeGenerator
    ))
