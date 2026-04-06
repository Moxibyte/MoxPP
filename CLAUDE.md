# MoxPP

> This is an unconfigured MoxPP template. Run `/moxpp-setup` to replace this section with the actual project description, purpose, coding conventions, and any other context Claude needs to work effectively in this codebase.

## Conan Dependencies

> Not yet configured. Run `/moxpp-setup` to populate this section, or manually list the active packages below.

## MoxPP Build System

MoxPP is a C++ project template that combines **Premake5** (meta-build system) and **Conan 2** (package manager). Premake5 generates platform-native build files (Visual Studio solutions on Windows, Makefiles on Linux, Xcode on macOS). Conan fetches and wires up C++ dependencies.

### Entry Points

All commands go through the launcher scripts:
- **Windows:** `mox.bat <action> [args]`
- **Linux/macOS:** `./mox.sh <action> [args]`

> **Important for Claude:** Always run these commands with the working directory set to the repository root. Use the Bash tool with an explicit `cd` to the repo root before invoking, e.g.: `cd /path/to/repo && mox.bat <action>` (Windows) or `cd /path/to/repo && ./mox.sh <action>` (Linux/macOS). Never run mox from a subdirectory.

Common actions:
| Action | Description |
|--------|-------------|
| `init` | Download Premake5, run Conan, generate project files |
| `build` | Compile (`--conf Debug\|Release`, `--arch x86_64\|x86\|ARM\|ARM64`) |
| `run` | Execute a compiled binary |
| `test` | Run unit tests (init → build → run unittest) |
| `clean` | Remove generated files (`output`, `project`, `dependencies`, `all`) |
| `deploy` | Package binaries and sources into ZIPs |
| `autogen` | Full pipeline: init → build → deploy |
| `generate_uuid` | Print a new UUID for use in a build.lua |
| `generate_licenses` | Create an HTML license compliance report (`./LICENSE.html`) |
| `generate_moxpp_dependencies` | Process `dependencies.yml`: download/extract archives, run build scripts, copy DLLs into `dlls/`, emit `dependencies/dependencies.lua` |
| `graph` | Generate a Conan dependency graph |

### Configuration: `mox.lua`

The single file a developer needs to touch for project-wide settings. Key variables:

```lua
cmox_product_name        -- Solution/workspace name (string)
cmox_cpp_version         -- C++ standard, e.g. "C++23" (string)
cmox_src_folder          -- Source root folder name, default "src" (string)
cmox_macro_prefix        -- Prefix for all generated preprocessor macros, e.g. "MOXPP_" (string)
cmox_project_architecture -- How projects are discovered (see below)
cmox_copy_dlls           -- Auto-copy shared libs post-build (bool)
cmox_unit_test_src       -- Folder name for unit tests, or nil to disable (string|nil)
cmox_configurations_n    -- Array of configuration names, e.g. {"Debug","Release"}
cmox_configurations_d    -- Parallel array of debug flags (bool per config)
```

Callback functions (optional, defined in `mox.lua`):
```lua
function cmox_function_setupworkspace()  -- Called once for workspace-level Premake5 settings
function cmox_function_setupproject()    -- Called for every project
function cmox_function_includeprojects() -- Only used when architecture = "manual"
```

### Project Architecture Modes

Set via `cmox_project_architecture` in `mox.lua`:

| Mode | Layout | When to use |
|------|--------|-------------|
| `"single"` | One `build.lua` directly in `src/` | Single executable/library repo |
| `"flat"` | Each subdirectory of `src/` is a project with its own `build.lua` | Multiple sibling projects |
| `"hierarchical"` | `src/<group>/<project>/build.lua` | Grouped/layered project structure |
| `"manual"` | `cmox_function_includeprojects()` controls what gets loaded | Full custom control |

### build.lua API (`scripts/libmox.lua`)

Every project is defined in a `build.lua` file using these functions in order:

```lua
-- 1. Declare project (must be first)
mox_project("ProjectName", "output_name")  -- output_name is optional

-- 2. Select language
mox_cpp()        -- C++ (uses cmox_cpp_version)
mox_c()          -- C
mox_cs("4.6")   -- C# with optional .NET version

-- 3. Select output type
mox_console()    -- Console executable
mox_windowed()   -- GUI executable (no console window, Windows only)
mox_sharedlib()  -- Shared library (.dll/.so/.dylib)
mox_staticlib()  -- Static library
mox_utility()    -- Utility project (custom build actions, no code output)
mox_none()       -- Header-only / no build output

-- 4. Set a unique UUID (required, generate with: python -c "import uuid; print(uuid.uuid4())")
uuid("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

-- 5. Optional: mark this lib as a dependency for the unit test project
mox_test_requirement()
```

