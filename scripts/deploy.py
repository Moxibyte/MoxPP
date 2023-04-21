"""
The deployment script is written minimal by default!
Add your own code to the main "function"

The script is by default called with "Release" in the first argument
"""
import os
import sys
import zipfile

if __name__ == '__main__':
    # Configuration for the build
    conf = 'Release'
    if len(sys.argv) > 1:
        conf = sys.argv[1]

    # Work directory's
    tempDir = f'./temp/{conf}/'
    deployDir = f'./deploy/{conf}/'
    os.makedirs(tempDir, exist_ok=True)
    os.makedirs(deployDir, exist_ok=True)

    # We will do a quick copy from the out folder
    # TODO: Add your own implementation
    with zipfile.ZipFile(f'{deployDir}package.zip', 'w') as zip_file:
        for file in os.listdir(f'./build/x86_64-{conf}/bin'):
            path = f'./build/x86_64-{conf}/bin/{file}'
            if os.path.isfile(path):
                zip_file.write(path, file)
