#!/usr/bin/env python3
"""
Generate data.json for the launcher.

Standalone command that:
  - Scans every game folder inside `games/`
  - Reads each `info.yaml` (including system_requirements + screenshots)
  - Packages each game into a zip under `games-build/`
  - Downloads external games listed in `ext.json` (if present)
  - Writes `data.json`
"""

import os
import sys
import json
import shutil
import stat
import tempfile
import argparse
from pathlib import Path
from datetime import datetime

try:
    import yaml
    import requests
    import zipfile
except ImportError as e:
    print(f"Missing required module: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml requests", file=sys.stderr)
    sys.exit(1)


# ----------------------------------------------------------------------
# Paths & constants
# ----------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.resolve()
GAMES_DIR = ROOT_DIR / "games"
GAMES_BUILD_DIR = ROOT_DIR / "games-build"
TEMP_DIR = ROOT_DIR / "temp"

BLACKLIST_FOLDERS = {'.venv', '.vscode', '__pycache__', '.github'}
BLACKLIST_EXTENSIONS = {'md', 'txt', 'json', 'pyc', 'aseprite', 'ase', 'zip'}
BLACKLIST_FILES = {'.gitignore', '.gitattributes', '.gitkeep', '.gitmodules'}

# Screenshots detection
SCREENSHOTS_FOLDER = "screenshots"
SCREENSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# OS codes and aliases
DEFAULT_OS = ["W"]
OS_ORDER = ["W", "L", "M"]
OS_ALIASES = {
    # Windows
    "w": "W", "win": "W", "windows": "W",
    "windows 7": "W", "windows 8": "W", "windows 10": "W", "windows 11": "W",
    "win7": "W", "win8": "W", "win10": "W", "win11": "W",
    # Linux
    "l": "L", "lin": "L", "linux": "L",
    "ubuntu": "L", "debian": "L", "fedora": "L", "arch": "L", "archlinux": "L",
    # macOS
    "m": "M", "mac": "M", "macos": "M", "mac os": "M", "mac os x": "M",
    "osx": "M", "os x": "M", "darwin": "M", "apple": "M",
}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def remove_readonly(func, path, excinfo):
    """Make a file writable and retry deletion (for shutil.rmtree)."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def count_files(folder: Path) -> tuple[int, float]:
    count = 0
    size = 0.0
    for item in folder.iterdir():
        if item.is_dir():
            if item.name in BLACKLIST_FOLDERS:
                continue
            c, s = count_files(item)
        else:
            if item.name in BLACKLIST_FILES:
                continue
            if item.suffix.lstrip('.') in BLACKLIST_EXTENSIONS:
                continue
            c = 1
            s = item.stat().st_size / (1024 ** 2)
        count += c
        size += s
    return count, size


def delete_save_data(game_root: Path, game_info: dict) -> None:
    save_type = game_info.get("save_type")
    save_data_path = game_info.get("save_data_path", "")
    if not save_type or not save_data_path:
        return
    target = game_root / save_data_path
    if not target.exists():
        return
    try:
        if target.is_dir():
            shutil.rmtree(target, onexc=remove_readonly)
            print(f"   Deleted save folder: {target}")
        else:
            target.unlink()
            print(f"   Deleted save file: {target}")
    except Exception as e:
        print(f"   Warning: could not delete {target}: {e}")


def clean_old_zips(game_title: str, current_version: str) -> None:
    if not GAMES_BUILD_DIR.exists():
        return
    current_zip_name = f"{game_title}-{current_version}.zip"
    for zip_path in GAMES_BUILD_DIR.glob(f"{game_title}-*.zip"):
        if zip_path.name != current_zip_name:
            try:
                zip_path.unlink()
                print(f"   Removed old zip: {zip_path.name}")
            except Exception as e:
                print(f"   Warning: could not remove {zip_path.name}: {e}")


def create_zip(game_info: dict, game_path: Path) -> None:
    game_name = game_info["title"]
    version = game_info["version"]
    zip_name = f"{game_name}-{version}"
    temp_game_dir = TEMP_DIR / game_name
    if temp_game_dir.exists():
        shutil.rmtree(temp_game_dir, onexc=remove_readonly)
    temp_game_dir.mkdir(parents=True)
    for item in game_path.iterdir():
        if item.is_dir():
            if item.name in BLACKLIST_FOLDERS:
                continue
            shutil.copytree(item, temp_game_dir / item.name)
        else:
            if item.name in BLACKLIST_FILES:
                continue
            if item.suffix.lstrip('.') in BLACKLIST_EXTENSIONS:
                continue
            shutil.copy2(item, temp_game_dir / item.name)

    GAMES_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(GAMES_BUILD_DIR / zip_name), 'zip', temp_game_dir)
    shutil.rmtree(temp_game_dir, onexc=remove_readonly)


def load_requirements(game_path: Path) -> list[str]:
    req_file = game_path / "requirements.txt"
    if req_file.exists():
        with open(req_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []


def collect_screenshots(game_path: Path) -> list[str]:
    """Return relative paths of screenshots found in the game's `screenshots/` folder."""
    screenshots_dir = game_path / SCREENSHOTS_FOLDER
    if not screenshots_dir.is_dir():
        return []
    paths = []
    for item in sorted(screenshots_dir.rglob("*")):
        if item.is_file() and item.suffix.lower() in SCREENSHOT_EXTENSIONS:
            rel = item.relative_to(game_path).as_posix()
            paths.append(rel)
    return paths


