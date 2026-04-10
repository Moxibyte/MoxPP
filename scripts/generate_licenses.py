"""
Script that collects all license files and generate a .html license summary

This is how an additional licenses.yml file may look like:
> additional_licenses:
>   - name: MyLib
>     version: 1.0.0
>     license_files:
>       - "./path_to_license/LICENSE.txt"   # exact path
>       - "./vendor/mylib/LICENSE*"         # wildcard filename
>       - "./third_party/**/LICENSE"        # recursive glob
>
> strip_licenses:
>   - lib: <lib-name>     # must match the lib name exactly
>     file: <filename>    # filename to remove from that lib's license list

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

import glob
import html
import yaml
import pathlib
import markdown
import argparse
import pygments.formatters

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: 'Segoe UI', sans-serif;
      max-width: 960px;
      margin: 2rem auto;
      padding: 0 2rem;
      line-height: 1.7;
      color: #222;
      background: #fafafa;
    }}
    h1 {{ border-bottom: 2px solid #ccc; padding-bottom: .5rem; }}
    h2 {{ margin-top: 2.5rem; color: #444; }}
    h3 {{ margin-top: 2rem; color: #333; }}
    h4 {{ margin-top: 1.5rem; color: #555; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 2rem 0; }}
    pre {{
      background: #f4f4f4;
      border: 1px solid #ddd;
      border-radius: 6px;
      padding: 1.2rem;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.85rem;
    }}
    {pygments_css}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

def make_project_license(name: str, disclaimer: str, license_text: str) -> dict:
    return {"name": name, "disclaimer": disclaimer, "license_text": license_text}

def make_third_party_lib(name: str, version: str, licenses: dict[str, str]) -> dict:
    return {"name": name, "version": version, "licenses": licenses}

def _license_pre(text: str) -> str:
    """Wrap license text in an HTML <pre> block with all special chars escaped.
    Using raw HTML instead of markdown fenced code blocks avoids any breakage
    when the license text itself contains backticks or other markdown syntax."""
    return f"<pre><code>{html.escape(text.strip())}</code></pre>"

def build_markdown(project: dict, third_party: list[dict]) -> str:
    sections = []

    sections.append(f"# {project['name']}")
    if project["disclaimer"]:
        sections.append(project['disclaimer'])
    sections.append("## License")
    sections.append(_license_pre(project['license_text']))

    sections.append("## Third-Party Licenses")

    for lib in third_party:
        sections.append(f"### {lib['name']} (Version {lib['version']})")
        for filename, license_text in lib["licenses"].items():
            sections.append(f"#### {filename}")
            sections.append(_license_pre(license_text))

    # You are NOT obligated to keep this! But it would be nice :-)
    # Please make sure you read and understand the disclaimer
    sections.append("*Powered by [MoxPP C++ Template](https://github.com/Moxibyte/MoxPP) by Moxibyte GmbH*<br/>*Moxibyte GmbH is not liable for the correctness of this file if not distributed by Moxibyte GmbH. The correctness needs to be ensured by the final entity redistributing software using external lib(s). This is not legal advice!*")

    return "\n\n".join(sections)

def build_license_html(project: dict, third_party: list[dict]) -> str:
    pygments_css = pygments.formatters.HtmlFormatter(style="friendly").get_style_defs(".highlight")

    md_text = build_markdown(project, third_party)
    body = markdown.markdown(md_text, extensions=["fenced_code", "codehilite", "toc"])

    return HTML_TEMPLATE.format(title=f'{project["name"]} LICENSE', pygments_css=pygments_css, body=body)

def discover_conan_licenses(dependencies_root: str | pathlib.Path) -> list[dict]:
    dependencies_root = pathlib.Path(dependencies_root)
    host_root = dependencies_root / "full_deploy" / "host"

    third_party = []

    for lib_dir in sorted(host_root.iterdir()):
        if not lib_dir.is_dir():
            continue

        lib_name = lib_dir.name

        # Find most recent version using sorted() with version tuple key
        version_dirs = [v for v in lib_dir.iterdir() if v.is_dir()]
        if not version_dirs:
            continue

        latest_version_dir = sorted(
            version_dirs,
            key=lambda v: tuple(int(x) for x in v.name.split(".") if x.isdigit()),
        )[-1]
        lib_version = latest_version_dir.name

        # Use first platform found under Release/, Debug/ (compiled libs) or directly
        # under the version dir (header-only libs that have no Debug/Release level)
        for conf in ("Release", "Debug"):
            if (latest_version_dir / conf).is_dir():
                search_dir = latest_version_dir / conf
                break
        else:
            search_dir = latest_version_dir

        # Use first platform subdir that contains a licenses/ folder, or fall
        # back to search_dir itself (libs that omit the platform level)
        platform_dirs = [p for p in search_dir.iterdir() if p.is_dir()]
        licenses_dir = None
        for p in platform_dirs:
            candidate = p / "licenses"
            if candidate.is_dir():
                licenses_dir = candidate
                break
        if licenses_dir is None:
            candidate = search_dir / "licenses"
            if candidate.is_dir():
                licenses_dir = candidate
        if licenses_dir is None:
            continue

        # Collect all license files
        license_files = {
            f.name: f.read_text(encoding="utf-8", errors="replace")
            for f in sorted(licenses_dir.iterdir())
            if f.is_file()
        }

        if not license_files:
            continue

        third_party.append(make_third_party_lib(lib_name, lib_version, license_files))

    return third_party

def _expand_license_pattern(pattern: str) -> list[pathlib.Path]:
    """Expand a glob pattern to a sorted list of matching files.
    Falls back to treating the string as a literal path when no glob hits."""
    matched = sorted(glob.glob(pattern, recursive=True))
    if matched:
        return [p for m in matched if (p := pathlib.Path(m)).is_file()]
    p = pathlib.Path(pattern)
    return [p] if p.is_file() else []

def load_additional_licenses(control_file: str | pathlib.Path) -> list[dict] | None:
    control_file = pathlib.Path(control_file)

    if not control_file.is_file():
        return None

    with control_file.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    entries = data.get("additional_licenses") if data else None
    if not entries:
        return None

    third_party = []

    for entry in entries:
        name    = entry["name"]
        version = str(entry["version"])

        license_files = {}
        for pattern in entry.get("license_files", []):
            for path in _expand_license_pattern(pattern):
                license_files[path.name] = path.read_text(encoding="utf-8", errors="replace")

        if not license_files:
            continue

        third_party.append(make_third_party_lib(name, version, license_files))

    return third_party or None

def load_strip_licenses(control_file: str | pathlib.Path) -> list[dict] | None:
    control_file = pathlib.Path(control_file)
    if not control_file.is_file():
        return None
    with control_file.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    entries = data.get("strip_licenses") if data else None
    return entries or None

def apply_strip_licenses(third_party: list[dict], strips: list[dict]) -> list[dict]:
    for strip in strips:
        lib_name  = strip["lib"]
        file_name = strip["file"]
        for lib in third_party:
            if lib["name"] == lib_name:
                if file_name in lib["licenses"]:
                    del lib["licenses"][file_name]
                    print(f"  Stripped '{file_name}' from '{lib_name}'")
                else:
                    print(f"  Warning: '{file_name}' not found in '{lib_name}' — skipping strip")
                break
        else:
            print(f"  Warning: lib '{lib_name}' not found — skipping strip")
    # Drop libs whose entire license set was stripped away
    return [lib for lib in third_party if lib["licenses"]]

if __name__ == "__main__":
    # CLI Setup
    p = argparse.ArgumentParser(
        prog="generate_licenses.py", 
        description="Generate a LICENSE.html from project and third-party licenses.",
        allow_abbrev=False
    )
    p.add_argument("--project-name", type=str, default="MoxPP", help="Name of the project (default: MoxPP)")
    p.add_argument("--disclaimer", type=str, default=None, help="Optional project disclaimer text")
    p.add_argument("--project-license", type=str, default="./LICENSE", help="Path to the project license file (default: ./LICENSE)")
    p.add_argument("--additional-licenses", type=str, default=None, help="Path to the additional_licenses.yml control file")
    p.add_argument("--output", type=str, default="./LICENSE.html", help="Output path for the generated HTML file (default: ./LICENSE.html)")

    # CLI Parse and extraction
    args = p.parse_args()
    project_name        = args.project_name
    disclaimer          = args.disclaimer
    project_license     = pathlib.Path(args.project_license) if args.project_license else None
    additional_licenses = pathlib.Path(args.additional_licenses) if args.additional_licenses else None
    output_path         = pathlib.Path(args.output)

    # Echo
    print("Collecting and generating LICENSE file...")

    # Disclaimer text
    disclaimer_text = None
    if disclaimer is None:
        disclaimer_text = "**WARNING: This is the default output generated by MoxPP!**<br/>**Make sure to check the final generated license output and remove the disclaimer. This is not legal advice! Consult your lawyer!**"
    elif len(disclaimer) > 0:
        disclaimer_text = disclaimer

    # Project License text
    license_text = None
    if project_license is None or not project_license.exists():
        license_text = "Provide a LICENSE file to the project to add it to this file!"
    else:
        license_text = project_license.read_text()

    # Project License
    project = make_project_license(
        name         = project_name,
        disclaimer   = disclaimer_text,
        license_text = license_text,
    )

    # Third party
    third_party = discover_conan_licenses("./dependencies")
    if additional_licenses and additional_licenses.exists():
        additional = load_additional_licenses(additional_licenses)
        if additional:
            third_party.extend(additional)
        strips = load_strip_licenses(additional_licenses)
        if strips:
            third_party = apply_strip_licenses(third_party, strips)

    # Build license
    html = build_license_html(project, third_party)
    output_path.write_text(html, encoding="utf-8")
