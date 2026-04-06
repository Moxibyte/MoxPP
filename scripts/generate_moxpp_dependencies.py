"""
Generate ./dependencies/dependencies.lua from ./dependencies.yml

For each dependency entry the flow is:
  1. If 'download' is specified: download the archive and extract it into 'folder'.
     The step is skipped when 'folder' already exists unless --force-download is given.
  2. If 'build' is specified: run that Python script with the current interpreter.
  3. Copy DLLs listed under copy_dll into ./dlls/Debug-<arch> or ./dlls/Release-<arch>
     based on the section they are declared in (all -> both, debug/release -> respective).
  4. Flatten the YAML sections for the target --arch into all/debug/release and emit
     a hardcoded Lua table plus moxpp_dependencies_build / moxpp_dependencies_link
     into ./dependencies/dependencies.lua.

dependencies.yml format:
  dependencies:
    - download: <url>           # optional - if given, archive is fetched and extracted
      folder:   <local-folder>  # folder relative to repo root
      build:    <script.py>     # optional - path relative to repo root
      # Every section below is optional. Omitted sections are treated as empty.
      # Each section accepts: include_dirs, lib_dirs, links, defines, copy_dll  (all optional lists)
      # copy_dll: flat-copies the listed paths (relative to folder) into ./dlls/<Conf>-<arch>/
      #
      # Plain sections (arch-independent):
      #   all     - applied unconditionally
      #   debug   - applied when is_debug == true
      #   release - applied when is_debug == false
      #
      # Architecture-qualified sections (merged into plain sections at generation
      # time for the target --arch, e.g. x86_64):
      #   all_x86_64, debug_x86_64, release_x86_64
      #   (use the premake5 arch name as returned by MOX_ARCH_MAP["premake_arch"])

Copyright (c) 2026 Moxibyte GmbH

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
import mox
import yaml
import shutil
import zipfile
import tarfile
import platform
import argparse
import subprocess
import urllib.request

# ---------------------------------------------------------------------------
# Download / extract helpers
# ---------------------------------------------------------------------------

def _extract_tar(path, dest, mode):
    with tarfile.open(path, mode) as t:
        try:
            t.extractall(dest, filter=tarfile.data_filter)
        except TypeError:
            # Python < 3.12 does not support the filter keyword
            t.extractall(dest)  # noqa: S202


_EXTRACTORS = {
    '.zip':     lambda p, d: zipfile.ZipFile(p).extractall(d),
    '.tar.gz':  lambda p, d: _extract_tar(p, d, 'r:gz'),
    '.tgz':     lambda p, d: _extract_tar(p, d, 'r:gz'),
    '.tar.bz2': lambda p, d: _extract_tar(p, d, 'r:bz2'),
    '.tar.xz':  lambda p, d: _extract_tar(p, d, 'r:xz'),
    '.tar':     lambda p, d: _extract_tar(p, d, 'r'),
}


def _archive_suffix(url):
    url_lower = url.lower()
    for suffix in ('.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.zip', '.tar'):
        if url_lower.endswith(suffix):
            return suffix
    return None


def download_and_extract(url, folder):
    """Download *url* and extract (or copy) into *folder*."""
    os.makedirs(folder, exist_ok=True)
    tmp = os.path.join(folder, '_moxpp_download_tmp')
    print(f'  Downloading {url} ...')
    urllib.request.urlretrieve(url, tmp)

    suffix = _archive_suffix(url)
    if suffix and suffix in _EXTRACTORS:
        print(f'  Extracting to {folder} ...')
        _EXTRACTORS[suffix](tmp, folder)
        os.remove(tmp)
    else:
        # Not a known archive - rename to the original filename
        dest = os.path.join(folder, os.path.basename(url.split('?')[0]))
        os.replace(tmp, dest)

# ---------------------------------------------------------------------------
# Section flattening
# ---------------------------------------------------------------------------

_FLAT_VARIANTS = ('all', 'debug', 'release')
_SECTION_KEYS  = ('include_dirs', 'lib_dirs', 'links', 'defines')
# Only these keys contain file-system paths that need the workspace prefix.
_PATH_KEYS     = frozenset(('include_dirs', 'lib_dirs'))


def _merge_section(base, extra):
    """Return a new dict with lists from *extra* appended to those in *base*."""
    result = {}
    for key in _SECTION_KEYS:
        result[key] = list(base.get(key) or []) + list((extra or {}).get(key) or [])
    return result


def _flatten_dep(dep, premake_arch):
    """Flatten arch-qualified sections into plain all/debug/release for *premake_arch*.

    Path-type keys (include_dirs, lib_dirs) are prefixed with
    %{wks.location}/<folder>/ so premake5 resolves them correctly.
    """
    folder = dep.get('folder', '').strip('/')
    flat = {}
    for variant in _FLAT_VARIANTS:
        base   = dep.get(variant) or {}
        arch   = dep.get(f'{variant}_{premake_arch}') or {}
        merged = _merge_section(base, arch)
        section = {}
        for key in _SECTION_KEYS:
            if key in _PATH_KEYS:
                section[key] = [
                    f'%{{wks.location}}/{folder}/{v.lstrip("/")}' for v in merged[key]
                ]
            else:
                section[key] = merged[key]
        flat[variant] = section
    return flat


def _copy_dlls(dep, premake_arch):
    """Copy DLLs declared under copy_dll into ./dlls/<Conf>-<arch>/ (flat, filename only)."""
    folder = dep.get('folder', '.')

    # Map each section to the conf folders it feeds into
    section_to_confs = {
        'all':     ('Debug', 'Release'),
        'debug':   ('Debug',),
        'release': ('Release',),
        f'all_{premake_arch}':     ('Debug', 'Release'),
        f'debug_{premake_arch}':   ('Debug',),
        f'release_{premake_arch}': ('Release',),
    }

    for section_name, confs in section_to_confs.items():
        dlls = (dep.get(section_name) or {}).get('copy_dll') or []
        for dll_rel in dlls:
            src = os.path.join(folder, dll_rel)
            if not os.path.isfile(src):
                print(f'  Warning: DLL not found: {src}')
                continue
            filename = os.path.basename(dll_rel)
            for conf in confs:
                dst_dir = f'./dlls/{conf}-{premake_arch}'
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, filename)
                print(f'  Copying {src} -> {dst}')
                shutil.copy2(src, dst)

# ---------------------------------------------------------------------------
# Lua templates
# ---------------------------------------------------------------------------

_LUA_INDENT = '    '

_LUA_HEADER = """\
-- Auto-generated by generate_moxpp_dependencies.py
-- DO NOT EDIT MANUALLY
"""

_LUA_TABLE_OPEN = """\
local moxpp_deps = {
"""

_LUA_TABLE_CLOSE = """\
}
"""

_LUA_FN_BUILD = """\
function moxpp_dependencies_build(conf, is_debug)
    local variant = is_debug and "debug" or "release"
    filter { "configurations:" .. conf }
        for _, dep in ipairs(moxpp_deps) do
            if #dep.all.include_dirs > 0 then includedirs(dep.all.include_dirs) end
            if #dep.all.defines      > 0 then defines(dep.all.defines)          end
            if #dep[variant].include_dirs > 0 then includedirs(dep[variant].include_dirs) end
            if #dep[variant].defines      > 0 then defines(dep[variant].defines)          end
        end
    filter {}