def normalize_os_list(value) -> list[str]:
    """Normalize OS entries (str / list / None) to ordered list of 'W'/'L'/'M'."""
    if value is None:
        return list(DEFAULT_OS)

    if isinstance(value, str):
        entries = [v.strip() for v in value.split(",") if v.strip()]
    elif isinstance(value, list):
        entries = [str(v).strip() for v in value if str(v).strip()]
    else:
        return list(DEFAULT_OS)

    codes = set()
    for entry in entries:
        code = OS_ALIASES.get(entry.lower())
        if code:
            codes.add(code)

    if not codes:
        return list(DEFAULT_OS)

    return [c for c in OS_ORDER if c in codes]


def normalize_storage(value, total_size_mb: float) -> str:
    """Return storage string. Auto-fills from computed size when value is None."""
    if value is None:
        return f"{round(total_size_mb, 2)} MB"
    if isinstance(value, (int, float)):
        return f"{round(float(value), 2)} MB"
    if isinstance(value, str):
        return value.strip()
    return f"{round(total_size_mb, 2)} MB"


def finalize_system_requirements(data: dict, total_size_mb: float) -> dict:
    sr = data.get("system_requirements") or {}
    if not isinstance(sr, dict):
        sr = {}
    return {
        "storage": normalize_storage(sr.get("storage"), total_size_mb),
        "os": normalize_os_list(sr.get("os")),
    }


def parse_contacts(contacts_data):
    """Convert YAML contacts into a consistent dict structure."""
    if not contacts_data:
        return {}
    result = {}
    if isinstance(contacts_data, dict):
        for platform, value in contacts_data.items():
            if isinstance(value, list):
                entries = []
                for item in value:
                    if isinstance(item, dict):
                        url = item.get("url")
                        name = item.get("name", platform.capitalize())
                        if url:
                            entries.append({"url": url, "name": name})
                    elif isinstance(item, str):
                        entries.append({"url": item, "name": platform.capitalize()})
                if entries:
                    result[platform] = entries
            elif isinstance(value, str):
                result[platform] = [{"url": value, "name": platform.capitalize()}]
    elif isinstance(contacts_data, list):
        for item in contacts_data:
            if isinstance(item, dict):
                for platform, val in item.items():
                    if isinstance(val, list):
                        entries = []
                        for entry in val:
                            if isinstance(entry, dict):
                                url = entry.get("url")
                                name = entry.get("name", platform.capitalize())
                                if url:
                                    entries.append({"url": url, "name": name})
                            elif isinstance(entry, str):
                                entries.append({"url": entry, "name": platform.capitalize()})
                        if entries:
                            result[platform] = entries
                    elif isinstance(val, str):
                        result[platform] = [{"url": val, "name": platform.capitalize()}]
    return result


