import re
from typing import List, Tuple


class RandomMarioAgent:
    """
    A simple rule-based Mario agent that jumps only when an obstacle is close.
    Output format must stay 'Jump Level: <0-6>' to satisfy the environment parser.
    """

    TRACK = "TRACK1"

    def __init__(self):
        self.default_jump = 0

    def act(self, obs):
        text = obs.get("obs_str", "") or ""
        mario_x, _ = self._parse_mario_position(text)
        goombas = self._parse_pairs(text, "Monster Goombas")
        koopas = self._parse_pairs(text, "Monster Koopas")
        warp_pipes = self._parse_triples(text, "Warp Pipes")
        pits = self._parse_pit(text)

        jump_level = self.default_jump

        # Jump over pits aggressively
        if pits:
            pit_dist = min((x1 - mario_x) for x1, _ in pits if x1 > mario_x) if any(x1 > mario_x for x1, _ in pits) else None
            if pit_dist is not None and pit_dist < 70:
                jump_level = max(jump_level, 6)

        # Jump over warp pipes based on height
        for x, _, height in warp_pipes:
            if x > mario_x:
                dist = x - mario_x
                if dist < 60:
                    required = 6 if height and height > 40 else 5
                    jump_level = max(jump_level, required)
                    break

        # Avoid nearby enemies on the ground
        for enemy_list in (goombas, koopas):
            for x, y in enemy_list:
                if x > mario_x and (x - mario_x) < 40 and y >= 30:
                    jump_level = max(jump_level, 4)
                    break

        return f"Jump Level: {jump_level}"

    # Parsing helpers -----------------------------------------------------
    def _parse_mario_position(self, text: str) -> Tuple[int, int]:
        match = re.search(r"Position of Mario:\s*\(([-\d]+),\s*([-\d]+)\)", text)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    def _parse_pairs(self, text: str, key: str) -> List[Tuple[int, int]]:
        line = self._find_line(text, key)
        if not line or "None" in line:
            return []
        return [(int(a), int(b)) for a, b in re.findall(r"\(([-\d]+),\s*([-\d]+)\)", line)]

    def _parse_triples(self, text: str, key: str) -> List[Tuple[int, int, int]]:
        line = self._find_line(text, key)
        if not line or "None" in line:
            return []
        return [(int(a), int(b), int(c)) for a, b, c in re.findall(r"\(([-\d]+),\s*([-\d]+),\s*([-\d]+)\)", line)]

    def _parse_pit(self, text: str) -> List[Tuple[int, int]]:
        # Returns list of (start_x, end_x)
        match = re.search(r"Pit:\s*start at\s*\(([-\d]+),\s*([-\d]+)\),\s*end at\s*\(([-\d]+),\s*([-\d]+)\)", text)
        if match:
            return [(int(match.group(1)), int(match.group(3)))]
        return []

    def _find_line(self, text: str, key: str) -> str:
        for line in text.splitlines():
            if key in line:
                return line
        return ""
