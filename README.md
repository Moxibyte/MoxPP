# MoxPP
C++ Template Repository with Conan2 and Premake5 for Windows and Linux. Out of the Box unit-testing and GitHub actions.

**Please make sure to read the WHOLE readme and follow all instructions!**

## Important things to know
- There is currently no support for cross compiling. That means you need to always compile on Windows for Windows, on Linux for Linux, on ARM64 for ARM64 and so on.
- The project support `x86`, `x86_64`, `ARM` and `ARM64` (please note that ARM and 32-Bit support is experimental and is currently not covered by any tests. Github runners only support x86_64. I have tested ARM64 on an OnLogic industrial RPi with am CM4 and it worked with no problems).
- **PLEASE NOTE THAT THERE IS NO PRECOMPILED BINARY OF PREMAKE FOR ARM!!! YOU NEED TO MANUALLY COMPILE AND COPY THE EXECUTABLE.**
- The project uses GitHub Actions by default. Delete them if you don't want them. We will NOT cover any costs or results occurred because of actions or code shipped with this template! MIT Licenses also applies here!

## Dependencies
Before you are getting started make sure to install the following applications:
- Python3
- Conan2 (`pip install conan`) please use version `2.9.3` (it might work on newer version but conan2 changes a thing with every update!)
- Visual Studio (Windows)
- build-essential (Linux)
More information in [BUILDING.md](BUILDING.md)

## Checklist
After you used this template for creating your new project please make sure to follow all these steps to setup your repository correctly.
- [ ] Check that the project works on your system:
    - [ ] Windows: Run `mox.bat init`, open the visual studio and build the solution (Batch build).
    - [ ] Linux: Run `./mox.sh autogen`. This should produce the file `./deploy/Release/package.zip` (You can also do this on windows. Run `mox.bat autogen` shall have the same result).
- [ ] Take a look at `./mox.lua` (The configuration file for your repository) and understand all the settings. Modify them for your needs. If you modify `mox.lua` or any other project related `.lua` file later. Please make sure to always rerun `mox.bat init`. Copying or removing visual studio projects and solutions is only possible when visual studio is closed! You can remove all visual studio and makefile by running `mox.bat clean project`.  
- [ ] Read and understand how `./src/build.lua` works.
- [ ] Choose a project architecture `cmox_project_architecture` in `mox.lua`:
    - `single`: Only one single build file is used. Use this architecture if you are writing a simple project with only one executable and no shared or static libs.
    - `flat`: Flat build architecture in the source subfolder (`cmox_src_folder`). Each subfolder is one project with it's own dedicated `build.lua` file inside.
    - `hierarchical`: Projects are group into groups. The src folder contains a subfolder for each group. Within the groups subfolder each project is represented as a subdirectory with it's own `build.lua` file.
    - `manual`: MoxPP will not handle automatic including of the `build.lua` files. Instead MoxPP will call a custom callback function provided by you. Implement the function `cmox_function_includeprojects` within `mox.lua`.
- [ ] Add and modify the projects build script according to the selected architecture.
- [ ] Revisit `BUILDING.md` and adjust it to your projects requirements. In case you modified any of the build steps (Scripts themselves), make sure to change `BUILDING.md` so that it's still correct.
- [ ] Adding your own scripts: You can add your own python scripts by adding them to the `./scripts` folder. You can run the script with the mox tool `mox.bat <SCRIPT_NAME>` working dir is the repository root. Make sure to add your script to the list of actions in `BUILDING.md`.
- [ ] Choosing your desired license. Make sure to add a license to the repository. All files that are copyright by us have already been marked with a license and thus are fine. This is no legal advice! Consult your lawyer! 
- [ ] Disable unit-testing when required. By default we provide a dummy unit test, we encourage the use of unit-tests! If you don't want them you can disable them in `mox.lua` and delete the `test` directory. You can also modify the building of unit tests or the library. MoxPP is shipped with gtest but has no hard requirements on it.
- [ ] Verify the usage of GitHub actions. We provide GitHub actions that build and test the codebase. Please make sure to delete the workflow files or disable action, in case you don't want to uses them!
- [ ] Now you can shall remove this readme file and replace it with your description of your project. 

**There is more information in** `BUILDING.md` **(That you should keep) on how to build the project.**

**We have an extensive video that showcases how this template works: [https://youtu.be/u-2syomFD2s](https://youtu.be/u-2syomFD2s)**

## License
The code shipped with MoxPP is licensed under the `MIT License`. All python and lua scripts have the license embedded into them. Additional attribution is not required as long as the template is not redistributed itself. Feel free to use the template in your projects. This is no legal advice! Consult your lawyer! 
