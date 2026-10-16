"""
MDDPkg - MoxPP Deploy
Packs into a debian package (.deb) via dpkg-deb (debian based linux only)

Usage mirrors MDZip: add files / folders (destination = absolute linux install path),
declare metadata, dependencies and maintainer scripts, call Deploy().

Deploy() will:
  1. Skip (with a warning) when not on linux or when dpkg-deb is not available.
  2. Stage the package tree into ./build/dpkg/<name>/ (symlinks are preserved).
  3. Write DEBIAN/control (with a self computed Installed-Size), md5sums, conffiles
     and the maintainer scripts (preinst, postinst, prerm, postrm).
  4. Run "dpkg-deb --build --root-owner-group" into ./deploy/<filename>

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
import os
import re
import math
import shutil
import hashlib
import platform

from .mox import RunChecked, GetPlatformInfo

# premake arch -> debian arch
DEB_ARCH_MAP = {
    'x86':    'i386',
    'x86_64': 'amd64',
    'ARM':    'armhf',
    'ARM64':  'arm64',
}

MAINTAINER_SCRIPTS = ('preinst', 'postinst', 'prerm', 'postrm')

# API kind -> control field
DEPENDENCY_FIELDS = {
    'pre-depends': 'Pre-Depends',
    'depends':     'Depends',
    'recommends':  'Recommends',
    'suggests':    'Suggests',
    'conflicts':   'Conflicts',
    'breaks':      'Breaks',
    'replaces':    'Replaces',
    'provides':    'Provides',
}

def _n(name):
    """Normalize a destination to a relative posix path ("/usr/bin/app" -> "usr/bin/app")"""
    return name.replace('\\', '/').strip('/')

def _package_name(name):
    name = name.lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name):
        raise ValueError(f'MDDPkg: Invalid debian package name "{name}" (use lowercase letters, digits, +, -, .)')
    return name

def _package_version(version):
    version = version[1:] if version.startswith(('v', 'V')) else version
    if not re.fullmatch(r'[0-9][A-Za-z0-9.+~:-]*', version):
        raise ValueError(f'MDDPkg: Invalid debian version "{version}" (must start with a digit)')
    return version

class MDDPkg:
    def __init__(self, filename, packageName, version, arch, deployDir='./deploy'):
        os.makedirs(deployDir, exist_ok=True)
        self.__filename = filename
        self.__path = deployDir + "/" + filename
        self.__package = _package_name(packageName)
        self.__version = _package_version(version)
        self.__arch = DEB_ARCH_MAP[GetPlatformInfo(arch)["premake_arch"]]
        self.__files = []                   # (src, dst, mode)
        self.__symlinks = []                # (dst, target)
        self.__dependencies = {}            # control field -> [spec]
        self.__fields = {}                  # custom control fields
        self.__scripts = {name: [] for name in MAINTAINER_SCRIPTS}
        self.__scriptMode = 0o755

        # Meta
        self.__maintainer = None
        self.__description = None
        self.__longDescription = None
        self.__section = None
        self.__priority = None
        self.__homepage = None

    # ------------------------------------------------------------------
    # Files (destinations are absolute linux install paths)
    # ------------------------------------------------------------------

    def AddFile(self, file, name, mode=None):
        """Adds a file. mode: e.g. 0o755, defaults to 0o755 for executable sources and 0o644 otherwise.
        A source that is a symlink is packaged as a symlink with its original target."""
        if os.path.islink(file):
            self.AddSymlink(name, os.readlink(file))
            return
        if mode is None:
            mode = 0o755 if os.access(file, os.X_OK) else 0o644
        self.__files.append((file, _n(name), mode))

    def AddFolder(self, folder, name, mode=None):
        """Adds a folder recursively. Symlinked files and folders are preserved as symlinks."""
        for root, dirs, files in os.walk(folder, followlinks=False):
            rel = os.path.relpath(root, folder).replace('\\', '/')
            arc_dir = _n(name) if rel == '.' else f'{_n(name)}/{rel}'
            for d in list(dirs):
                src = os.path.join(root, d)
                if os.path.islink(src):
                    self.AddSymlink(f'{arc_dir}/{d}', os.readlink(src))
                    dirs.remove(d)
            for file in files:
                self.AddFile(os.path.join(root, file), f'{arc_dir}/{file}', mode)

    def AddSymlink(self, name, target):
        """Adds a symlink at name pointing to target (absolute or relative, written verbatim)"""
        self.__symlinks.append((_n(name), target))

    # ------------------------------------------------------------------
    # Control file
    # ------------------------------------------------------------------

    def SetMeta(self, maintainer=None, description=None, section=None, priority=None, homepage=None, longDescription=None):
        if maintainer is not None: self.__maintainer = maintainer
        if description is not None: self.__description = description
        if section is not None: self.__section = section
        if priority is not None: self.__priority = priority
        if homepage is not None: self.__homepage = homepage
        if longDescription is not None: self.__longDescription = longDescription

    def AddDependency(self, package, version=None, kind='depends'):
        """Adds a package relation, e.g. AddDependency("libssl3", ">= 3.0"). kind: depends, pre-depends,
        recommends, suggests, conflicts, breaks, replaces, provides"""
        if kind not in DEPENDENCY_FIELDS:
            raise ValueError(f'MDDPkg: Unknown dependency kind "{kind}" (use {", ".join(DEPENDENCY_FIELDS)})')
        spec = f'{package} ({version})' if version else package
        self.__dependencies.setdefault(DEPENDENCY_FIELDS[kind], []).append(spec)

    def SetControlField(self, field, value):
        """Sets any additional control field"""
        self.__fields[field] = value

    # ------------------------------------------------------------------
    # Maintainer scripts (every call appends)
    # ------------------------------------------------------------------

    def AppendScript(self, name, lines):
        """Appends lines (str, may be multi-line, or list of str) to the maintainer script name (preinst, postinst, prerm, postrm)"""
        if name not in MAINTAINER_SCRIPTS:
            raise ValueError(f'MDDPkg: Unknown maintainer script "{name}" (use {", ".join(MAINTAINER_SCRIPTS)})')
        if isinstance(lines, str):
            lines = lines.replace('\r\n', '\n').split('\n')
        self.__scripts[name].extend(lines)

    def AppendPreInstall(self, lines):
        self.AppendScript('preinst', lines)

    def AppendPostInstall(self, lines):
        self.AppendScript('postinst', lines)

    def AppendPreRemove(self, lines):
        self.AppendScript('prerm', lines)

    def AppendPostRemove(self, lines):
        self.AppendScript('postrm', lines)

    def SetScriptMode(self, mode=0o755):
        """File mode of all maintainer scripts (dpkg accepts 0o755 to 0o775)"""
        self.__scriptMode = mode

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def __Control(self, installedSize):
        lines = [
            f'Package: {self.__package}',
            f'Version: {self.__version}',
            f'Architecture: {self.__arch}',
            f'Maintainer: {self.__maintainer}',
            f'Installed-Size: {installedSize}',
        ]
        if self.__section: lines.append(f'Section: {self.__section}')
        if self.__priority: lines.append(f'Priority: {self.__priority}')
        if self.__homepage: lines.append(f'Homepage: {self.__homepage}')
        for field in DEPENDENCY_FIELDS.values():
            if field in self.__dependencies:
                lines.append(f'{field}: {", ".join(self.__dependencies[field])}')
        for field, value in self.__fields.items():
            lines.append(f'{field}: {value}')
        lines.append(f'Description: {self.__description}')
        if self.__longDescription:
            for line in self.__longDescription.replace('\r\n', '\n').strip('\n').split('\n'):
                lines.append(f' {line}' if line.strip() else ' .')
        return '\n'.join(lines) + '\n'

    def __Script(self, lines):
        return '#!/bin/bash\nset -e\n\n' + '\n'.join(lines) + '\n'

    # ------------------------------------------------------------------
    # Deploy
    # ------------------------------------------------------------------

    def Deploy(self):
        if platform.system().lower() != 'linux' or shutil.which('dpkg-deb') is None:
            print(f'MDDPkg: dpkg-deb not available on this system, skipping {self.__filename}')
            return

        if not self.__maintainer or not self.__description:
            raise ValueError('MDDPkg: SetMeta(maintainer=..., description=...) is required by dpkg')

        # Staging (always from scratch, stale files would be packaged)
        staging = os.path.abspath(f'./build/dpkg/{os.path.splitext(self.__filename)[0]}')
        if os.path.isdir(staging):
            shutil.rmtree(staging)
        os.makedirs(staging)
        for src, dst, mode in self.__files:
            target = os.path.join(staging, dst)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(src, target, follow_symlinks=True)
            os.chmod(target, mode)
        for dst, target in self.__symlinks:
            link = os.path.join(staging, dst)
            os.makedirs(os.path.dirname(link), exist_ok=True)
            os.symlink(target, link)

        # Installed size (KiB, regular files only) and md5sums
        size = 0
        md5sums = []
        conffiles = []
        for root, dirs, files in os.walk(staging, followlinks=False):
            for file in files:
                path = os.path.join(root, file)
                if os.path.islink(path):
                    continue
                rel = os.path.relpath(path, staging).replace('\\', '/')
                size += os.lstat(path).st_size
                with open(path, 'rb') as f:
                    md5sums.append(f'{hashlib.md5(f.read()).hexdigest()}  {rel}')
                if rel.startswith('etc/'):
                    conffiles.append(f'/{rel}')
        installedSize = math.ceil(size / 1024)

        # DEBIAN control folder
        debian = os.path.join(staging, 'DEBIAN')
        os.makedirs(debian)
        os.chmod(debian, 0o755)
        with open(os.path.join(debian, 'control'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(self.__Control(installedSize))
        with open(os.path.join(debian, 'md5sums'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sorted(md5sums)) + '\n')
        if conffiles:
            with open(os.path.join(debian, 'conffiles'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(sorted(conffiles)) + '\n')
        for name, lines in self.__scripts.items():
            if not lines:
                continue
            script = os.path.join(debian, name)
            with open(script, 'w', encoding='utf-8', newline='\n') as f:
                f.write(self.__Script(lines))
            os.chmod(script, self.__scriptMode)

        # Build
        print(f'Building debian package {self.__path} ...')
        RunChecked(('dpkg-deb', '--build', '--root-owner-group', staging, os.path.abspath(self.__path)))
