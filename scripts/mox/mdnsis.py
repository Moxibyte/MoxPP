"""
MDNSIS - MoxPP Deploy
Packs into a NSIS (Nullsoft Scriptable Install System) installer (Windows only)

Usage mirrors MDZip: add files / folders, configure optional features, call Deploy().
Files, shortcuts and actions bind to the most recent StartComponent() call. Everything
added before the first StartComponent() lands in a hidden, always installed section.

Deploy() will:
  1. Skip (with a warning) when not running on windows.
  2. Bootstrap a portable NSIS into ./dependencies/nsis (if not present).
  3. Download NSIS plug-ins when a feature requires them (EmbedHTML for html licenses).
  4. Generate a Modern UI 2 installer script into ./build/nsis/<name>/installer.nsi
  5. Compile it with makensis into ./deploy/<filename>

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
import sys
import moxwin
import zipfile
import pathlib
import platform
import urllib.request

from .mox import RunChecked, GetPlatformInfo

# Portable NSIS release used for bootstrapping (zip contains a "nsis-<version>/" top level folder)
NSIS_VERSION = '3.13'
NSIS_URL = f'https://sourceforge.net/projects/nsis/files/NSIS%203/{NSIS_VERSION}/nsis-{NSIS_VERSION}.zip/download'

# Plug-ins that are downloaded on demand. The zip files use the native NSIS layout
# (Plugins/x86-unicode/<name>.dll, Docs/..., Examples/...) and are extracted into the nsis folder.
NSIS_PLUGINS = {
    'EmbedHTML': 'https://nsis.sourceforge.io/mediawiki/images/7/7c/EmbedHTML.zip',
}

# Default texts for the custom (non MUI) strings. Can be overridden per language via SetStrings()
DEFAULT_STRINGS = {
    'MOX_README_TITLE':    'Information',
    'MOX_README_SUBTITLE': 'Please read the following information before installing $(^NameDA).',
}

STRING_KEYS = {
    'readmeTitle':    'MOX_README_TITLE',
    'readmeSubtitle': 'MOX_README_SUBTITLE',
}

SHORTCUT_LOCATIONS = ('startmenu', 'desktop')

def _q(text):
    """Quote a string for NSIS (double quoted, escapes "). Note: "$" keeps its NSIS meaning (use "$$" for a literal)"""
    text = str(text).replace('"', '$\\"')
    return f'"{text}"'

def _n(name):
    """Normalize an archive style name ("/dir/file") to a windows relative path ("dir\\file")"""
    return name.replace('\\', '/').strip('/').replace('/', '\\')

def _target(path):
    """Resolve a path for use inside the installer: relative paths are placed below $INSTDIR"""
    if path.startswith('$') or os.path.isabs(path):
        return path
    return f'$INSTDIR\\{_n(path)}'

def _version_numeric(version):
    """Build a X.X.X.X version string (required by VIProductVersion) from any version string"""
    parts = [min(int(p), 65535) for p in re.findall(r'\d+', version)][:4]
    while len(parts) < 4:
        parts.append(0)
    return '.'.join(str(p) for p in parts)

class _Component:
    def __init__(self, path, required=False, default=True, description=None):
        self.path = path                    # "Group/Leaf" ("" for the hidden default section)
        self.required = required
        self.default = default
        self.description = description
        self.files = []                     # (src, dst)
        self.shortcuts = []                 # (target, name, location, args, icon)
        self.postInstall = []               # (exe, args, visible)
        self.preUninstall = []              # (exe, args, visible)
        self.redist = None                  # absolute path to vc_redist.x64.exe

    def IsEmpty(self):
        return not (self.files or self.shortcuts or self.postInstall or self.preUninstall or self.redist)

class MDNSIS:
    def __init__(self, filename, appName, version, arch, deployDir='./deploy', nsisDir='./dependencies/nsis'):
        os.makedirs(deployDir, exist_ok=True)
        self.__filename = filename
        self.__path = deployDir + "/" + filename
        self.__nsisDir = nsisDir
        self.__appName = appName
        self.__version = version
        self.__arch = GetPlatformInfo(arch)["premake_arch"]

        # Components
        self.__default = _Component('', required=True)
        self.__components = {}              # path -> _Component (insertion ordered)
        self.__current = None

        # Meta
        self.__publisher = ''
        self.__description = ''
        self.__url = ''
        self.__copyright = ''
        self.__installFolderName = appName

        # Features
        self.__mainExe = None
        self.__readmeText = None
        self.__readmeFile = None
        self.__license = None
        self.__scopes = ('machine', 'user')
        self.__runAfterInstall = False
        self.__runAfterInstallText = None
        self.__languages = ('English',)
        self.__installIcon = None
        self.__uninstallIcon = None
        self.__headerImage = None
        self.__headerImageRight = False
        self.__welcomeImage = None
        self.__unwelcomeImage = None
        self.__abortWarning = True
        self.__strings = {}

    # ------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------

    def StartComponent(self, path, required=False, default=True, description=None):
        """Starts (or re-selects) a component. Following AddFile/AddFolder/AddShortcut/Add*Action calls bind to it.
        Use "/" for hierarchy: "Shortcuts/Desktop" creates a group "Shortcuts" with a leaf "Desktop"."""
        path = '/'.join(p.strip() for p in path.replace('\\', '/').split('/') if p.strip())
        if not path:
            raise ValueError('MDNSIS: Component path must not be empty')
        if path in self.__components:
            self.__current = self.__components[path]
            return self.__current
        for existing in self.__components:
            if existing.startswith(path + '/') or path.startswith(existing + '/'):
                raise ValueError(f'MDNSIS: Component "{path}" conflicts with "{existing}" (groups and leaves may not share a name)')
        component = _Component(path, required, default, description)
        self.__components[path] = component
        self.__current = component
        return component

    def __Target(self):
        return self.__current if self.__current is not None else self.__default

    # ------------------------------------------------------------------
    # Files (same semantics as MDZip)
    # ------------------------------------------------------------------

    def AddFile(self, file, name):
        self.__Target().files.append((file, name))

    def AddFolder(self, folder, name):
        for root, dirs, files in os.walk(folder):
            rel = os.path.relpath(root, folder)
            arc_dir = name if rel == '.' else f'{name}/{rel}'
            for file in files:
                self.AddFile(os.path.join(root, file), f'{arc_dir}/{file}')

    def AddMSVCRedists(self, vsVersion=None):
        """Bundles the msvc redist installer, runs it silently during installation and removes it afterwards"""
        if sys.platform.startswith('win'):
            vswhere = moxwin.FindPreferedVisualStudio(vsVersion)
            vspath = moxwin.GetVisualStudioPath(vswhere)
            redist_base_dir = pathlib.Path(vspath) / 'VC' / 'Redist' / 'MSVC'
            redist_canidates = sorted(redist_base_dir.glob('v*/vc_redist.x64.exe'), reverse=True)
            if redist_canidates and len(redist_canidates) >= 1:
                self.__Target().redist = str(redist_canidates[0])
            else:
                print('ERROR: Failed to find msvc redist installer!')

    # ------------------------------------------------------------------
    # Shortcuts and actions (bound to the current component)
    # ------------------------------------------------------------------

    def AddShortcut(self, target, name, location='startmenu', args='', icon=None):
        """Creates a shortcut "<name>.lnk" to target (relative to the install dir) in the start menu folder or on the desktop"""
        if location not in SHORTCUT_LOCATIONS:
            raise ValueError(f'MDNSIS: Unknown shortcut location "{location}" (use {", ".join(SHORTCUT_LOCATIONS)})')
        self.__Target().shortcuts.append((target, name, location, args, icon))

    def AddPostInstallAction(self, exe, args='', visible=False):
        """Runs exe (relative to the install dir unless absolute or starting with $) after the component's files were installed.
        Hidden actions run via nsExec with their output in the install log, visible ones via ExecWait."""
        self.__Target().postInstall.append((exe, args, visible))

    def AddPreUninstallAction(self, exe, args='', visible=False):
        """Runs exe before the uninstaller removes any files. Skipped when exe does not exist (component not installed)."""
        self.__Target().preUninstall.append((exe, args, visible))

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def SetMeta(self, publisher=None, description=None, url=None, copyright=None, installFolderName=None):
        if publisher is not None: self.__publisher = publisher
        if description is not None: self.__description = description
        if url is not None: self.__url = url
        if copyright is not None: self.__copyright = copyright
        if installFolderName is not None: self.__installFolderName = installFolderName

    def SetMainExecutable(self, relativeExe):
        """Executable (relative to the install dir) used for the display icon and run after install"""
        self.__mainExe = _n(relativeExe)

    def SetReadme(self, text=None, file=None):
        """Free text information page displayed before the installation"""
        self.__readmeText = text
        self.__readmeFile = file

    def SetLicense(self, file):
        """License page. .html/.htm files are rendered via the EmbedHTML plug-in, .txt/.rtf natively"""
        self.__license = file

    def SetInstallScopes(self, scopes=('machine', 'user')):
        """Supported install scopes. When both are supported the end user chooses inside the installer"""
        scopes = tuple(scopes)
        for scope in scopes:
            if scope not in ('machine', 'user'):
                raise ValueError(f'Unknown install scope "{scope}" (use "machine" and/or "user")')
        if len(scopes) == 0:
            raise ValueError('At least one install scope is required')
        self.__scopes = scopes

    def SetRunAfterInstall(self, enabled=True, text=None):
        """Adds a "Run <app>" checkbox to the finish page (requires SetMainExecutable)"""
        self.__runAfterInstall = enabled
        self.__runAfterInstallText = text

    def SetLanguages(self, languages=('English',)):
        """MUI language names (e.g. "English", "German"). More than one language shows a language dialog"""
        languages = tuple(languages)
        if len(languages) == 0:
            raise ValueError('At least one language is required')
        self.__languages = languages

    def SetIcons(self, installIcon=None, uninstallIcon=None):
        self.__installIcon = installIcon
        self.__uninstallIcon = uninstallIcon

    def SetTheme(self, headerImage=None, headerImageRight=False, welcomeImage=None, unwelcomeImage=None, abortWarning=True):
        """Optional custom theming (bitmaps). Header: 150x57, welcome/finish: 164x314"""
        self.__headerImage = headerImage
        self.__headerImageRight = headerImageRight
        self.__welcomeImage = welcomeImage
        self.__unwelcomeImage = unwelcomeImage
        self.__abortWarning = abortWarning

    def SetStrings(self, language, **strings):
        """Override custom strings for a language: readmeTitle, readmeSubtitle"""
        for key in strings:
            if key not in STRING_KEYS:
                raise ValueError(f'Unknown string "{key}" (use {", ".join(STRING_KEYS)})')
        self.__strings.setdefault(language, {}).update(strings)

    # ------------------------------------------------------------------
    # Bootstrapping
    # ------------------------------------------------------------------

    def __Download(self, url, target):
        print(f'Downloading {url} ...')
        urllib.request.urlretrieve(url, target)

    def __MakensisPath(self):
        return os.path.abspath(os.path.join(self.__nsisDir, 'makensis.exe'))

    def __EnsureNsis(self):
        makensis = self.__MakensisPath()
        if os.path.exists(makensis):
            return
        print(f'Bootstrapping portable NSIS {NSIS_VERSION} into {self.__nsisDir} ...')
        os.makedirs(self.__nsisDir, exist_ok=True)
        tmp = os.path.join(self.__nsisDir, 'nsis.tmp')
        self.__Download(NSIS_URL, tmp)
        with zipfile.ZipFile(tmp, 'r') as zipFile:
            for member in zipFile.infolist():
                # Strip the "nsis-<version>/" top level folder
                parts = member.filename.split('/', 1)
                if len(parts) < 2 or parts[1] == '':
                    continue
                target = os.path.join(self.__nsisDir, parts[1])
                if member.is_dir():
                    os.makedirs(target, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with zipFile.open(member) as src, open(target, 'wb') as dst:
                        dst.write(src.read())
        os.remove(tmp)

    def __EnsurePlugin(self, name):
        dll = os.path.join(self.__nsisDir, 'Plugins', 'x86-unicode', f'{name}.dll')
        if os.path.exists(dll):
            return
        print(f'Installing NSIS plug-in {name} ...')
        tmp = os.path.join(self.__nsisDir, f'{name}.tmp')
        self.__Download(NSIS_PLUGINS[name], tmp)
        with zipfile.ZipFile(tmp, 'r') as zipFile:
            zipFile.extractall(self.__nsisDir)
        os.remove(tmp)

    # ------------------------------------------------------------------
    # Script generation helpers
    # ------------------------------------------------------------------

    def __IsHtmlLicense(self):
        return self.__license is not None and self.__license.lower().endswith(('.html', '.htm'))

    def __RegKey(self):
        if self.__publisher:
            return f'Software\\{self.__publisher}\\{self.__appName}'
        return f'Software\\{self.__appName}'

    def __UninstallRegKey(self):
        return f'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{self.__appName}'

    def __Is64Bit(self):
        return self.__arch in ('x86_64', 'ARM64')

    def __LangId(self, language):
        return f'${{LANG_{language.upper()}}}'

    def __AllComponents(self):
        return [self.__default] + list(self.__components.values())

    def __ShortcutPath(self, name, location):
        if location == 'desktop':
            return f'$DESKTOP\\{name}.lnk'
        return f'$SMPROGRAMS\\{self.__appName}\\{name}.lnk'

    def __EmitAction(self, w, indent, exe, args, visible):
        cmd = f'"{_target(exe)}"' + (f' {args}' if args else '')
        if visible:
            w(f"{indent}ExecWait '{cmd}'")
        else:
            w(f"{indent}nsExec::ExecToLog '{cmd}'")
            w(f'{indent}Pop $0')

    def __EmitComponentBody(self, w, component):
        files = [(os.path.abspath(src), _n(dst)) for src, dst in component.files]
        if component.required and component.path:
            w('    SectionIn RO')
        w('    SetOverwrite on')
        currentDir = None
        for src, dst in files:
            dstDir = os.path.dirname(dst)
            if dstDir != currentDir:
                currentDir = dstDir
                w(f'    SetOutPath "$INSTDIR\\{dstDir}"' if dstDir else '    SetOutPath "$INSTDIR"')
            w(f'    File "/oname={os.path.basename(dst)}" {_q(src)}')
        w('    SetOutPath "$INSTDIR"')
        for target, name, location, args, icon in component.shortcuts:
            if location == 'startmenu':
                w(f'    CreateDirectory "$SMPROGRAMS\\{self.__appName}"')
            iconArg = f' "{_target(icon)}"' if icon else ''
            w(f'    CreateShortcut "{self.__ShortcutPath(name, location)}" "{_target(target)}" {_q(args)}{iconArg}')
        if component.redist:
            w(f'    File "/oname=vc_redist.x64.exe" {_q(os.path.abspath(component.redist))}')
            self.__EmitAction(w, '    ', 'vc_redist.x64.exe', '/install /quiet /norestart', False)
            w('    Delete "$INSTDIR\\vc_redist.x64.exe"')
        for exe, args, visible in component.postInstall:
            self.__EmitAction(w, '    ', exe, args, visible)

    def __EmitComponentTree(self, w):
        """Emit SectionGroup / Section blocks following the first-appearance order of the component paths"""
        # Build an ordered tree. A node is a list of children, each either
        # ('group', segment, childNode) or ('leaf', component), in first-appearance order.
        root = []
        for component in self.__components.values():
            segments = component.path.split('/')
            node = root
            for segment in segments[:-1]:
                child = next((c for c in node if c[0] == 'group' and c[1] == segment), None)
                if child is None:
                    child = ('group', segment, [])
                    node.append(child)
                node = child[2]
            node.append(('leaf', component))

        counter = {'sec': 0, 'grp': 0}
        sectionIds = {}

        def emit(node, indent):
            for child in node:
                if child[0] == 'group':
                    counter['grp'] += 1
                    w(f'{indent}SectionGroup /e {_q(child[1])} GRP_{counter["grp"]}')
                    emit(child[2], indent + '    ')
                    w(f'{indent}SectionGroupEnd')
                    w('')
                else:
                    component = child[1]
                    counter['sec'] += 1
                    secId = f'SEC_{counter["sec"]}'
                    sectionIds[component.path] = secId
                    flag = '/o ' if (not component.required and not component.default) else ''
                    w(f'{indent}Section {flag}{_q(component.path.split("/")[-1])} {secId}')
                    self.__EmitComponentBody(w, component)
                    w(f'{indent}SectionEnd')
                    w('')

        emit(root, '')
        return sectionIds

    # ------------------------------------------------------------------
    # Script generation
    # ------------------------------------------------------------------

    def __GenerateScript(self, staging):
        app = self.__appName
        multiLang = len(self.__languages) > 1
        htmlLicense = self.__IsHtmlLicense()
        regKey = self.__RegKey()
        unRegKey = self.__UninstallRegKey()
        components = list(self.__components.values())
        hasOptional = any(not c.required for c in components)
        hasDescriptions = any(c.description for c in components)
        out = []
        w = out.append

        # --- Header ---
        w('; Auto-generated by MoxPP (mox.MDNSIS) - DO NOT EDIT MANUALLY')
        w('Unicode true')
        w('ManifestDPIAware true')
        w('SetCompressor /SOLID lzma')
        w(f'Name {_q(app)}')
        w(f'OutFile {_q(os.path.abspath(self.__path))}')
        w(f'BrandingText {_q(f"{app} {self.__version}")}')
        w('')

        # --- MultiUser (install scope) ---
        if len(self.__scopes) == 2:
            executionLevel = 'Highest'
        elif self.__scopes[0] == 'machine':
            executionLevel = 'Admin'
        else:
            executionLevel = 'Standard'
        w(f'!define MULTIUSER_EXECUTIONLEVEL {executionLevel}')
        w('!define MULTIUSER_MUI')
        w('!define MULTIUSER_INSTALLMODE_COMMANDLINE')
        w(f'!define MULTIUSER_INSTALLMODE_INSTDIR {_q(self.__installFolderName)}')
        if self.__Is64Bit():
            w('!define MULTIUSER_USE_PROGRAMFILES64')
        w(f'!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY {_q(regKey)}')
        w('!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME "InstallDir"')
        w(f'!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY {_q(regKey)}')
        w('!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME "InstallMode"')
        w('!include MultiUser.nsh')
        w('!include MUI2.nsh')
        w('!include FileFunc.nsh')
        w('!include LogicLib.nsh')
        w('')

        # --- Version information ---
        w(f'VIProductVersion "{_version_numeric(self.__version)}"')
        w(f'VIAddVersionKey "ProductName" {_q(app)}')
        w(f'VIAddVersionKey "ProductVersion" {_q(self.__version)}')
        w(f'VIAddVersionKey "FileVersion" {_q(self.__version)}')
        w(f'VIAddVersionKey "FileDescription" {_q(self.__description or f"{app} Installer")}')
        if self.__publisher:
            w(f'VIAddVersionKey "CompanyName" {_q(self.__publisher)}')
        # Always written: makensis warns (9100) when the standard key is missing
        w(f'VIAddVersionKey "LegalCopyright" {_q(self.__copyright or f"(c) {self.__publisher or app}")}')
        w('')

        # --- MUI interface settings ---
        if self.__abortWarning:
            w('!define MUI_ABORTWARNING')
            w('!define MUI_UNABORTWARNING')
        if self.__installIcon:
            w(f'!define MUI_ICON {_q(os.path.abspath(self.__installIcon))}')
        if self.__uninstallIcon:
            w(f'!define MUI_UNICON {_q(os.path.abspath(self.__uninstallIcon))}')
        if self.__headerImage:
            w('!define MUI_HEADERIMAGE')
            w(f'!define MUI_HEADERIMAGE_BITMAP {_q(os.path.abspath(self.__headerImage))}')
            w(f'!define MUI_HEADERIMAGE_UNBITMAP {_q(os.path.abspath(self.__headerImage))}')
            if self.__headerImageRight:
                w('!define MUI_HEADERIMAGE_RIGHT')
        if self.__welcomeImage:
            w(f'!define MUI_WELCOMEFINISHPAGE_BITMAP {_q(os.path.abspath(self.__welcomeImage))}')
        if self.__unwelcomeImage:
            w(f'!define MUI_UNWELCOMEFINISHPAGE_BITMAP {_q(os.path.abspath(self.__unwelcomeImage))}')
        if multiLang:
            w('!define MUI_LANGDLL_REGISTRY_ROOT "SHCTX"')
            w(f'!define MUI_LANGDLL_REGISTRY_KEY {_q(regKey)}')
            w('!define MUI_LANGDLL_REGISTRY_VALUENAME "InstallerLanguage"')
        if hasOptional and not hasDescriptions:
            w('!define MUI_COMPONENTSPAGE_NODESC')
        w('')

        # --- Installer pages ---
        w('!insertmacro MUI_PAGE_WELCOME')
        if self.__readmeText is not None or self.__readmeFile is not None:
            w('!define MUI_PAGE_HEADER_TEXT "$(MOX_README_TITLE)"')
            w('!define MUI_PAGE_HEADER_SUBTEXT "$(MOX_README_SUBTITLE)"')
            w('!define MUI_LICENSEPAGE_TEXT_TOP " "')
            w('!define MUI_LICENSEPAGE_TEXT_BOTTOM " "')
            w('!define MUI_LICENSEPAGE_BUTTON "$(^NextBtn)"')
            w(f'!insertmacro MUI_PAGE_LICENSE {_q(os.path.join(staging, "readme.txt"))}')
        if self.__license is not None:
            w('!define MUI_LICENSEPAGE_CHECKBOX')
            if htmlLicense:
                w('!define MUI_PAGE_CUSTOMFUNCTION_SHOW MoxLicenseShow')
                w(f'!insertmacro MUI_PAGE_LICENSE {_q(os.path.join(staging, "Empty.txt"))}')
            else:
                w(f'!insertmacro MUI_PAGE_LICENSE {_q(os.path.abspath(self.__license))}')
        if len(self.__scopes) == 2:
            w('!insertmacro MULTIUSER_PAGE_INSTALLMODE')
        if hasOptional:
            w('!insertmacro MUI_PAGE_COMPONENTS')
        w('!insertmacro MUI_PAGE_DIRECTORY')
        w('!insertmacro MUI_PAGE_INSTFILES')
        if self.__runAfterInstall:
            w(f'!define MUI_FINISHPAGE_RUN "$INSTDIR\\{self.__mainExe}"')
            if self.__runAfterInstallText:
                w(f'!define MUI_FINISHPAGE_RUN_TEXT {_q(self.__runAfterInstallText)}')
        w('!insertmacro MUI_PAGE_FINISH')
        w('')

        # --- Uninstaller pages ---
        w('!insertmacro MUI_UNPAGE_WELCOME')
        w('!insertmacro MUI_UNPAGE_CONFIRM')
        w('!insertmacro MUI_UNPAGE_INSTFILES')
        w('!insertmacro MUI_UNPAGE_FINISH')
        w('')

        # --- Languages ---
        for language in self.__languages:
            w(f'!insertmacro MUI_LANGUAGE {_q(language)}')
        if multiLang:
            w('!insertmacro MUI_RESERVEFILE_LANGDLL')
        w('')
        for language in self.__languages:
            overrides = self.__strings.get(language, {})
            for key, nsisName in STRING_KEYS.items():
                text = overrides.get(key, DEFAULT_STRINGS[nsisName])
                w(f'LangString {nsisName} {self.__LangId(language)} {_q(text)}')
        w('')

        # --- Hidden default section (content added before any StartComponent) ---
        if not self.__default.IsEmpty():
            w('Section "-Install"')
            if self.__Is64Bit():
                w('    SetRegView 64')
            self.__EmitComponentBody(w, self.__default)
            w('SectionEnd')
            w('')

        # --- Component sections ---
        sectionIds = self.__EmitComponentTree(w)

        # --- Component descriptions ---
        if hasOptional and hasDescriptions:
            w('!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN')
            for component in components:
                if component.description:
                    w(f'    !insertmacro MUI_DESCRIPTION_TEXT ${{{sectionIds[component.path]}}} {_q(component.description)}')
            w('!insertmacro MUI_FUNCTION_DESCRIPTION_END')
            w('')

        # --- Post section (uninstaller + registry, always last) ---
        w('Section "-Post"')
        if self.__Is64Bit():
            w('    SetRegView 64')
        w('    SetOutPath "$INSTDIR"')
        w('    WriteUninstaller "$INSTDIR\\Uninstall.exe"')
        w(f'    WriteRegStr SHCTX {_q(regKey)} "InstallDir" "$INSTDIR"')
        w(f'    WriteRegStr SHCTX {_q(regKey)} "InstallMode" "$MultiUser.InstallMode"')
        w(f'    WriteRegStr SHCTX {_q(unRegKey)} "DisplayName" {_q(app)}')
        w(f'    WriteRegStr SHCTX {_q(unRegKey)} "DisplayVersion" {_q(self.__version)}')
        if self.__publisher:
            w(f'    WriteRegStr SHCTX {_q(unRegKey)} "Publisher" {_q(self.__publisher)}')
        if self.__url:
            w(f'    WriteRegStr SHCTX {_q(unRegKey)} "URLInfoAbout" {_q(self.__url)}')
        displayIcon = f'$INSTDIR\\{self.__mainExe}' if self.__mainExe else '$INSTDIR\\Uninstall.exe'
        w(f'    WriteRegStr SHCTX {_q(unRegKey)} "DisplayIcon" "{displayIcon}"')
        w(f'    WriteRegStr SHCTX {_q(unRegKey)} "InstallLocation" "$INSTDIR"')
        w(f'    WriteRegStr SHCTX {_q(unRegKey)} "UninstallString" \'"$INSTDIR\\Uninstall.exe" /$MultiUser.InstallMode\'')
        w(f'    WriteRegStr SHCTX {_q(unRegKey)} "QuietUninstallString" \'"$INSTDIR\\Uninstall.exe" /$MultiUser.InstallMode /S\'')
        w(f'    WriteRegDWORD SHCTX {_q(unRegKey)} "NoModify" 1')
        w(f'    WriteRegDWORD SHCTX {_q(unRegKey)} "NoRepair" 1')
        w('    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2')
        w('    IntFmt $0 "0x%08X" $0')
        w(f'    WriteRegDWORD SHCTX {_q(unRegKey)} "EstimatedSize" "$0"')
        w('SectionEnd')
        w('')

        # --- Uninstall section ---
        allComponents = self.__AllComponents()
        allFiles = [_n(dst) for c in allComponents for _, dst in c.files]
        allDirs = sorted({os.path.dirname(f) for f in allFiles if os.path.dirname(f)}, key=lambda d: d.count('\\'))
        allShortcuts = [(name, location) for c in allComponents for _, name, location, _, _ in c.shortcuts]

        w('Section "Uninstall"')
        if self.__Is64Bit():
            w('    SetRegView 64')
        w('    SetOutPath "$INSTDIR"')
        for component in allComponents:
            for exe, args, visible in component.preUninstall:
                w(f'    ${{If}} ${{FileExists}} "{_target(exe)}"')
                self.__EmitAction(w, '        ', exe, args, visible)
                w('    ${EndIf}')
        w('    SetOutPath "$TEMP"')
        for dst in allFiles:
            w(f'    Delete "$INSTDIR\\{dst}"')
        for d in reversed(allDirs):
            w(f'    RMDir "$INSTDIR\\{d}"')
        w('    Delete "$INSTDIR\\Uninstall.exe"')
        w('    RMDir "$INSTDIR"')
        for name, location in allShortcuts:
            w(f'    Delete "{self.__ShortcutPath(name, location)}"')
        if any(location == 'startmenu' for _, location in allShortcuts):
            w(f'    RMDir "$SMPROGRAMS\\{app}"')
        w(f'    DeleteRegKey SHCTX {_q(unRegKey)}')
        w(f'    DeleteRegKey SHCTX {_q(regKey)}')
        w('SectionEnd')
        w('')

        # --- Functions ---
        w('Function .onInit')
        if self.__Is64Bit():
            w('    SetRegView 64')
        w('    !insertmacro MULTIUSER_INIT')
        if multiLang:
            w('    !insertmacro MUI_LANGDLL_DISPLAY')
        if htmlLicense:
            w('    InitPluginsDir')
            w(f'    File "/oname=$PLUGINSDIR\\LICENSE.html" {_q(os.path.abspath(self.__license))}')
        w('FunctionEnd')
        w('')
        w('Function un.onInit')
        if self.__Is64Bit():
            w('    SetRegView 64')
        w('    !insertmacro MULTIUSER_UNINIT')
        if multiLang:
            w('    !insertmacro MUI_UNGETLANGUAGE')
        w('FunctionEnd')
        w('')
        if htmlLicense:
            w('Function MoxLicenseShow')
            w('    ; Replace the license rich-edit control (1000) with an embedded HTML view')
            w('    FindWindow $R0 "#32770" "" $HWNDPARENT')
            w('    GetDlgItem $R0 $R0 1000')
            w('    EmbedHTML::Load /replace $R0 "$PLUGINSDIR\\LICENSE.html"')
            w('FunctionEnd')
            w('')

        return '\n'.join(out) + '\n'

    # ------------------------------------------------------------------
    # Deploy
    # ------------------------------------------------------------------

    def Deploy(self):
        if platform.system().lower() != 'windows':
            print(f'MDNSIS: NSIS installers are only supported on Windows, skipping {self.__filename}')
            return

        # Validate configuration
        if self.__runAfterInstall and not self.__mainExe:
            raise ValueError('MDNSIS: SetMainExecutable() is required for run after install')
        if self.__license is not None and not os.path.isfile(self.__license):
            raise FileNotFoundError(f'MDNSIS: License file not found: {self.__license}')
        if self.__readmeFile is not None and not os.path.isfile(self.__readmeFile):
            raise FileNotFoundError(f'MDNSIS: Readme file not found: {self.__readmeFile}')
        for component in self.__components.values():
            if component.IsEmpty():
                print(f'MDNSIS: Warning: component "{component.path}" is empty')

        # Bootstrap NSIS and required plug-ins
        self.__EnsureNsis()
        if self.__IsHtmlLicense():
            self.__EnsurePlugin('EmbedHTML')

        # Staging folder
        staging = os.path.abspath(f'./build/nsis/{os.path.splitext(self.__filename)[0]}')
        os.makedirs(staging, exist_ok=True)
        if self.__readmeText is not None or self.__readmeFile is not None:
            text = self.__readmeText
            if text is None:
                with open(self.__readmeFile, 'r', encoding='utf-8') as f:
                    text = f.read()
            text = text.replace('\r\n', '\n').replace('\n', '\r\n')
            with open(os.path.join(staging, 'readme.txt'), 'w', encoding='utf-8-sig', newline='') as f:
                f.write(text)
        if self.__IsHtmlLicense():
            with open(os.path.join(staging, 'Empty.txt'), 'w', encoding='utf-8-sig') as f:
                f.write(' ')
        script = os.path.join(staging, 'installer.nsi')
        with open(script, 'w', encoding='utf-8-sig', newline='\r\n') as f:
            f.write(self.__GenerateScript(staging))

        # Compile
        print(f'Building NSIS installer {self.__path} ...')
        RunChecked((self.__MakensisPath(), '/V2', script))
