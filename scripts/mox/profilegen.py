"""
Generates conan profiles

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
import re
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
    "18.0": "195",
    "18.1": "195",
    "18.2": "195",
    "18.3": "195",
    "18.4": "195",
    "18.5": "195",
    "18.6": "195",
    "18.7": "195",
    "18.8": "195",
    "18.9": "195",
}

class INIProfileGen:
    def __init__(self, filename: str, architecture: str, os: str):
        self.filename = filename
        # All pairs are buffered per section and only written out by Save().
        # This allows Add* calls in any order and guarantees every section
        # header appears exactly once (conan rejects duplicated sections).
        self.sections = {}
        # Base conan profile settings
        self.SetPair("settings", "arch", architecture)
        if os != "Darwin":
            self.SetPair("settings", "os", os)
        else:
            self.SetPair("settings", "os", "Macos")
        self.SetPair("settings", "build_type", "Release")

    def AddGcc(self, cppversion: str, gccversion: str, abiversion: str):
        self.SetPair("settings", "compiler", "gcc")
        self.SetPair("settings", "compiler.cppstd", cppversion)
        self.SetPair("settings", "compiler.version", gccversion)
        self.SetPair("settings", "compiler.libcxx", abiversion)

    def AddClang(self, cppversion: str, clangversion: str, abiversion: str):
        self.SetPair("settings", "compiler", "clang")
        self.SetPair("settings", "compiler.cppstd", cppversion)
        self.SetPair("settings", "compiler.version", clangversion)
        self.SetPair("settings", "compiler.libcxx", abiversion)

    def AddMSVC(self, cppversion: str, msvcversion: str, runtime: str):
        self.SetPair("settings", "compiler", "msvc")
        self.SetPair("settings", "compiler.cppstd", cppversion)
        self.SetPair("settings", "compiler.version", msvcversion)
        self.SetPair("settings", "compiler.runtime", runtime)

    def AddTempFolder(self, is_windows: bool, tempfolder: str):
        if is_windows:
            self.SetPair("buildenv", "TEMP", tempfolder)
            self.SetPair("buildenv", "TMP", tempfolder)
        else:
            self.SetPair("buildenv", "TMPDIR", tempfolder)
            self.SetPair("buildenv", "TEMP", tempfolder)
            self.SetPair("buildenv", "TMP", tempfolder)

    def AddGccCrossLink(self, compilerprefix: str):
        self.SetPair("buildenv", "CC", f"{compilerprefix}-gcc")
        self.SetPair("buildenv", "CXX", f"{compilerprefix}-g++")
        self.SetPair("buildenv", "LD", f"{compilerprefix}-ld")

    def SetPair(self, section: str, key: str, value: str):
        self.sections.setdefault(section, {})[key] = value

    def Save(self):
        with open(self.filename, "w", encoding="utf-8") as file:
            for section, pairs in self.sections.items():
                file.write(f"[{section}]\n")
                for key, value in pairs.items():
                    file.write(f"{key}={value}\n")

def ProfileGen(path: str, architecture: str, cppversion: str, tempfolder: str, vsVersion: str):
    is_windows = platform.system().lower() == "windows"
    is_macos = platform.system().lower() == "darwin"
    platformInfo = mox.GetPlatformInfo(architecture)
    arch = platformInfo["conan_arch"]

    gen = INIProfileGen(path, arch, platform.system())
    if is_windows:
        vs_version = moxwin.FindPreferedVisualStudio(vsVersion)["catalog"]["buildVersion"]
        vs_version = ".".join(vs_version.split(".")[:2])
        msvc_version = VS_MSVC_MAPPINGS[vs_version]
        gen.AddMSVC(cppversion, msvc_version, "dynamic")
    elif is_macos:
        clang_version = re.search(r"Apple clang version (\d\d)\.\d\.\d", subprocess.check_output(("clang", "--version"), text=True).strip()).group(1)
        gen.AddClang(cppversion, clang_version, "libc++")
    else:
        gcc_version = subprocess.check_output(("g++", "-dumpversion"), text=True).strip()
        gen.AddGcc(cppversion, gcc_version, "libstdc++11")
        if architecture.lower() != platform.machine().lower():
            gen.AddGccCrossLink(platformInfo["gcc_linux_prefix"])
    gen.AddTempFolder(is_windows, tempfolder)
    gen.Save()
