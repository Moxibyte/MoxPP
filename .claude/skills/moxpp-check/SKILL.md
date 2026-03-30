---
name: moxpp-check
description: Checks the integrity of CLAUDE.md against the actual project structure. Use when CLAUDE.md may be out of sync with mox.lua, conanfile.py, build.lua files, README.md, or LICENSE.
---

# MoxPP CLAUDE.md Integrity Check

Audit `CLAUDE.md` against the actual project files and propose any corrections. Work through each check below, then present a consolidated diff of all proposed changes for the user to confirm before editing anything.

## Steps

### 1. Read all source-of-truth files

Read the following files in parallel:
- `CLAUDE.md` — current documented state
- `mox.lua` — ground truth for project name, C++ version, architecture, macro prefix, configurations, unit test setting
- `conanfile.py` — ground truth for Conan dependencies and options
- `README.md` — project description and overview
- `LICENSE` (if it exists) — license type

Then discover and read all `build.lua` files in the project:
- **single**: `src/build.lua`
- **flat**: `src/*/build.lua`
- **hierarchical**: `src/*/*/build.lua`
- **manual**: search recursively under `src/` for any `build.lua`
- Always also check `test/build.lua` if `cmox_unit_test_src` is set

### 2. Check project name

Compare the `# <Heading>` at the top of `CLAUDE.md` against `cmox_product_name` in `mox.lua`. Flag if they differ.

### 3. Check project description

Compare the description paragraph(s) below the top heading in `CLAUDE.md` against the content of `README.md`. Flag if `CLAUDE.md` is missing a description or if it appears significantly out of date relative to `README.md`. Do not require word-for-word matches — flag only meaningful divergences in purpose, audience, or scope.

### 4. Check Conan dependencies

Parse all `self.requires("name/version")` calls from `conanfile.py`. Compare the resulting list against the `## Conan Dependencies` section in `CLAUDE.md`:
- Flag any package present in `conanfile.py` but missing from `CLAUDE.md`
- Flag any package listed in `CLAUDE.md` but absent from `conanfile.py`
- Flag any version mismatches

### 5. Check unit test setting

Read `cmox_unit_test_src` from `mox.lua`:
- If `nil`: verify the `test/` directory does not exist. If it does, warn the user — it should be deleted.
- If set to a folder name: verify that folder exists at the repo root.

### 6. Check build.lua projects

For each discovered `build.lua`, extract the project name from `mox_project(...)`. Check:
- No two projects share the same UUID — flag any duplicates.
- Each project's source directory contains at least one `.cpp` file. For `sharedlib`/`staticlib` projects, verify `dummy.cpp` is present.

### 7. Check license

If a `LICENSE` file exists, check whether `CLAUDE.md` mentions the license. If not, note it as a minor gap (non-blocking).

### 8. Present findings and propose edits

Summarise all findings grouped by severity:
- **Error** — factual mismatch that will mislead Claude (wrong name, missing/wrong dependency, duplicate UUID)
- **Warning** — gap that reduces Claude's effectiveness (missing description, missing dependency note)
- **Info** — minor or cosmetic gap (license mention, stale wording)

For each Error and Warning, show the exact proposed change to `CLAUDE.md`. Ask the user to confirm before applying any edits.
