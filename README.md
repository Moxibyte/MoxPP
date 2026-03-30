# MoxPP
C++ Template Repository with Conan2 and Premake5 for Windows, Linux and MacOS. Out of the Box unit-testing and GitHub actions.

**Please make sure to read the WHOLE readme and follow all instructions!**

## Important things to know
- This project support cross compiling but only for the same os. I only tested `x86_64` to `arm64` (because this is the most likely usage of cross compiling. The binaries work on `arm64` chips like RPi CMs, iMX91/3)
- The project support `x86`, `x86_64`, `ARM` and `ARM64` (Compiling from windows and linux for the respective systems has been test. Only plain `ARM` is not tests. However we do not unit-test any configuration other than 64bit).
- **PLEASE NOTE THAT THERE IS NO PRECOMPILED BINARY OF PREMAKE FOR ARM BUILD SYSTEM!!! YOU NEED TO MANUALLY COMPILE AND COPY THE EXECUTABLE.**
- The project uses GitHub Actions by default. Delete them if you don't want them. We will NOT cover any costs or results occurred because of actions or code shipped with this template! MIT Licenses also applies here!

## Dependencies
Before you are getting started make sure to install the following applications:
- Python3 with venv (On linux `python3` and `python3-venv`)
- Visual Studio with the C++ workloads (Windows)
- Package `build-essential` (Linux only) 
- GLIBC_2.38 or more recent (Linux; Premake requirement)
- Xcode with clang and default abi (MacOS)
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

## Claude Code Integration

MoxPP ships with [Claude Code](https://claude.ai/code) skills to help you set up and extend your project. A `CLAUDE.md` file is included at the repository root — it gives Claude context about the MoxPP build system and, after running `/moxpp-setup`, will also contain your project's description and coding conventions. Claude Code reads this file automatically in every session.

If you have Claude Code installed, you can use the following skills directly in your repository:

### `/moxpp-setup`
Guides you through the full initial configuration of this template for your project. Run this after cloning before you do anything else. It will:
- Ask for your project name, description, C++ standard, architecture mode, and Conan dependencies
- Update `mox.lua`, `src/build.lua`, and `conanfile.py` accordingly
- Rewrite `CLAUDE.md` with your project's purpose and coding conventions, keeping the MoxPP reference as a subsection

### `/moxpp-add-project`
Adds a new sub-project (executable, library, or utility) to an existing MoxPP workspace. It will:
- Ask for the project name, output type, language, and any inter-project dependencies
- Generate a fresh UUID, create the project directory and `build.lua`, and add a starter source file
- Update `conanfile.py` if new Conan packages are needed
- Warn you if a change in project architecture (`single` → `flat`/`hierarchical`) is required

### `/moxpp-check`
Audits `CLAUDE.md` for drift against the actual project structure. Run this any time you've changed `mox.lua`, `conanfile.py`, or project `build.lua` files without updating `CLAUDE.md`. It will:
- Compare the documented project name and description against `mox.lua` and `README.md`
- Diff the `## Conan Dependencies` section against `conanfile.py`
- Detect duplicate UUIDs across all `build.lua` files
- Check for missing `dummy.cpp` in lib projects and orphaned `test/` directories
- Propose all corrections with severity ratings before making any changes

**We have an extensive video that showcases how this template works: [https://youtu.be/u-2syomFD2s](https://youtu.be/u-2syomFD2s)** (This video is outdated by now. I will make a new one in the new future)

## License
The code shipped with MoxPP is licensed under the `MIT License`. All python and lua scripts have the license embedded into them. Additional attribution is not required as long as the template is not redistributed itself. Feel free to use the template in your projects. This is no legal advice! Consult your lawyer!
