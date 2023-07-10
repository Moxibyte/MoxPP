# Building the project
This project supports
- [x] Windows
- [x] Linux

## Requirements
- Python3 with:
    - Conan2 (Version 2.0.7 or later; Install it via `pip install conan` / `pip3 install conan` on Linux) 
- Visual Studio with the C++ workloads (Windows)
- build-essential (Linux)
- CMake (Required for some conan packages, but not for the template)

## Windows
### Initial configuration
- Conan profile: Let conan detect your profile automatically. Run the command `conan profile detect`

### Setting up the project
To create the visual studio solution and projects run the following commands in the root of the repository
```bat
mox.bat init
```
*This will also download and compile all external dependencies. Please be patient.*

### Writing code and compiling
After setting up the project, you will find a `.sln` file in the root directory. Open this file with Visual Studio and start developing/compiling. 

## Linux
### Initial configuration
- Conan profile: Let conan detect your profile automatically. Run the command `conan profile detect`
- Making sure conan uses the right ABI:
    - Open your default profile (`/home/<username>/.conan2/profiles/default`)
    - Make sure the following line is existing `compiler.libcxx=libstdc++11` (You might need to manually add/change this!)

### Writing code and compiling
On linux you can directly start editing the code without any solution. Use the text editor of your choice. 

As soon as you are ready to build run the following commands
```sh
# It's recommented to run init after the first clone and after creating / moving / deleting files. 
./mox.sh init
# This is the raw linux "make". You can add the configuration as an argument
./mox.sh build 
./mox.sh build Debug
# This is how you can run the compiled application in the proper way from the repositiory root
./mox.sh run EXECUTABLE_NAME
# Optional with the configuration
./mox.sh run -c=Debug EXECUTABLE_NAME
```
The above commands also fully work on windows (use `mox` or `mox.bat` instead of `./mox.sh`).

## Actions
The project provides the following actions. You can run them with the mox tool (`mox` or `mox.bat` on Windows. `./mox.sh` on linux):
- **init**: This command will initialized the repository. On windows it will generate a solution, on linux Makefiles.
- **build**: This command will build the project. Usage: `./mox.bat/sh build [conf]`.
- **deploy**: This command will deploy a build. Usage: `./mox.bat/sh deploy [conf]`.
- **clean**: This command will remove all regenerateable files of a certain category. Usage `./mox.bat/sh clean [type]` Where type can be (`output`, `project`, `dependencies`, or `all`. Defaults to `output`).
- **run**: This will automatically run a specific executable in the correct working dir. Usage `./mox.bat/sh run [-c=Debug/Release/...] EXE [args...]`.
- **autogen**: Will automatically run `init`, `build` and `deploy`.