def parse_game_info(game_path: Path) -> dict:
    yaml_file = game_path / "info.yaml"
    if not yaml_file.exists():
        raise FileNotFoundError(f"Missing info.yaml in {game_path}")
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    required = ["title", "version", "author", "type", "description", "main_file", "icon"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in {yaml_file}")

    data.setdefault("banner", None)
    data.setdefault("color1", None)
    data.setdefault("color2", None)
    data.setdefault("contacts", {})
    data.setdefault("args", {})
    data.setdefault("tags", [])
    data.setdefault("save_type", None)
    data.setdefault("save_data_path", "")
    data.setdefault("system_requirements", {})
    data.setdefault("source", None)

    data["contacts"] = parse_contacts(data.get("contacts"))

    if isinstance(data["tags"], str):
        data["tags"] = [t.strip() for t in data["tags"].split(',') if t.strip()]

    if not isinstance(data["args"], dict):
        data["args"] = {}

    # system_requirements is finalized later (needs total_size_mb)
    if not isinstance(data["system_requirements"], dict):
        data["system_requirements"] = {}

    return data


def download_and_process_external_repo(repo_url: str) -> dict | None:
    repo_url = repo_url.rstrip('/')
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 2:
        print(f"   Invalid GitHub URL: {repo_url}")
        return None
    owner, repo = parts[-2], parts[-1]

    for branch in ['main', 'master']:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        try:
            print(f"   Downloading {repo} from {zip_url}")
            resp = requests.get(zip_url, timeout=30)
            if resp.status_code == 200:
                break
        except Exception:
            continue
    else:
        print(f"   Failed to download {repo}: no valid branch found")
        return None

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp.write(resp.content)
        tmp_zip = Path(tmp.name)

    extract_dir = TEMP_DIR / f"ext_{repo}"
    if extract_dir.exists():
        shutil.rmtree(extract_dir, onexc=remove_readonly)
    extract_dir.mkdir(parents=True)

    with zipfile.ZipFile(tmp_zip, 'r') as zf:
        zf.extractall(extract_dir)

    tmp_zip.unlink()

    subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
    if not subdirs:
        print(f"   No subdirectory found in extracted repo {repo}")
        shutil.rmtree(extract_dir, onexc=remove_readonly)
        return None
    repo_root = subdirs[0]

    try:
        info = parse_game_info(repo_root)
    except Exception as e:
        print(f"   Failed to parse info.yaml in {repo}: {e}")
        shutil.rmtree(extract_dir, onexc=remove_readonly)
        return None

    delete_save_data(repo_root, info)
    total_files, total_size = count_files(repo_root)
    requirements = load_requirements(repo_root)
    screenshots = collect_screenshots(repo_root)
    create_zip(info, repo_root)
    clean_old_zips(info['title'], info['version'])
    shutil.rmtree(extract_dir, onexc=remove_readonly)

    record = {
        **info,
        "source": repo_url,                                              
        "build": f"games-build/{info['title']}-{info['version']}.zip",   
        "total_files": total_files,
        "total_size_mb": round(total_size, 2),
        "requirements": requirements,
        "compact_file": f"{info['title']}-{info['version']}.zip",
        "external_game": True,
        "repo_url": repo_url,
        "screenshots": screenshots,
        "system_requirements": finalize_system_requirements(info, total_size),
    }
    print(f"✓ Packaged external game {info['title']} v{info['version']} from {repo_url}")
    return record


# ----------------------------------------------------------------------
# Subcommand entry point
# ----------------------------------------------------------------------
def subcommand_generate(args=None):
    """Execute the generate subcommand (writes games/data.json)."""
    if not GAMES_DIR.exists():
        print("Error: 'games' folder not found.", file=sys.stderr)
        sys.exit(1)

    # Reset temp working dir
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, onexc=remove_readonly)
    TEMP_DIR.mkdir()

    # Ensure the build folder exists
    GAMES_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    games_metadata = []

    for game_folder in GAMES_DIR.iterdir():
        if not game_folder.is_dir():
            continue
        try:
            info = parse_game_info(game_folder)
            delete_save_data(game_folder, info)
            total_files, total_size = count_files(game_folder)
            requirements = load_requirements(game_folder)
            screenshots = collect_screenshots(game_folder)

            source = info.get("source") or game_folder.relative_to(ROOT_DIR).as_posix()

            record = {
                **info,
                "source": source,                                                
                "build": f"games-build/{info['title']}-{info['version']}.zip",   
                "total_files": total_files,
                "total_size_mb": round(total_size, 2),
                "requirements": requirements,
                "compact_file": f"{info['title']}-{info['version']}.zip",
                "external_game": False,
                "screenshots": screenshots,
                "system_requirements": finalize_system_requirements(info, total_size),
            }
            games_metadata.append(record)
            create_zip(info, game_folder)
            clean_old_zips(info['title'], info['version'])
            print(f"✓ Packaged {info['title']} v{info['version']}")
        except Exception as e:
            print(f"✗ Failed to process {game_folder.name}: {e}")

    # External games from ext.json
    ext_json_path = ROOT_DIR / "ext.json"
    if ext_json_path.exists():
        with open(ext_json_path, 'r', encoding='utf-8') as f:
            ext_data = json.load(f)
        games_urls = ext_data.get("games_url", [])
        for url in games_urls:
            print(f"\nProcessing external repo: {url}")
            record = download_and_process_external_repo(url)
            if record:
                if any(g['title'] == record['title'] for g in games_metadata):
                    print(f"  Skipping duplicate game title '{record['title']}' from external repo")
                    continue
                games_metadata.append(record)

    output = {
        "info": {
            "version": 0,
            "author": "MrJuaumBR",
            "total_games": len(games_metadata),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "games": games_metadata,
    }

    data_json_path = ROOT_DIR / "data.json"
    with open(data_json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n Done. Processed {len(games_metadata)} games. data.json written.")
    print(f"   Zips stored in: {GAMES_BUILD_DIR}")
    return len(games_metadata)


def main():
    parser = argparse.ArgumentParser(
        description="Generate data.json and package games into games-build/."
    )
    parser.parse_args()
    subcommand_generate()


if __name__ == "__main__":
    main()