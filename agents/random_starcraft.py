import re
from typing import List


class RandomStarCraftAgent:
    """
    A lightweight macro-focused Protoss script:
    - Keeps making probes until ~32 workers.
    - Adds pylons before supply block.
    - Builds assimilators/gateways, then sprinkles basic army and occasional attack calls.
    Always returns exactly num_actions lines: 'idx: ACTION'.
    """

    TRACK = "TRACK1"

    def __init__(self):
        self.step_count = 0

    def act(self, obs):
        self.step_count += 1
        text = obs.get("obs_str", "") or ""
        game_info = obs.get("game_info", {}) or {}
        num_actions = max(1, game_info.get("num_actions", 5))

        supply_left = self._extract_int(r"Supply left:\s*(\d+)", text)
        worker_supply = self._extract_int(r"Worker supply:\s*(\d+)", text)
        army_supply = self._extract_int(r"Army supply:\s*(\d+)", text)
        nexus_count = self._extract_int(r"Nexus count:\s*(\d+)", text) or 1
        pylon_count = self._extract_int(r"Pylon count:\s*(\d+)", text) or 0
        gas_buildings = self._extract_int(r"Gas buildings count:\s*(\d+)", text) or 0
        gateway_count = self._extract_int(r"Gateway count:\s*(\d+)", text) or 0

        actions: List[str] = []

        # Avoid supply block
        if supply_left is not None and supply_left < 5:
            actions.append("BUILD PYLON")

        # Maintain worker production up to ~32 supply
        if worker_supply is None or worker_supply < 32:
            actions.append("TRAIN PROBE")

        # Early gas + gateways
        if gas_buildings < min(2, nexus_count * 2) and worker_supply and worker_supply > 12:
            actions.append("BUILD ASSIMILATOR")

        if gateway_count < 2 and pylon_count > 0:
            actions.append("BUILD GATEWAY")

        # Basic army
        if gateway_count >= 1:
            actions.append("TRAIN ZEALOT")

        # Small poke once we have some army
        if army_supply and army_supply >= 20:
            actions.append("MULTI-ATTACK")

        # Fill remaining with safe no-ops
        while len(actions) < num_actions:
            actions.append("EMPTY ACTION")
        actions = actions[:num_actions]

        return "\n".join(f"{i}: {action}" for i, action in enumerate(actions))

    def _extract_int(self, pattern: str, text: str) -> int | None:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None