end
"""

_LUA_FN_LINK = """\
function moxpp_dependencies_link(conf, is_debug)
    local variant = is_debug and "debug" or "release"
    filter { "configurations:" .. conf }
        for _, dep in ipairs(moxpp_deps) do
            if #dep.all.lib_dirs > 0 then libdirs(dep.all.lib_dirs) end
            if #dep.all.links    > 0 then links(dep.all.links)       end
            if #dep[variant].lib_dirs > 0 then libdirs(dep[variant].lib_dirs) end
            if #dep[variant].links    > 0 then links(dep[variant].links)       end
        end
    filter {}
end
"""

# ---------------------------------------------------------------------------
# Lua emitter
# ---------------------------------------------------------------------------


def _lua_list(items):
    """Return a Lua table constructor for a list of strings."""
    if not items:
        return '{}'
    quoted = ', '.join(f'"{v}"' for v in items)
    return f'{{ {quoted} }}'


def _generate_lua(flat_deps):
    """Return the full text of dependencies.lua as a string."""
    lines = [_LUA_HEADER, '\n', _LUA_TABLE_OPEN]

    for flat in flat_deps:
        lines.append(f'{_LUA_INDENT}{{\n')
        for variant in _FLAT_VARIANTS:
            lines.append(f'{_LUA_INDENT * 2}{variant} = {{\n')
            for key in _SECTION_KEYS:
                lines.append(f'{_LUA_INDENT * 3}{key} = {_lua_list(flat[variant][key])},\n')
            lines.append(f'{_LUA_INDENT * 2}}},\n')
        lines.append(f'{_LUA_INDENT}}},\n')

    lines += [_LUA_TABLE_CLOSE, '\n', _LUA_FN_BUILD, '\n', _LUA_FN_LINK]
    return ''.join(lines)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        prog='generate_moxpp_dependencies.py',
        description='Process dependencies.yml and generate dependencies/dependencies.lua',
    )
    p.add_argument(
        '--deps-file', default='./dependencies.yml',
        help='Path to dependencies.yml (default: ./dependencies.yml)',
    )
    p.add_argument(
        '--output', default='./dependencies/dependencies.lua',
        help='Output Lua file (default: ./dependencies/dependencies.lua)',
    )
    p.add_argument(
        '--arch', default=platform.machine().lower(),
        help='Target architecture (host machine arch by default). Used to resolve '
             'arch-qualified YAML sections (e.g. all_x86_64) into the flat Lua table.',
    )
    p.add_argument(
        '--skip-download', action='store_true',
        help='Skip downloading even if a URL is specified',
    )
    p.add_argument(
        '--force-download', action='store_true',
        help='Re-download even if the target folder already exists',
    )
    p.add_argument(
        '--skip-build', action='store_true',
        help='Skip running build scripts',
    )
    args = p.parse_args()

    # Resolve premake arch name from the --arch argument (or host machine)
    raw_arch = args.arch.lower()
    premake_arch = mox.GetPlatformInfo(raw_arch)['premake_arch']
    print(f'Target architecture: {raw_arch} -> premake_arch={premake_arch}')

    # Load YAML (gracefully handle missing file)
    if not os.path.exists(args.deps_file):
        print(f'No {args.deps_file} found - generating empty dependencies.lua')
        deps_list = []
    else:
        with open(args.deps_file, 'r', encoding='utf-8') as fh:
            raw = yaml.safe_load(fh)
        deps_list = (raw or {}).get('dependencies') or []

    # Process each dependency
    flat_deps = []
    for dep in deps_list:
        folder       = dep.get('folder')
        url          = dep.get('download')
        build_script = dep.get('build')

        if folder:
            if url and not args.skip_download:
                if args.force_download or not os.path.exists(folder):
                    print(f'Dependency: {folder}')
                    download_and_extract(url, folder)
                else:
                    print(f'Dependency: {folder} (already present, skipping download)')
            elif not url and not os.path.exists(folder):
                print(
                    f'Warning: folder "{folder}" does not exist '
                    f'and no download URL was specified - skipping'
                )

        if build_script and not args.skip_build:
            print(f'  Running build script: {build_script}')
            result = subprocess.run([sys.executable, build_script], check=False)
            if result.returncode != 0:
                print(f'  Warning: build script exited with code {result.returncode}')

        _copy_dlls(dep, premake_arch)
        flat_deps.append(_flatten_dep(dep, premake_arch))

    # Generate Lua
    lua_text = _generate_lua(flat_deps)
    out_path = args.output
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(lua_text)
    print(f'Generated {out_path}')
