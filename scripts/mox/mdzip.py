"""
MDZip - MoxPP Deploy 
Packes into a zip file

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
import os
import zipfile

class MDZip:
    def __init__(self, filename):
        self.__path = filename
        self.__files = []

    def AddFile(self, file, name):
        self.__files.append((file, name))

    def AddFolder(self, folder, name):
        for file in os.listdir(folder):
            path = f'{folder}/{file}'
            if os.path.isfile(path):
                self.AddFile(path, f'{name}/{file}')

    def Pack(self):
        with zipfile.ZipFile(self.__path, 'w') as zip_file:
            for file in self.__files:
                zip_file.write(file[0], file[1])
