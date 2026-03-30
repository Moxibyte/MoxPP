---
name: moxpp-add-project
description: Adds a new sub-project to an existing MoxPP workspace. Use when the developer wants to add a new executable, library, or utility project to the build system.
---

# MoxPP Add Project

Help the developer add a new sub-project to this MoxPP workspace. Work through the steps below interactively — ask for any information you don't already have before making changes.

## Steps

### 1. Check architecture compatibility

Read `mox.lua` and check `cmox_project_architecture`:
- **`single`**: Adding a second project requires switching to `flat`, `hierarchical`, or `manual` first. Warn the user and ask how they want to proceed before continuing.
- **`flat`**: New project goes into `src/<project-name>/`.
- **`hierarchical`**: Ask for the group name. New project goes into `src/<group>/<project-name>/`.
- **`manual`**: Remind the user they must manually add an `include` call in `cmox_function_includeprojects()` inside `mox.lua`.

### 2. Gather project information

Ask the user for the following if not already provided via $ARGUMENTS:
- **Project name** — used in the Visual Studio solution (PascalCase recommended)
- **Output name** — binary/library filename, snake_case. Default: snake_case of project name.
- **Language** — `C++` (default), `C`, or `C#`
- **Output type**:
  - `console` — console executable
  - `windowed` — GUI executable (no console window, Windows only)
  - `sharedlib` — shared library (.dll / .so / .dylib)
  - `staticlib` — static library
  - `utility` — custom build actions, no code output
  - `none` — header-only, no build output
- **Dependencies on other projects** — list project names to `links {}` against. Ask separately if build order matters (`dependson {}`).
- **Unit test requirement** — if output type is `sharedlib` or `staticlib`, ask whether the unit test project should link against this project (adds `mox_test_requirement()`).
- **Conan dependencies** — any additional Conan packages needed in `<name>/<version>` format. Ask whether any need options changed. (Only relevant for `C++` and `C` projects; skip for `staticlib` and `none` since they don't link Conan deps directly.)

### 3. Generate a UUID

Run `mox generate_uuid` (Windows: `mox.bat generate_uuid`, Unix: `./mox.sh generate_uuid`) and capture the output for use in the new `build.lua`.

### 4. Create the project directory and `build.lua`

Create the directory according to the architecture layout determined in step 1.

Write `build.lua` using the gathered information:

```lua
mox_project("<ProjectName>", "<output_name>")

mox_cpp()        -- or mox_c() / mox_cs()

mox_console()    -- or mox_windowed() / mox_sharedlib() / mox_staticlib() / mox_utility() / mox_none()

uuid("<generated-uuid>")

-- mox_test_requirement()  -- uncomment if this lib is needed by the unit tests

-- links {
--     "OtherProject",
-- }

-- dependson {
--     "OtherProject",
-- }
```

Uncomment and fill in only the sections that apply. Remove unused comment blocks.

### 5. Create a starter source file

For `console` and `windowed` projects: create `<project-dir>/main.cpp` with a minimal `main()` function.
For `sharedlib` or `staticlib`: create `<project-dir>/<output_name>.h` and `<project-dir>/<output_name>.cpp` with an empty placeholder.
For `utility` or `none`: no source file needed.

### 6. Update `conanfile.py` (if new Conan packages were requested)

Add the new `self.requires(...)` calls and any `self.options[...]` entries.

### 7. Update `mox.lua` if needed

- If architecture was changed from `single` to `flat`/`hierarchical`: update `cmox_project_architecture`.
- For `manual` architecture: remind the user to add the `include` call in `cmox_function_includeprojects()`.
- If this is the intended startup project for Visual Studio, update `startproject` in `cmox_function_setupworkspace()`.

### 8. Confirm and summarize

List all files created or modified and remind the user to run `mox init` (or `./mox.sh init`) to regenerate project files.
