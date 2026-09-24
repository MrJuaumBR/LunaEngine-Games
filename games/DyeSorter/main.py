from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.backend import OpenGLRenderer, TransitionType
from lunaengine.misc import Icons
from lunaengine.utils import humanize_time

from argparse import ArgumentParser
import pygame
from pathlib import Path
from typing import List, Optional
import os
import random
import sys
import json
from datetime import datetime
from time import time

COLORS = [
    ("RED", (200, 50, 50)),
    ("GREEN", (50, 200, 50)),
    ("BLUE", (50, 50, 200)),
    ("YELLOW", (200, 200, 50)),
    ("PINK", (200, 50, 200)),
    ("CYAN", (50, 200, 200)),
    ("ORANGE", (200, 100, 50)),
]

SEGMENTS_PER_BOTTLE = 5
MAX_UNDO = 3

MAX_COLUMNS = 7
MAX_ROWS = 4
MAX_BOTTLES = MAX_COLUMNS * MAX_ROWS

MAX_BOTTLE_WIDTH = 128
MAX_BOTTLE_HEIGHT = 256
MIN_BOTTLE_WIDTH = 64
MIN_BOTTLE_HEIGHT = 128

LIQUID_LEFT = 0.22
LIQUID_RIGHT = 0.78
LIQUID_TOP = 0.20
LIQUID_BOTTOM = 0.91


def create_save(root: Path | str) -> dict:
    assert isinstance(root, Path)
    le_file = root / "leaderboard.json"
    save = {"leaderboard": [], "last_user_name": ""}

    if le_file.exists():
        with open(le_file, "rb") as f:
            save = json.loads(f.read().decode("utf-8"))
    else:
        with open(le_file, "wb+") as f:
            f.write(json.dumps(save).encode("utf-8"))

    return save


def update_save(root: Path | str):
    assert isinstance(root, Path)
    le_file = root / "leaderboard.json"

    if not le_file.exists():
        global CONFIG
        CONFIG = create_save(root)

    with open(le_file, "wb+") as f:
        f.write(json.dumps(CONFIG).encode("utf-8"))


class Bottle:
    def __init__(self, index: int):
        self.index = index
        self.segments: List[Optional[tuple[int, int, int]]] = [
            None
        ] * SEGMENTS_PER_BOTTLE

    def is_empty(self) -> bool:
        return all(segment is None for segment in self.segments)

    def is_full(self) -> bool:
        return all(segment is not None for segment in self.segments)

    def empty_slots(self) -> int:
        return sum(segment is None for segment in self.segments)

    def filled_segments(self) -> int:
        return sum(segment is not None for segment in self.segments)

    def top_color(self) -> Optional[tuple[int, int, int]]:
        for segment in reversed(self.segments):
            if segment is not None:
                return segment
        return None

    def add_segment(self, color: tuple[int, int, int]) -> bool:
        for i in range(SEGMENTS_PER_BOTTLE):
            if self.segments[i] is None:
                self.segments[i] = color
                return True
        return False

    def remove_segment(self) -> Optional[tuple[int, int, int]]:
        for i in range(SEGMENTS_PER_BOTTLE - 1, -1, -1):
            if self.segments[i] is not None:
                color = self.segments[i]
                self.segments[i] = None
                return color
        return None

    def is_solved(self) -> bool:
        if self.is_empty():
            return True

        if not self.is_full():
            return False

        color = self.segments[0]
        return all(segment == color for segment in self.segments)


