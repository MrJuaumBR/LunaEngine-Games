# assets/src/levels_data.py
import json
from pathlib import Path
from typing import Dict, Any, Tuple

class LevelData:
    def __init__(self, levels_folder: str = None):
        if levels_folder is None:
            self.levels_folder = Path(__file__).parent / "levels"
        else:
            self.levels_folder = Path(levels_folder)
        self.cache: Dict[int, Dict[str, Any]] = {}

    def get_level(self, level_num: int) -> Dict[str, Any]:
        if level_num in self.cache:
            return self.cache[level_num]
        file_path = self.levels_folder / f"level_{level_num}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Level {level_num} not found at {file_path}")
        with open(file_path) as f:
            data = json.load(f)
        required = ["width", "height", "tile_size", "tiles", "entities", "star_times"]
        for key in required:
            if key not in data:
                data[key] = {} if key == "star_times" else None
        self.cache[level_num] = data
        return data

    def get_tile(self, level_data: Dict[str, Any], gx: int, gy: int) -> int:
        tiles = level_data["tiles"]
        if gy < 0 or gy >= len(tiles) or gx < 0 or gx >= len(tiles[0]):
            return 1  # out of bounds = wall
        return tiles[gy][gx]

    def is_wall(self, level_data: Dict[str, Any], gx: int, gy: int) -> bool:
        """Only tile type 1 is a solid wall. Tile type 2 is visual only."""
        return self.get_tile(level_data, gx, gy) == 1

    def grid_to_pixel(self, level_data: Dict[str, Any], gx: int, gy: int, tile_size: int) -> Tuple[int, int]:
        return (gx * tile_size + tile_size // 2, gy * tile_size + tile_size // 2)

LEVEL_LOADER = LevelData()