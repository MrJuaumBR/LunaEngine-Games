# `info.yaml` – Game Metadata Reference

This file is required for every game in the `games/` folder. It tells the launcher how to display, run, and back up your game.

---

## Example `info.yaml`

```yaml
title: My Awesome Game
version: 1.2.3
author: YourName
tags:
  - adventure
  - puzzle
  - retro
type: game
description: A thrilling journey through time and space.
main_file: main.py
icon: assets/icon.png
banner: assets/banner.jpg
color1: "#ff6b6b"
color2: "#4ecdc4"
contacts:
  discord: https://discord.gg/example
  homepage: https://mygame.com
args:
  username: true
  fullscreen: false
save_type: folder
save_data_path: saves/
source: https://github.com/YourName/MyAwesomeGame
system_requirements:
  storage: null        # auto = consumed space; or e.g. "150 MB"
  os: [W, L]           # default ["W"]; case-insensitive aliases accepted
```

## Field Descriptions

### Required Fields
| Field     | Type   | Description |
|-----------|--------|-------------|
| `title` | string | The display name of the game (used in the store/library). |
| `version`| string | Version string (e.g., `1.0.0`, `0.2.1`). |
| `author` | string | Name of the game’s author. |
| `tags` | list of strings | Categories or keywords (e.g., `["arcade", "puzzle"]`). Can also be a comma-separated string in YAML. |
| `type` | string | Game type (e.g., `game`, `demo`, `tool`). Currently used for categorization. |
| `description` | string | Short description shown in the game details panel. |
| `main_file` | string | Entry point script (usually `main.py`). The launcher runs this with the embedded Python. |
| `icon` | string | Path to the game’s icon (relative to the game folder). Recommended size: 256×256 |

### Optional Fields
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `banner` | string or null | `null` | Path to a banner image (e.g., for a hero header). Not currently used in the UI but reserved. |
| `color1` | string (hex) | `null` | Primary accent color (e.g., `"#3b82f6"`). Used for card borders and buttons. |
| `color2` | string (hex) | `null` | Secondary accent color (e.g., for delete button). |
| `contacts` | dictionary | `{}` | Social or support links. Keys can be `discord`, `homepage`, `github`, etc. |
| `args` | dictionary | `{}` | Command-line arguments to pass to the game. Supported keys:<br>- `username` (bool): if `true`, the launcher will pass `--username:<PlayerName>`<br>- `fullscreen` (bool): if `true`, the launcher will pass `--fullscreen` (the game must handle this flag).<br>Other keys are ignored for now. |
| `save_type` | string or null | `null` | Describes how the game stores its save data:<br>- `"file"` – a single file (e.g., `leaderboard.json`)<br>- `"folder"` – an entire folder (e.g., `saves/`)<br>- `null` or omitted – the game has no save data to back up. |
| `save_data_path` | string | `""` | Relative path inside the game folder to the save data (file or folder). Only used if `save_type` is set. |
| `source` | string or null | `null` | Link to the game’s **source code** (e.g. a GitHub repo URL). Used by the launcher as the “View Source” link. If omitted: **local games** get the relative folder path (`games/<folder>`), **external games** get their `repo_url`. |
| `system_requirements` | dictionary | see below | Minimum requirements used for display / compatibility filtering. |

---

## System Requirements

```yaml
system_requirements:
  storage: null        # or "150 MB" / 150 (MB)
  os: [W, L]           # or "Windows, Linux" / "W, Linux" / "Mac"
```

### `storage`
- If `null` (or omitted) → automatically filled with the game's **consumed disk space** in `MB` (e.g. `"12.34 MB"`).
- If a **number** → treated as MB (e.g. `150` → `"150.0 MB"`).
- If a **string** → used as-is (e.g. `"150 MB"`, `"1.2 GB"`).

### `os`
- Case-insensitive.
- Accepts **aliases** and **codes** interchangeably.
- Input may be a single string, a comma-separated string, or a list.
- If omitted / empty / unrecognized → defaults to `["W"]` (Windows only).

**Accepted aliases (case-insensitive):**

| OS       | Code | Aliases |
|----------|------|---------|
| Windows  | `W`  | `w`, `win`, `windows`, `windows 7`, `windows 8`, `windows 10`, `windows 11`, `win7`, `win8`, `win10`, `win11` |
| Linux    | `L`  | `l`, `lin`, `linux`, `ubuntu`, `debian`, `fedora`, `arch`, `archlinux` |
| macOS    | `M`  | `m`, `mac`, `macos`, `mac os`, `mac os x`, `osx`, `os x`, `darwin`, `apple` |

**Examples (all valid, all produce `["W", "L"]`):**

```yaml
system_requirements:
  os: [W, L]
```

