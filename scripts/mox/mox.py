"""
Generic util functions

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
import os
import platform
import datetime

MOX_ARCH_MAP = {
    # x86 32bit
    "i386":         { "conan_arch": "x86",      "premake_arch": "x86" },        # Seen on linux
    "i686":         { "conan_arch": "x86",      "premake_arch": "x86" },        # Seen on linux
    "x86":          { "conan_arch": "x86",      "premake_arch": "x86" },        # Seen on windows

    # x86 64bit
    "amd64":        { "conan_arch": "x86_64",   "premake_arch": "x86_64" },     # Seen on windows
    "x86_64":       { "conan_arch": "x86_64",   "premake_arch": "x86_64" },     # Seen on windows and linux

    # ARM (32bit)
    "arm":          { "conan_arch": "armv7",    "premake_arch": "ARM" },        # Seen on linux

    # ARM64 
    "arm64":        { "conan_arch": "armv8",    "premake_arch": "ARM64" },      # Seen on windows
    "aarch64":      { "conan_arch": "armv8",    "premake_arch": "ARM64" },      # Seen on linux
    "aarch64_be":   { "conan_arch": "armv8",    "premake_arch": "ARM64" },      # Seen on linux
    "armv8b":       { "conan_arch": "armv8",    "premake_arch": "ARM64" },      # Seen on linux
    "armv8l":       { "conan_arch": "armv8",    "premake_arch": "ARM64" },      # Seen on linux
}

def GetPlatformInfo():
    arch = platform.machine().lower()
    if not arch in MOX_ARCH_MAP:
        raise ValueError(f'Architecture "{arch}" is not supported by MoxPP!')
    return MOX_ARCH_MAP[arch]

def GetFilename(product, version, system, conf, arch, extension):
    return f'{product}-{version}-{system}-{conf}-{arch}.{extension}' # project_name-1.0.0-Windows-Release-x86_64.zip

def AutomaticFilename(product, version, conf, extension):
    return GetFilename(product, version, platform.system(), conf, GetPlatformInfo()["premake_arch"], extension)

def GetAppVersion(default=""):
    version = os.environ.get("MOXPP_VERSION")
    if version is None:
        if len(default) > 0:
            return default
        return f"0.0.0+dev.{ datetime.datetime.now().strftime('%Y%m%d') }"
    return version
