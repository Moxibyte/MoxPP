# Building the project
This project supports
- [x] Windows
- [x] Linux

## Requirements
- Python3 with:
    - Conan2 (Version 2.0.4 or later; Install it via `pip install conan` / `pip3 install conan` on Linux) 
- Visual Studio with the C++ workloads (Windows)
- build-essential (Linux)
- CMake (Required for some conan packages, but not for the template)

## Windows
### Setting up the project
To create the visual studio solution and projects run the following commands in the root of the repository
```bat
mox.bat init
```
*This will also download and compile all external dependencies. Please be patient.*

### Writing code and compiling
After setting up the project, you will find a `.sln` file in the root directory. Open this file with Visual Studio and start developing/compiling. 

## Linux
### Setting up the project
### Writing code and compiling

## MOX Actions
The project provides the following actions:
- **init**: This command will initialized the repository. On windows it will generate a solution, on linux Makefiles.
- **build**: This command will build the project. Usage: `./mox.bat/sh build [conf]`.
- **deploy**: This command will deploy a build. Usage: `./mox.bat/sh deploy [conf]`.
- **clean**: This command will remove all regenerate able files of a certain category. Usage `./mox.bat/sh clean [type]` Where type can be (`output`, `project`, `dependencies`, or `all`. Default to `output`).
- **run**: This will automatically run a specific executable in the correct working dir. Usage `./mox.bat/sh run [-c=Debug/Release/...] EXE [args...]`.
- **autogen**: Will automatically run `init`, `build` and `deploy`.