After these calls, any standard [Premake5 API](https://premake.github.io/docs) calls are valid (e.g. `links`, `dependson`, `includedirs`, `defines`).

Helper functions available in `build.lua`:
```lua
mox_runpy_postbuild("action [args]")   -- Add a mox action as a post-build step
mox_runpy_prebuild("action [args]")    -- Add a mox action as a pre-build step
```

### Auto-generated Preprocessor Macros

Every project gets these macros (prefix = `cmox_macro_prefix`):

| Macro | Value |
|-------|-------|
| `PREFIX_VERSION` | Version string (from `MOXPP_VERSION` env var or dev timestamp) |
| `PREFIX_WORKSPACE_ROOT` | Absolute path to the repo root |
| `PREFIX_PROJECT_ROOT` | Absolute path to this project's directory |
| `PREFIX_DEBUG` / `PREFIX_NDEBUG` | Set per configuration |
| `PREFIX_<CONF_NAME>` | E.g. `PREFIX_DEBUG`, `PREFIX_RELEASE` |
| `PREFIX_OS_WINDOWS` / `_LINUX` / `_MACOS` | Platform |
| `PREFIX_ARCH_X86` / `_X86_64` / `_ARM` / `_ARM64` | Architecture |
| `PREFIX_BIT_32` / `PREFIX_BIT_64` | Bitness |
| `PREFIX_APP` + `PREFIX_CONSOLE`/`_WINDOWED` | For executable projects |
| `PREFIX_LIB` + `PREFIX_LIB_SHARED`/`_STATIC` | For library projects |

### Dependencies: `conanfile.py`

Add Conan package references in the `requirements()` method:
```python
self.requires("spdlog/1.15.3")
self.requires("gtest/1.16.0")   # keep if using unit tests
```

Set package options in `configure()`:
```python
self.options["spdlog"].shared = True
```

After editing `conanfile.py`, re-run `mox init` to regenerate project files.

### External Dependencies: `dependencies.yml`

For libraries that cannot be managed by Conan (prebuilt binaries, header-only zips, custom-built libs), create `./dependencies.yml` at the repository root. It is processed automatically during `mox init` and can be run standalone with `mox generate_moxpp_dependencies`.

**YAML structure:**
```yaml
dependencies:
  - download: <url>        # optional – archive fetched and extracted into folder
    folder:   <local-dir>  # path relative to repo root
    build:    <script.py>  # optional – Python script run after extraction (repo root cwd)
    # Every section below is optional.
    # Each section accepts: include_dirs, lib_dirs, links, defines, copy_dll
    all:                   # applied unconditionally
    debug:                 # applied when is_debug == true
    release:               # applied when is_debug == false
    # Architecture-qualified variants (merged into the plain section at generation time):
    all_x86_64:            # merged into 'all' when --arch resolves to x86_64
    debug_x86_64:          # merged into 'debug' when --arch resolves to x86_64
    release_x86_64:        # … likewise for x86, ARM, ARM64 (premake5 arch names)
```

`include_dirs` and `lib_dirs` paths are relative to `folder` and are automatically prefixed with `%{wks.location}/<folder>/` in the generated Lua. `links` and `defines` are emitted as-is.

**`copy_dll`** — list of paths relative to `folder`; files are flat-copied (filename only, no subdirectory) to:

| Section | Destination |
|---------|-------------|
| `all` / `all_<arch>` | `./dlls/Debug-<arch>/` **and** `./dlls/Release-<arch>/` |
| `debug` / `debug_<arch>` | `./dlls/Debug-<arch>/` only |
| `release` / `release_<arch>` | `./dlls/Release-<arch>/` only |

**Generated output** — `./dependencies/dependencies.lua` is included automatically by `scripts/premake5.lua` and exposes two functions:
```lua
moxpp_dependencies_build(conf, is_debug)  -- applies includedirs + defines, gated by conf filter
moxpp_dependencies_link(conf, is_debug)   -- applies libdirs + links, gated by conf filter
```
Call them from `cmox_function_setupproject()` in `mox.lua`, or directly inside a project's `build.lua` after `mox_cpp()` / `mox_console()` / etc.

### License Report: `generate_licenses` / `licenses.yml`

`scripts/generate_licenses.py` is run automatically at the end of `mox init`. It collects:
1. The project's own license from `./LICENSE`.
2. All Conan dependency licenses from `./dependencies/full_deploy/`.
3. Any additional non-Conan licenses from an optional `./licenses.yml` file.

**`licenses.yml` format** (place at repo root, pass via `--additional-licenses` in `init.py`):
```yaml
additional_licenses:
  - name: MyLib
    version: 1.0.0
    license_files:
      - ./path/to/LICENSE.txt
```

Output is written to `./LICENSE.html`.

### Build Output Layout

```
build/<arch>-<conf>/bin/    # Executables and shared libraries
build/<arch>-<conf>/obj/    # Object files (per project subfolder)
app/                        # Working directory when running/debugging
dlls/<Debug|Release>-<arch>/  # Conan-managed DLLs (auto-copied post-build)
```

### Unit Tests

Set `cmox_unit_test_src = "test"` in `mox.lua`. The `test/build.lua` uses `mox_setup_test()` which auto-creates the `unittest` project linked against any project that called `mox_test_requirement()`. The test framework (gtest by default) is a Conan dependency — it can be swapped.

### Platform Support

| Platform | Architectures | Build backend |
|----------|--------------|---------------|
| Windows | x86, x86_64, ARM64 | MSBuild (VS 2017/2019/2022/2026) |
| Linux | x86, x86_64, ARM, ARM64 | GNU Make |
| macOS | ARM64 | Xcode |
