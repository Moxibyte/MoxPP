"""
Cleans all relevant files 
Multiple modes:
- "output" (default): Removes the build directory
- "project": Removes all visual studio files / Makefiles
- "dependencies": Removes the external downloaded dependencies (not the conan cache)
- "all": All above steps 

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
import os
import sys
import shutil

def RecursiveRemove(root_dir, extensions_to_remove = (), exclude_subdirs = ()):
    for content in os.listdir(root_dir):
        path = f'{root_dir}{content}'

        if os.path.isfile(path):
            for ext in extensions_to_remove:
                if str(path).endswith(ext):
                    os.remove(path)

        if os.path.isdir(path):
            if path not in exclude_subdirs:
                RecursiveRemove(f'{path}/', extensions_to_remove)

def CleanOutput():
    shutil.rmtree('./build', ignore_errors=True)
    shutil.rmtree('./temp', ignore_errors=True)
    shutil.rmtree('./deploy', ignore_errors=True)

def CleanDependencies():
    shutil.rmtree('./dependencies', ignore_errors=True)

def CleanProject():
    shutil.rmtree('./vs', ignore_errors=True)
    RecursiveRemove(
        './', 
        ('.sln', '.vcxproj', '.vcxproj.user', '.vcxproj.filters', 'Makefile'),
        ('.git', '.vs', 'app', 'build', 'dependencies', 'scripts')
    )

if __name__ == '__main__':
    # Get mode from cli
    mode = 'output'
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    # Select mode
    if mode == 'output':
        CleanOutput()
    elif mode == 'project':
        CleanProject()
    elif mode == 'dependencies':
        CleanDependencies()
    elif mode == 'all':
        CleanOutput()
        CleanProject()
        CleanDependencies()
