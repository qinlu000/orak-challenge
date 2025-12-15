import re
from typing import Tuple


class RandomPokemonAgent:
    """
    Minimal auto-progress agent:
    - Spam 'a' during title, dialog, or battles.
    - On field, walk toward the nearest warp point if present; otherwise wander right/down.
    Returned string can contain multiple button presses separated by spaces; the env will execute them sequentially.
    """

    TRACK = "TRACK1"

    def __init__(self):
        self.default_wander = ["right", "down", "left", "up"]
        self.wander_idx = 0

    def act(self, obs):
        text = obs.get("obs_str", "") or ""
        state = self._extract_state(text)

        if state in ("Title", "Dialog"):
            return "a"
        if "Battle" in state:
            return "a a"  # confirm menus quickly

        pos = self._parse_position(text)
        warp = self._parse_warp_point(text)
        if pos and warp:
            move = self._step_toward(pos, warp)
            return move

        # Fallback wander
        move = self.default_wander[self.wander_idx % len(self.default_wander)]
        self.wander_idx += 1
        return move

    # Helpers -------------------------------------------------------------
    def _extract_state(self, text: str) -> str:
        match = re.search(r"State:\s*([A-Za-z]+)", text)
        return match.group(1) if match else "Field"

    def _parse_position(self, text: str) -> Tuple[int, int] | None:
        match = re.search(r"Your position \(x, y\):\s*\(([-\d]+),\s*([-\d]+)\)", text)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

    def _parse_warp_point(self, text: str) -> Tuple[int, int] | None:
        match = re.search(r"WarpPoint", text)
        if not match:
            return None
        # Try to find coordinates preceding WarpPoint in Notable Objects lines
        coords = re.findall(r"\(\s*([-\d]+),\s*([-\d]+)\)\s*WarpPoint", text)
        if coords:
            x, y = coords[0]
            return int(x), int(y)
        return None

    def _step_toward(self, pos: Tuple[int, int], target: Tuple[int, int]) -> str:
        px, py = pos
        tx, ty = target
        if abs(px - tx) > abs(py - ty):
            return "right" if tx > px else "left"
        return "down" if ty > py else "up"
