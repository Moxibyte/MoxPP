"""
Generates a current project archive to the archive directory

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
import sys
import pathlib
import datetime
import subprocess

ARCHIVE_PRODUCT_NAME = "moxpp"

def IsRepoReadyToArchive(path):
    # Step 1: Check if path is a Git repository
    if not os.path.isdir(os.path.join(path, '.git')):
        print("ERROR: No git repository!")
        return False

    try:
        # Step 2: Use git status --porcelain to detect changes
        result = subprocess.run(
            ('git', 'status', '--porcelain'),
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        if result.stdout.strip():
            print("WARNING: Pending changes NOT included!")
        return True

    except subprocess.CalledProcessError as e:
        print("ERROR: Failed to check repository status.")
        return False

def CreateGitArchive(path, archive_dir, product_name):
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    archive_name = f"{product_name}-archive-{timestamp}.zip"
    archive_path = os.path.join(archive_dir, archive_name)

    try:
        subprocess.run(
            ('git', 'archive', '--format=zip', '-o', archive_path, 'HEAD'),
            cwd=path,
            check=True
        )
        print(f"Archive created at: {archive_path}")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to create archive.")

if __name__ == "__main__":
    current_dir = os.getcwd()
    archive_dir = os.path.join(current_dir, "archive")

    if IsRepoReadyToArchive(current_dir):
        CreateGitArchive(current_dir, archive_dir, ARCHIVE_PRODUCT_NAME)