class MainMenu(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)

        self.engine.add_function_to_live_inspector(
            "Create Random Score",
            self.create_test_score,
            [("username", str)],
            "Create a random score for leaderboard",
        )

        self.setup_ui()

    def create_test_score(self, username: str):
        self.username_box.set_text(username)
        CONFIG["last_user_name"] = username

        CONFIG["leaderboard"].append(
            (
                username,
                random.randint(0, 10000),
                random.randint(0, 360),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

        update_save(self.engine.atlas.get_item("root").path)
        self.reload_leaderboard()
        return False

    def setup_ui(self):
        self.add_ui_element(
            TextLabel(
                self.engine.width // 2,
                100,
                "Dye Sorter",
                76,
                pivot=(0.5, 0),
            )
        )

        play_button = Button(
            self.engine.width // 2,
            200,
            200,
            65,
            "Play",
            50,
            pivot=(0.5, 0),
        )

        play_button.set_on_click(
            lambda: self.engine.set_scene(
                "game",
                TransitionType.SLIDE_LEFT,
                0.6,
            )
        )

        self.add_ui_element(play_button)

        self.username_box = TextBox(
            self.engine.width // 2 + 210,
            200,
            200,
            32,
            str(CONFIG.get("last_user_name", "")),
            28,
            pivot=(0.5, 0),
        )

        self.add_ui_element(self.username_box)

        exit_button = Button(
            self.engine.width // 2,
            375,
            200,
            50,
            "Exit",
            40,
            pivot=(0.5, 0),
        )

        self.add_ui_element(exit_button)

        self.leaderboard_score = ScrollingFrame(
            self.engine.width // 2,
            self.engine.height - 50,
            600,
            300,
            580,
            700,
            pivot=(0.5, 1),
        )

        self.add_ui_element(self.leaderboard_score)

    def on_enter(self, prev):
        self.reload_leaderboard()

    def reload_leaderboard(self):
        self.leaderboard_score.clear_children()

        table = Table(
            self.leaderboard_score.width // 2,
            20,
            self.leaderboard_score.width * 0.8,
            self.leaderboard_score.content_height - 40,
            ["Name", "Score", "Time Played", "Date"],
            header_height=20,
            pivot=(0.5, 0),
        )

        self.leaderboard_score.add_child(table)

        for name, score, time_played, date in CONFIG.get("leaderboard", []):
            table.add_row([name, score, time_played, date])

    def render(self, renderer: OpenGLRenderer):
        renderer.fill_screen(ThemeManager.get_color("background"))


class Game(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)

        self.start_time = time()
        self.moves = 0
        self.times_cleared = 0
        self.last_click = time()

        self.bottle_surface = pygame.image.load(
            self.engine.atlas.get_item("flask").path
        ).convert_alpha()

        self.bottles: List[Bottle] = []
        self.selected_bottle: Optional[Bottle] = None

        self.undo_history: List[List[List[Optional[tuple[int, int, int]]]]] = []

        self.setup_ui()

    def create_bottles(self):
        num_of_bottles = min(
            MAX_BOTTLES,
            1 + (2 * (self.times_cleared + 1)),
        )

        num_of_empty_bottles = 2
        num_of_colored_bottles = max(
            1,
            num_of_bottles - num_of_empty_bottles,
        )

        liquid = []

        for i in range(num_of_colored_bottles):
            color = COLORS[i % len(COLORS)][1]
            liquid.extend([color] * SEGMENTS_PER_BOTTLE)

        random.shuffle(liquid)

        self.bottles = [Bottle(i) for i in range(num_of_bottles)]

        liquid_index = 0

        for bottle in self.bottles[:num_of_colored_bottles]:
            for slot in range(SEGMENTS_PER_BOTTLE):
                bottle.segments[slot] = liquid[liquid_index]
                liquid_index += 1

        self.selected_bottle = None
        self.undo_history.clear()

    def save_state(self):
        state = [bottle.segments.copy() for bottle in self.bottles]

        self.undo_history.append(state)

        if len(self.undo_history) > MAX_UNDO:
            self.undo_history.pop(0)

    def undo(self):
        if not self.undo_history:
            return

        previous_state = self.undo_history.pop()

        for bottle, segments in zip(
            self.bottles,
            previous_state,
        ):
            bottle.segments = segments.copy()

        if self.moves > 0:
            self.moves -= 1

        self.selected_bottle = None

    def humanize_time(self) -> str:
        return humanize_time(time() - self.start_time)

    def setup_ui(self):
        back = self.add_ui_element(
            Button(
                10,
                20,
                100,
                24,
                "Back",
                18,
                icon=Icons.BACK,
            )
        )

        back.set_on_click(
            lambda: self.engine.set_scene(
                "main",
                TransitionType.SLIDE_RIGHT,
                0.6,
            )
        )

        self.undo_button = self.add_ui_element(
            Button(
                125,
                20,
                100,
                24,
                "Undo",
                18,
            )
        )

        self.undo_button.set_on_click(self.undo)

        self.time_counter = self.add_ui_element(
            TextLabel(
                self.engine.width - 20,
                20,
                "Time: 0s",
                24,
                pivot=(1, 0),
            )
        )

        self.moves_counter = self.add_ui_element(
            TextLabel(
                self.engine.width - 20,
                55,
                "Moves: 0",
                24,
                pivot=(1, 0),
            )
        )

        self.undo_counter = self.add_ui_element(
            TextLabel(
                self.engine.width - 20,
                90,
                "Undo: 3",
                24,
                pivot=(1, 0),
            )
        )

    def on_enter(self, previous_scene: str | None = None):
        self.start_time = time()
        self.moves = 0
        self.times_cleared = 0
        self.last_click = time()
        self.undo_history.clear()
        self.selected_bottle = None
        self.create_bottles()

    def update(self, dt: float):
        self.time_counter.set_text(f"Time: {self.humanize_time()}")

        self.moves_counter.set_text(f"Moves: {self.moves}")

        self.undo_counter.set_text(f"Undo: {len(self.undo_history)}/{MAX_UNDO}")

        if (
            self.engine.input_state.mouse_just_pressed
            and time() - self.last_click > 0.1
        ):
            self.handle_click(self.engine.input_state.mouse_pos)
            self.last_click = time()

        if self.engine.input_state.keyPressed(pygame.K_z):
            self.undo()

    def get_bottle_size(self):
        bottle_count = len(self.bottles)

        if bottle_count <= 1:
            progress = 0.0
        else:
            progress = (bottle_count - 1) / (MAX_BOTTLES - 1)

        progress = max(0.0, min(1.0, progress))

        width = int(MAX_BOTTLE_WIDTH - (MAX_BOTTLE_WIDTH - MIN_BOTTLE_WIDTH) * progress)

        height = int(
            MAX_BOTTLE_HEIGHT - (MAX_BOTTLE_HEIGHT - MIN_BOTTLE_HEIGHT) * progress
        )

        return width, height

    def get_bottle_positions(self):
        bottle_count = len(self.bottles)

        if bottle_count == 0:
            return []

        bottle_width, bottle_height = self.get_bottle_size()

        columns = min(MAX_COLUMNS, bottle_count)
        rows = (bottle_count + columns - 1) // columns

        padding_x = bottle_width
        padding_y = bottle_height

        grid_width = (columns - 1) * padding_x + bottle_width

        grid_height = (rows - 1) * padding_y + bottle_height

        center_x = self.engine.width / 2
        center_y = self.engine.height / 2

        start_x = center_x - grid_width / 2
        start_y = center_y - grid_height / 2

        positions = []

        for bottle in self.bottles:
            column = bottle.index % columns
            row = bottle.index // columns

            x = start_x + column * padding_x
            y = start_y + row * padding_y

            positions.append(
                pygame.Rect(
                    int(x),
                    int(y),
                    bottle_width,
                    bottle_height,
                )
            )

        return positions

    def get_liquid_rect(self, bottle_rect: pygame.Rect):
        left = bottle_rect.x + int(bottle_rect.width * LIQUID_LEFT)

        right = bottle_rect.x + int(bottle_rect.width * LIQUID_RIGHT)

        top = bottle_rect.y + int(bottle_rect.height * LIQUID_TOP)

        bottom = bottle_rect.y + int(bottle_rect.height * LIQUID_BOTTOM)

        return pygame.Rect(
            left,
            top,
            right - left,
            bottom - top,
        )

    def draw_bottle_liquid(
        self,
        renderer: OpenGLRenderer,
        bottle: Bottle,
        bottle_rect: pygame.Rect,
    ):
        liquid_rect = self.get_liquid_rect(bottle_rect)

        if liquid_rect.height <= 0:
            return

        segment_height = liquid_rect.height / SEGMENTS_PER_BOTTLE

        for i, color in enumerate(bottle.segments):
            if color is None:
                continue

            y = liquid_rect.bottom - int((i + 1) * segment_height)

            next_y = liquid_rect.bottom - int(i * segment_height)

            renderer.draw_rect(
                liquid_rect.left,
                y,
                liquid_rect.width,
                next_y - y,
                color,
            )

    def get_clicked_bottle(self, position):
        positions = self.get_bottle_positions()

        for bottle, rect in zip(
            self.bottles,
            positions,
        ):
            if rect.collidepoint(position):
                return bottle

        return None

    def can_pour(
        self,
        source: Bottle,
        target: Bottle,
    ) -> bool:
        if source is target:
            return False

        if source.is_empty():
            return False

        if target.is_full():
            return False

        # Different colors are intentionally allowed.
        #
        # This lets the player temporarily stack a color
        # over another color to reorganize the puzzle.

        return True

    def pour(
        self,
        source: Bottle,
        target: Bottle,
    ) -> bool:
        if not self.can_pour(source, target):
            return False

        color = source.top_color()

        if color is None:
            return False

        # Save state BEFORE making the move.
        self.save_state()

        # Move EXACTLY ONE segment.
        moved_color = source.remove_segment()

        if moved_color is None:
            self.undo_history.pop()
            return False

        if not target.add_segment(moved_color):
            source.add_segment(moved_color)
            self.undo_history.pop()
            return False

        self.moves += 1

        return True

    def check_win(self):
        return bool(self.bottles) and all(bottle.is_solved() for bottle in self.bottles)

    def handle_click(self, position):
        clicked = self.get_clicked_bottle(position)

        if clicked is None:
            return

        if self.selected_bottle is None:
            if clicked.is_empty():
                return

            self.selected_bottle = clicked
            return

        if clicked is self.selected_bottle:
            self.selected_bottle = None
            return

        source = self.selected_bottle

        if self.pour(source, clicked):
            self.selected_bottle = None

            if self.check_win():
                self.times_cleared += 1
                self.create_bottles()
        else:
            if not clicked.is_empty():
                self.selected_bottle = clicked
            else:
                self.selected_bottle = None

    def render(self, renderer: OpenGLRenderer):
        renderer.fill_screen(ThemeManager.get_color("background"))

        bottle_width, bottle_height = self.get_bottle_size()

        bottle_surface = pygame.transform.scale(
            self.bottle_surface,
            (bottle_width, bottle_height),
        )

        positions = self.get_bottle_positions()

        for bottle, rect in zip(
            self.bottles,
            positions,
        ):
            if bottle is self.selected_bottle:
                renderer.draw_rect(
                    rect.x - 5,
                    rect.y - 5,
                    rect.width + 10,
                    rect.height + 10,
                    (0, 0, 0, 0),
                    border_color=(100, 50, 65),
                    border_width=3,
                    corner_radius=3,
                )

            self.draw_bottle_liquid(
                renderer,
                bottle,
                rect,
            )

            renderer.blit(
                bottle_surface,
                rect.topleft,
            )


def main():
    global CONFIG

    args = sys.argv[1:]

    parser = ArgumentParser()
    parser.add_argument(
        "-f",
        "--fullscreen",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
    )

    args = parser.parse_args(args)

    engine = LunaEngine(
        "Dye Sorter",
        1280,
        720,
        debug=args.debug,
        fullscreen=args.fullscreen,
    )

    engine.atlas.add_folder(
        "root",
        Path(os.path.abspath(os.path.dirname(__file__))),
    )

    engine.atlas.add_texture(
        "icon",
        engine.atlas.get_item("root").path / "icon.png",
    )

    engine.atlas.add_texture(
        "flask",
        engine.atlas.get_item("root").path / "flask.png",
    )

    CONFIG = create_save(engine.atlas.get_item("root").path)

    engine.set_icon(str(engine.atlas.get_item("icon").path))

    engine.set_global_theme(
        ThemeType.CLOUDS,
        False,
    )

    engine.add_scene("main", MainMenu)
    engine.add_scene("game", Game)

    engine.set_scene("main")
    engine.run()


if __name__ == "__main__":
    main()
