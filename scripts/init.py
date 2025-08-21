"""
Project initialization script
This will initialize your VisualStudio solution / Your makefile

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
import moxwin

import os
import re
import sys
import stat
import zipfile
import tarfile
import platform
import argparse
import subprocess
import urllib.request

def GetExecutable(exe):
    if sys.platform.startswith('linux'):
        return exe
    else:
        return f'{exe}.exe'

def GetPremakeGenerator():
    if sys.platform.startswith('linux'):
        return 'gmake'
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

def DownloadPremake(version = '5.0.0-beta7'):
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

def ConanBuild(conf, host_profile, build_profile):
    return (
        'conan', 'install', '.',
        '--build', 'missing',
        f'--profile:host=./profiles/{host_profile}',
        f'--profile:build=./profiles/{build_profile}',
        f'--output-folder=./dependencies',
        f'--deployer=full_deploy',
        f'--settings=build_type={conf}'
    )

if __name__ == '__main__':
    # Cli
    p = argparse.ArgumentParser(prog="init.py", allow_abbrev=False)
    p.add_argument("--skip-conan", action="store_true", help="Skip Conan evaluation")
    p.add_argument("--arch", default=platform.machine().lower(), help="Alternative (cross compile) architecture")
    args = p.parse_args()

    skipConan = args.skip_conan
    arch = args.arch

    # Generate conan profiles
    os.makedirs("./profiles/", exist_ok=True)
    cpp_version = re.search(r'(\d+)', mox.ExtractLuaDef("./mox.lua", "cmox_cpp_version")).group(1)
    mox.ProfileGen("./profiles/build", platform.machine().lower(), cpp_version)
    mox.ProfileGen(f"./profiles/host_{arch}", arch, cpp_version)

    # Download tool applications
    DownloadPremake()

    # Get system architecture
    buildArch = mox.GetThisPlatformInfo()
    hostArch = mox.GetPlatformInfo(arch)
    print(f'Generating project on { platform.machine().lower() } (conan={ buildArch["conan_arch"] } and premake={buildArch["premake_arch"]})')
    print(f'for {arch} (conan={ hostArch["conan_arch"] } and premake={hostArch["premake_arch"]})')

    # Version detection
    version = mox.GetAppVersion()
    print(f'Version is { version }')

    # Generate conan project
    if not skipConan:
        subprocess.run(ConanBuild('Debug', f'host_{arch}', 'build'))
        subprocess.run(ConanBuild('Release', f'host_{arch}', 'build'))
        # Copy conan dlls
        subprocess.run((
            sys.executable,
            './scripts/copydlls.py',
            arch
        ))

    # GCC Prefix
    gccPrefix = hostArch[f'gcc_{ "linux" if sys.platform.startswith("linux") else "windows"  }_prefix'] + '-'

    # Run premake5
    premakeGenerator = GetPremakeGenerator()
    subprocess.run((
        './dependencies/premake5/premake5',
        f'--mox_conan_arch={ hostArch["conan_arch"] }',
        f'--mox_premake_arch={ hostArch["premake_arch"] }',
        f'--mox_gcc_prefix={ gccPrefix }',
        f'--mox_version={ version }',
        '--file=./scripts/premake5.lua',
        premakeGenerator
    ))
