---
name: moxpp-setup
description: Configures a freshly cloned MoxPP template for a new project. Use when starting a new C++ project from the MoxPP template and the developer needs to rename and configure it.
---

# MoxPP Initial Setup

Help the developer configure this MoxPP template for their new project. Work through the steps below interactively — ask for any information you don't already have before making changes.

## Steps

### 1. Gather project information

Ask the user for the following if not already provided via $ARGUMENTS:
- **Project name** — the human-readable product name (used as solution/workspace name)
- **Project description** — what this project does; used in CLAUDE.md to give Claude context
- **Coding conventions** — any naming conventions, style rules, or patterns the developer follows (e.g. snake_case for files, PascalCase for classes, no exceptions, etc.); used in CLAUDE.md
- **Macro prefix** — short ALL_CAPS prefix for preprocessor macros (e.g. `MYAPP_`). Default: derived from project name.
- **C++ standard** — default is `C++23`, confirm or ask for override.
- **Project architecture** — `single` (one project), `flat` (sibling projects in src/), `hierarchical` (grouped), or `manual`. Default: `single`.
- **Unit tests** — keep (`test`) or remove unit test support (`nil`)?
- **Conan dependencies** — list any required packages in `<name>/<version>` format (e.g. `fmt/11.0.2`). Ask whether any package needs options changed (e.g. `shared = True`). Note: `gtest` is added automatically when unit tests are enabled and does not need to be listed here.

### 2. Update `mox.lua`

Edit the following fields in `mox.lua`:
- `cmox_product_name` → new project name
- `cmox_macro_prefix` → new macro prefix (must end with `_`)
- `cmox_cpp_version` → confirmed C++ standard
- `cmox_project_architecture` → chosen architecture mode
- `cmox_unit_test_src` → `"test"` or `nil`. **If set to `nil`, also delete the `./test` directory at the repository root** — leaving it in place will cause stale project files and build errors.
- In `cmox_function_setupworkspace()`: update `startproject` to match the new main project name (or remove the call if not applicable)

### 3. Rename the example project in `src/build.lua`

- Change `mox_project("HelloWorld", "hello_world")` to use the new project name and a snake_case output name.
- Update the output type to match what the user requested (e.g. `mox_console()`, `mox_sharedlib()`, etc.).
- Generate a fresh UUID by running `python -c "import uuid; print(uuid.uuid4())"` via Bash and replace the existing UUID in `src/build.lua`.
- **Source file management** (only for `single` architecture — for other architectures this is handled in step 5):
  - If `sharedlib` or `staticlib`: delete `src/main.cpp`, create `src/<output_name>.h`, `src/<output_name>.cpp` (empty placeholders), and `src/dummy.cpp` (containing only `// dummy`). `dummy.cpp` is required on Windows — without at least one compiled `.cpp`, MSBuild will not produce a `.lib` and any dependent project will fail to build.
  - If `console` or `windowed`: keep `src/main.cpp` as-is.

### 4. Update `conanfile.py`

- Rename the class from `MoxPPRecipe` to match the new project name (e.g. `MyProjectRecipe`).
- Replace the template `spdlog` dependency (and its `shared = True` option) with the packages the user provided.
- For each package that has options, add the corresponding `self.options[...]` calls in `configure()`.
- Keep `self.requires("gtest/1.16.0")` if unit tests are enabled; remove it otherwise.

### 5. Adjust architecture layout (if not `single`)

- **flat**: Create `src/<first-project-name>/`. Move `src/build.lua` into it. Then apply source file management based on output type:
  - If `console` or `windowed`: move `src/main.cpp` into the project directory.
  - If `sharedlib` or `staticlib`: delete `src/main.cpp` and create `<project-dir>/<output_name>.h`, `<project-dir>/<output_name>.cpp` (empty placeholders), and `<project-dir>/dummy.cpp` (containing only `// dummy`).
- **hierarchical**: Create `src/<group>/<project-name>/`. Move `src/build.lua` into it. Apply the same source file management rules as flat above, using the new project directory as the target.
- **manual**: Remove the auto-discovery note and remind the user to implement `cmox_function_includeprojects()` in `mox.lua`.

### 6. Update `CLAUDE.md`

Rewrite `CLAUDE.md` to follow the enforced layout below. Keep all existing content under `## MoxPP Build System` (headings inside that section demoted by one level: `##` → `###`). Replace the top section with real project content based on what was gathered in step 1.

Required layout:
```
# <Project Name>

<Project description — what it does, its purpose, target platform/audience, etc.>

## Coding Conventions
<List the conventions the developer provided. If none were given, omit this section.>

## <Any other project-specific sections the developer wants Claude to know>

## Conan Dependencies
<Bulleted list of all active Conan packages in `<name>/<version>` format, with a one-line note on purpose if known. Keep this section up to date whenever conanfile.py changes.>

## MoxPP Build System
<Existing MoxPP content verbatim, with all headings demoted one level>
```

### 7. Rewrite `README.md`

Ask the user directly: **"Do you want me to rewrite README.md for your project now?"**

If yes, ask for any additional details needed beyond what was already gathered (e.g. badges, links, usage examples, screenshots). Then replace the entire contents of `README.md` with a meaningful readme for the project. Do not include a Claude Code section — `BUILDING.md` already covers that and persists as the reference for build and tooling documentation. The only required carry-over is a short line pointing readers to `BUILDING.md` for build instructions, dependencies, and tooling (including Claude Code integration).

If no, remind the user that the current README.md is the MoxPP template readme and should be replaced before the project goes public.

### 8. Confirm and summarize

List all files changed and remind the user to run `mox init` (or `./mox.sh init`) to regenerate project files after these changes.
