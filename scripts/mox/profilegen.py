"""
Generates conan profiles

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
import platform
import subprocess

VS_MSVC_MAPPINGS = {
    "17.0": "193",
    "17.1": "193",
    "17.2": "193",
    "17.3": "193",
    "17.4": "193",
    "17.5": "193",
    "17.6": "193",
    "17.7": "193",
    "17.8": "193",
    "17.9": "193",
    "17.10": "194",
    "17.11": "194",
    "17.12": "194",
    "17.13": "194",
    "17.14": "194",
}

class INIProfileGen:
    def __init__(self, filename: str, architecture: str, os: str):
        # Open file
        self.file = open(filename, "w", encoding="utf-8")
        # Begin conan profile section
        self.StartSection("settings")
        self.WritePair("arch", architecture)
        self.WritePair("os", os)

    def __del__(self):
        # Close file
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def AddGcc(self, cppversion: str, gccversion: str, abiversion: str):
        self.WritePair("compiler", "gcc")
        self.WritePair("compiler.cppstd", cppversion)
        self.WritePair("compiler.version", gccversion)
        self.WritePair("compiler.libcxx", abiversion)

    def AddMSVC(self, cppversion: str, msvcversion: str, runtime: str):
        self.WritePair("compiler", "msvc")
        self.WritePair("compiler.cppstd", cppversion)
        self.WritePair("compiler.version", msvcversion)
        self.WritePair("compiler.runtime", runtime)

    def AddGccCrossLink(self, compilerprefix: str):
        self.StartSection("buildenv")
        self.WritePair("CC", f"{compilerprefix}-gcc")
        self.WritePair("CXX", f"{compilerprefix}-g++")
        self.WritePair("LD", f"{compilerprefix}-ld")

    def StartSection(self, section: str):
        self.file.write(f"[{section}]\n")

    def WritePair(self, key: str, value: str):
        self.file.write(f"{key}={value}\n")

def ProfileGen(path: str, architecture: str, cppversion: str):
    is_windows = platform.system().lower() == "windows"
    platformInfo = mox.GetPlatformInfo(architecture)
    arch = platformInfo["conan_arch"]

    gen = INIProfileGen(path, arch, platform.system())
    if is_windows:
        vs_version = moxwin.FindLatestVisualStudio()[0]["catalog"]["buildVersion"]
        vs_version = ".".join(vs_version.split(".")[:2])
        msvc_version = VS_MSVC_MAPPINGS[vs_version]
        gen.AddMSVC(cppversion, msvc_version, "dynamic")
    else:
        gcc_version = subprocess.check_output(("g++", "-dumpversion"), text=True).strip()
        gen.AddGcc(cppversion, gcc_version, "libstdc++11")
        if architecture.lower() != platform.machine().lower():
            gen.AddGccCrossLink(platformInfo["gcc_linux_prefix"])
