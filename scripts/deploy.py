"""
The deployment script is written minimal by default!
Add your own code to the main "function"

The script is by default called with "Release" in the first argument

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
import mox
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
    appName = mox.ExtractLuaDef("./mox.lua", "cmox_product_name")
    version = mox.GetAppVersion()
    arch = mox.GetPlatformInfo(args.arch)["premake_arch"]
    build_folder = f'./build/{arch}-{args.conf}'

    # TODO: Add your own implementation
    #       We do some quick example here

    # == Simple zip archive with the software (dumb copy) ==
    # Also add the msvc redists via "AddMSVCRedists" call (does nothing is not on windows!)
    zipArchive = mox.MDZip(mox.AutomaticFilename(f"{appName}", version, args.conf, args.arch, "zip"))
    zipArchive.AddFolder(f'{build_folder}/bin', '')
    zipArchive.AddFile("./LICENSE.html", "LICENSE.html")
    # zipArchive.AddMSVCRedists() <-- Add this when you want to distribute redists. REMARK: This will include latest redists (most recent install visual studio). Please make sure you check licensing
    zipArchive.Deploy()

    # == Windows installer (NSIS, Modern UI 2). Deploy() is skipped with a warning on non windows systems. ==
    # The first call bootstraps a portable NSIS into ./dependencies/nsis (plus plug-ins when needed).
    # All Set* calls are optional, see scripts/mox/mdnsis.py for the full API.
    installer = mox.MDNSIS(mox.AutomaticFilename(f"{appName}", version, args.conf, args.arch, "exe"), appName, version, args.arch)
    installer.SetMeta(publisher="Moxibyte GmbH", description=f"{appName} Installer", url="https://github.com/moxibyte/MoxPP") # <-- Adjust to your product
    installer.SetMainExecutable("hello_world.exe")           # Used for the display icon and run after install
    installer.SetLicense("./LICENSE.html")                   # .html is rendered via the EmbedHTML plug-in (.txt/.rtf also supported)
    installer.SetReadme(text=f"Thank you for installing {appName} {version}.\n\nThis is a free text information page shown before the installation starts.")
    installer.SetInstallScopes(("machine", "user"))          # Both supported -> the end user chooses inside the installer
    installer.SetRunAfterInstall(True)                       # "Run hello_world" checkbox on the finish page
    # installer.SetLanguages(("English", "German"))          # More than one language shows a language selection dialog
    # installer.SetIcons("./res/install.ico", "./res/uninstall.ico")
    # installer.SetTheme(headerImage="./res/header.bmp", welcomeImage="./res/welcome.bmp")

    # Components: files, shortcuts and actions bind to the most recent StartComponent() call.
    # "Group/Leaf" paths create section groups. The components page is only shown when an optional component exists.
    installer.StartComponent("Application", required=True, description="Core application files")
    installer.AddFolder(f'{build_folder}/bin', '')
    installer.AddFile("./LICENSE.html", "LICENSE.html")
    # installer.AddMSVCRedists()                                        # Installs the redist silently. See licensing remark above
    # installer.AddPostInstallAction("hello_world.exe", "--first-run")  # Runs hidden after the files, output in the install log
    # installer.AddPreUninstallAction("hello_world.exe", "--cleanup")   # Runs before the uninstaller removes files

    installer.StartComponent("Shortcuts/Start Menu", description="Start menu entries")
    installer.AddShortcut("hello_world.exe", appName, "startmenu")
    installer.AddShortcut("Uninstall.exe", f"Uninstall {appName}", "startmenu")

    installer.StartComponent("Shortcuts/Desktop", default=False, description="Desktop shortcut")
    installer.AddShortcut("hello_world.exe", appName, "desktop")
    installer.Deploy()

    # == Source archive ==
    srcArchive = mox.MDSrc(mox.AutomaticFilename(f"{appName}_src", version, args.conf, args.arch, "zip"))
    srcArchive.Deploy()
