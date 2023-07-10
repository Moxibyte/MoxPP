"""
Windows tool functions

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
import json
import subprocess

def GetCodepage():
    return "".join(filter(str.isalnum, subprocess.getoutput('chcp').split(':')[-1].strip()))
    
def FindLatestVisualStudio():
    vswhere = os.getenv('programfiles(x86)') + '\\Microsoft Visual Studio\\Installer\\vswhere.exe'
    out = subprocess.check_output((vswhere, '-latest', '-nocolor', '-format', 'json'))
    return json.loads(out.decode(f'cp{GetCodepage()}'))

def GetVisualStudioYearNumber(vswhere):
    installationVersion = vswhere[0]['installationVersion'].split('.')[0]
    if installationVersion == '17':
        return '2022'
    if installationVersion == '16':
        return '2019'
    if installationVersion == '15':
        return '2017'

def GetVisualStudioPath(vswhere):
    return vswhere[0]['installationPath']

