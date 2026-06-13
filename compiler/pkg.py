"""
ELIN Package Manager (Item 21)

Manages dependencies for ELIN projects. Dependencies are .elin files
from git repos or local paths. No registry server — just URLs and paths.

Usage:
    python3 pkg.py init                  Create elin.json manifest
    python3 pkg.py add <name> <source>   Add a dependency
    python3 pkg.py build                 Compile all .elin files together
    python3 pkg.py list                  List installed packages

Manifest format (elin.json):
{
    "name": "my_project",
    "version": "0.1.0",
    "dependencies": {
        "math": "https://github.com/user/elin-math",
        "strings": "./libs/strings"
    }
}
"""

import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from glob import glob


# Where downloaded packages live
PACKAGES_DIR = ".elin_packages"
MANIFEST_FILE = "elin.json"


def find_project_root():
    """Walk up from cwd looking for elin.json. Return its Path or None."""
    d = Path.cwd()
    while d != d.parent:
        if (d / MANIFEST_FILE).exists():
            return d
        d = d.parent
    # Check cwd itself
    if (Path.cwd() / MANIFEST_FILE).exists():
        return Path.cwd()
    return None


def cmd_init():
    """Create a blank elin.json in the current directory."""
    path = Path.cwd() / MANIFEST_FILE
    if path.exists():
        print(f"Error: {MANIFEST_FILE} already exists here.")
        return

    manifest = {
        "name": Path.cwd().name,
        "version": "0.1.0",
        "dependencies": {}
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Created {MANIFEST_FILE}")


def cmd_add(name, source):
    """Add a dependency. source can be a git URL or a local path."""
    root = find_project_root()
    if not root:
        print(f"Error: No {MANIFEST_FILE} found. Run 'pkg.py init' first.")
        return

    manifest_path = root / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text())

    if name in manifest["dependencies"]:
        print(f"Package '{name}' already exists. Updating source...")
        # Remove old version
        pkg_dir = root / PACKAGES_DIR / name
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)

    # Determine if source is a git URL or local path
    is_git = source.startswith("http://") or source.startswith("https://") or source.startswith("git@")

    packages_dir = root / PACKAGES_DIR
    packages_dir.mkdir(exist_ok=True)
    target_dir = packages_dir / name

    if is_git:
        print(f"Cloning {source} -> {PACKAGES_DIR}/{name}")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", source, str(target_dir)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error cloning: {result.stderr.strip()}")
            return
    else:
        # Local path — copy it
        src_path = Path(source).resolve()
        if not src_path.exists():
            print(f"Error: Source path '{source}' does not exist.")
            return
        print(f"Copying {source} -> {PACKAGES_DIR}/{name}")
        shutil.copytree(str(src_path), str(target_dir), dirs_exist_ok=True)

    # Update manifest
    manifest["dependencies"][name] = source
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Added '{name}' from {source}")


def cmd_remove(name):
    """Remove a dependency."""
    root = find_project_root()
    if not root:
        print(f"Error: No {MANIFEST_FILE} found.")
        return

    manifest = json.loads((root / MANIFEST_FILE).read_text())
    if name not in manifest["dependencies"]:
        print(f"Package '{name}' not found in dependencies.")
        return

    # Remove files
    pkg_dir = root / PACKAGES_DIR / name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)

    # Update manifest
    del manifest["dependencies"][name]
    (root / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Removed '{name}'")


def cmd_list():
    """List installed packages."""
    root = find_project_root()
    if not root:
        print(f"Error: No {MANIFEST_FILE} found.")
        return

    manifest = json.loads((root / MANIFEST_FILE).read_text())
    deps = manifest.get("dependencies", {})
    if not deps:
        print("No dependencies.")
        return

    packages_dir = root / PACKAGES_DIR
    for name, source in deps.items():
        installed = "installed" if (packages_dir / name).exists() else "NOT INSTALLED"
        print(f"  {name:20s} {source:40s} [{installed}]")


def find_elin_files(root):
    """Find all .elin files in the project, excluding .elin_packages."""
    files = []
    for path in sorted(root.rglob("*.elin")):
        # Skip the packages dir — we'll handle those separately
        if PACKAGES_DIR in str(path):
            continue
        files.append(path)
    return files


def find_package_elin_files(root):
    """Find all .elin files inside .elin_packages/."""
    pkg_dir = root / PACKAGES_DIR
    if not pkg_dir.exists():
        return []
    files = []
    for path in sorted(pkg_dir.rglob("*.elin")):
        files.append(path)
    return files


def cmd_build():
    """Compile all .elin files. Packages first, then project files."""
    root = find_project_root()
    if not root:
        print(f"Error: No {MANIFEST_FILE} found. Run 'pkg.py init' first.")
        return

    # Collect all source files
    pkg_files = find_package_elin_files(root)
    project_files = find_elin_files(root)

    if not project_files:
        print("Error: No .elin files found in project.")
        return

    all_sources = []
    source_labels = []

    # Package files come first (they define things the project uses)
    for f in pkg_files:
        all_sources.append(f.read_text())
        source_labels.append(f"pkg:{f.relative_to(root)}")

    # Project files
    for f in project_files:
        all_sources.append(f.read_text())
        source_labels.append(str(f.relative_to(root)))

    print(f"Building {len(project_files)} project file(s) + {len(pkg_files)} package file(s)")
    for label in source_labels:
        print(f"  - {label}")

    # Concatenate all sources
    combined = "\n".join(all_sources)

    # Compile
    compiler_dir = Path(__file__).parent
    sys.path.insert(0, str(compiler_dir))
    from compiler import compile, format_bytecode

    try:
        manifest = json.loads((root / MANIFEST_FILE).read_text())
        package_name = manifest.get("name", root.name)
        state = compile(combined.splitlines(), package_name)
        bytecode = format_bytecode(state)

        # Write output
        output_path = root / f"{package_name}.outz"
        output_path.write_text(bytecode)
        print(f"\nSuccess! Output: {output_path}")
        print("-" * 30)
        print(bytecode)
    except Exception as e:
        print(f"\nCompilation Error: {e}")


def main():
    if len(sys.argv) < 2:
        print("ELIN Package Manager")
        print("Usage:")
        print("  pkg.py init                  Create elin.json manifest")
        print("  pkg.py add <name> <source>   Add a dependency")
        print("  pkg.py remove <name>         Remove a dependency")
        print("  pkg.py list                  List installed packages")
        print("  pkg.py build                 Compile all files together")
        return

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: pkg.py add <name> <source>")
            print("  source can be a git URL or local path")
            return
        cmd_add(sys.argv[2], sys.argv[3])
    elif cmd == "remove" or cmd == "rm":
        if len(sys.argv) < 3:
            print("Usage: pkg.py remove <name>")
            return
        cmd_remove(sys.argv[2])
    elif cmd == "list" or cmd == "ls":
        cmd_list()
    elif cmd == "build":
        cmd_build()
    else:
        print(f"Unknown command: {cmd}")
        print("Available commands: init, add, remove, list, build")


if __name__ == "__main__":
    main()
