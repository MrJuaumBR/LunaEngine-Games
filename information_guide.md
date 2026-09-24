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
```
## Field Descriptions
### Required Fields
| Field     | Type   | Description |
|-----------|--------|-------------|
| ``title`` | string | The display name of the game (used in the store/library). |
| ``version``| string | Version string (e.g., ``1.0.0``, ``0.2.1``). |
| ``author`` | string | Name of the game’s author. |
| ``tags`` | list of strings | Categories or keywords (e.g., ``["arcade", "puzzle"]``). Can also be a comma‑separated string in YAML. |
| ``type`` | string	| Game type (e.g., ``game``, ``demo``, ``tool``). Currently used for categorization. |
| ``description`` | string | Short description shown in the game details panel. |
|``main_file``| string | Entry point script (usually ``main.py``). The launcher runs this with the embedded Python.|
|``icon`` | string | Path to the game’s icon (relative to the game folder). Recommended size: 256×256|

### Optional Fields
| Field     | Type  | Default | Description |
|-----------|--------|-------------|-|
|``banner``|	string or null|	``null``|	Path to a banner image (e.g., for a hero header). Not currently used in the UI but reserved.|
|``color1``	|string (hex)	|``null``	|Primary accent color (e.g., ``"#3b82f6"``). Used for card borders and buttons.|
|``color2``	|string (hex)	|``null``	|Secondary accent color (e.g., for delete button).|
|``contacts``	|dictionary|	``{}``	|Social or support links. Keys can be ``discord``, ``homepage``, ``github``, etc.|
|``args``	|dictionary|	``{}``	|Command‑line arguments to pass to the game. Supported keys:</br>- ``username`` (bool): if ``true``, the launcher will pass ``--username:<PlayerName>``</br>- ``fullscreen`` (bool): if ``true``, the launcher will pass ``--fullscreen`` (the game must handle this flag).</br>Other keys are ignored for now.|
|``save_type`` |	string or null	|``null``	|Describes how the game stores its save data:</br>- ``"file"`` – a single file (e.g., ``leaderboard.json``)</br>- ``"folder"`` – an entire folder (e.g., ``saves/``)</br>- ``null`` or omitted – the game has no save data to back up.|
|``save_data_path``|	string|	``""``|	Relative path inside the game folder to the save data (file or folder). Only used if ``save_type`` is set. Examples:</br>- ``"leaderboard.json"``</br>- ``"saves/"``</br>- ``"data/save.data"``|

## Notes

- The ``requirements.txt`` file (if present) is not part of ``info.yaml``. It is used by the launcher to install Python dependencies.
- The ``external_game`` flag is automatically set by the launcher when processing external repositories (see ``ext.json``). Do not add it to ``info.yaml``.
- All paths are relative to the game’s root folder.
- The ``args`` dictionary is extensible – you can add custom flags, but only ``username`` and ``fullscreen`` are handled by the launcher natively.

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
```

## Adding Save Support (Example)

If your game saves a progress file called ``game.sav`` in the root folder:
```yaml
save_type: file
save_data_path: game.sav
```
If it saves a whole folder ``save_data/``:
```yaml
save_type: folder
save_data_path: save_data/
```

## Adding Contacts (Example)

If you want to add Contacts to the Launcher so the user can interact with the devs, or receive a support:
```yaml
contacts:
  - discord:  # Needs to be "discord" in that way, eitherwise, it will be ignored!
    - url: discord.gg/...
    - name: Discord Server Name
  - youtube: # Same of the "discord"
    - url: youtube.com/@...
    - name: My Youtube Channel
  - ...
```

The currently supported plataforms are:
| Plataform | Icon | Contacts - key |
| --------- | ---- | -------------- |
| YouTube   | Yes  | youtube        |
| Discord   | Yes  | discord        |
| GitHub    | Yes  | github         |
| Trello    | Yes  | trello         |
| Custom    | No   | custom         |