```yaml
system_requirements:
  os: "Windows, Linux"
```

```yaml
system_requirements:
  os: ["win10", "Ubuntu"]
```

The output in `data.json` is always normalized to an **ordered list of codes** (Windows → Linux → macOS):

```json
"system_requirements": { "storage": "12.34 MB", "os": ["W", "L"] }
```

---

## Source Code Link

```yaml
source: https://github.com/YourName/MyAwesomeGame
```

- If provided, `data.json` will expose it as `"source"`.
- If omitted:
  - **Local game** → the relative folder path (`games/My Awesome Game`) is used.
  - **External game** (from `ext.json`) → the repository URL is used.

---

## Screenshots

Place image files inside a folder named **`screenshots/`** at the game root:

```
games/
└── My Awesome Game/
    ├── info.yaml
    ├── main.py
    ├── icon.png
    └── screenshots/
        ├── 1.png
        ├── 2.jpg
        └── menu.webp
```

- Supported extensions: **png, jpg, jpeg, webp, gif**.
- All detected files (including subfolders) are listed under the `screenshots` field in `data.json`, using paths relative to the game root (forward slashes).
- Screenshots are also included in the packaged game zip (so they are available locally after install).

Example output:

```json
"screenshots": ["screenshots/1.png", "screenshots/2.jpg", "screenshots/menu.webp"]
```

If the folder is missing or empty, `screenshots` will be `[]`.

---

## Build Output

Packaged zips are written to the **`games-build/`** folder at the project root. The generated **`data.json`** is written to the **project root** (next to `generate_data.py`):

```
project/
├── games/
│   └── My Awesome Game/
├── games-build/
│   ├── My Awesome Game-1.2.3.zip
│   └── Other Game-0.1.0.zip
├── data.json               <-- launcher data (root)
├── generate_data.py
├── launcher_tool.py
└── information_guide.md
```

- `generate_data.py` (and `launcher_tool.py generate`) write **`data.json` at the project root** and **all zips to `games-build/`**.
- Old versions of the same game title (e.g. `My Awesome Game-1.0.0.zip`) are automatically removed when a new version is packaged.
- `clean` does **not** touch `games-build/` nor `data.json` — it only cleans the `launcher/` folder.

Every game entry in `data.json` includes:

| Field | Description |
|-------|-------------|
| `source` | Link to the source code (repo URL if set, else `games/<folder>` for local games). |
| `build`  | Link to the zipped build: `games-build/<title>-<version>.zip`. |

Example entry:

```json
{
  "title": "My Awesome Game",
  "version": "1.2.3",
  "source": "https://github.com/YourName/MyAwesomeGame",
  "build": "games-build/My Awesome Game-1.2.3.zip"
}
```

> `build` is **auto-generated** by `generate_data.py` — do not add it to `info.yaml`.

---

## Notes

- The `requirements.txt` file (if present) is not part of `info.yaml`. It is used by the launcher to install Python dependencies.
- The `external_game` flag is automatically set by the launcher when processing external repositories (see `ext.json`). Do not add it to `info.yaml`.
- The `build` field is also auto-generated. Do not add it to `info.yaml`.
- All paths are relative to the game’s root folder.
- The `args` dictionary is extensible – you can add custom flags, but only `username` and `fullscreen` are handled by the launcher natively.

---

## Complete Minimal Example

```yaml
title: TicTacToe
version: 0.0.1
author: MrJuaumBR
tags:
  - simple
  - arcade
type: game
description: Classic Tic Tac Toe
main_file: main.py
icon: icon.png
banner: null
color1: null
color2: null
contacts:
args:
  username: false
save_type: null
save_data_path: ""
source: null
system_requirements:
  storage: null
  os: [W]
```

---

## Adding Save Support (Example)

If your game saves a progress file called `game.sav` in the root folder:

```yaml
save_type: file
save_data_path: game.sav
```

If it saves a whole folder `save_data/`:

```yaml
save_type: folder
save_data_path: save_data/
```

---

## Adding Contacts (Example)

If you want to add Contacts to the Launcher so the user can interact with the devs, or receive support:

```yaml
contacts:
  - discord:  # needs to be "discord", otherwise it will be ignored
    - url: discord.gg/...
    - name: Discord Server Name
  - youtube:  # same as "discord"
    - url: youtube.com/@...
    - name: My Youtube Channel
  - ...
```

Currently supported platforms:

| Platform | Icon | Contacts - key |
|----------|------|----------------|
| YouTube  | Yes  | `youtube`      |
| Discord  | Yes  | `discord`      |
| GitHub   | Yes  | `github`       |
| Trello   | Yes  | `trello`       |
| Custom   | No   | `custom`       |