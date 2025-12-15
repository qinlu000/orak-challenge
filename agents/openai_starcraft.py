import openai
import re
from typing import List

SYSTEM_PROMPT = """
You are a Protoss macro strategist for StarCraft II.
Given structured summaries, output exactly N actions formatted as `i: ACTION`, using ONLY the provided valid actions.
If unsure, fill remaining slots with `EMPTY ACTION`.

Macro priorities:
- Avoid supply block (build PYLON if supply left < 5).
- Continuous probes until strong economy; add assimilators, gateways, and tech.
- Mix early army (ZEALOT/STALKER); use MULTI-ATTACK when supply is decent.
- If information is missing, return safe macro (PROBE/ PYLON / EMPTY ACTION).
"""

USER_PROMPT = """
### Current Game State
{obs_text}

### Valid Actions
{valid_actions}

### Last Actions
{last_action}

Return exactly {num_actions} lines, each `i: ACTION`, i from 0.
"""

MODEL = "openai/gpt-4o-mini"

# Fallback action space (matches env docs) used if game_info lacks action_dict
DEFAULT_ACTIONS = [
    'TRAIN PROBE', 'TRAIN ZEALOT', 'TRAIN ADEPT', 'TRAIN STALKER', 'TRAIN SENTRY',
    'TRAIN HIGHTEMPLAR', 'TRAIN DARKTEMPLAR', 'TRAIN VOIDRAY', 'TRAIN CARRIER', 'TRAIN TEMPEST',
    'TRAIN ORACLE', 'TRAIN PHOENIX', 'TRAIN MOTHERSHIP', 'TRAIN OBSERVER', 'TRAIN IMMORTAL',
    'TRAIN WARPPRISM', 'TRAIN COLOSSUS', 'TRAIN DISRUPTOR', 'MORPH ARCHON',
    'BUILD PYLON', 'BUILD ASSIMILATOR', 'BUILD NEXUS', 'BUILD GATEWAY', 'BUILD CYBERNETICSCORE',
    'BUILD FORGE', 'BUILD TWILIGHTCOUNCIL', 'BUILD ROBOTICSFACILITY', 'BUILD STARGATE',
    'BUILD TEMPLARARCHIVE', 'BUILD DARKSHRINE', 'BUILD ROBOTICSBAY', 'BUILD FLEETBEACON',
    'BUILD PHOTONCANNON', 'BUILD SHIELDBATTERY',
    'RESEARCH WARPGATERESEARCH', 'RESEARCH PROTOSSAIRWEAPONSLEVEL1', 'RESEARCH PROTOSSAIRWEAPONSLEVEL2',
    'RESEARCH PROTOSSAIRWEAPONSLEVEL3', 'RESEARCH PROTOSSAIRARMORSLEVEL1', 'RESEARCH PROTOSSAIRARMORSLEVEL2',
    'RESEARCH PROTOSSAIRARMORSLEVEL3', 'RESEARCH ADEPTPIERCINGATTACK', 'RESEARCH BLINKTECH',
    'RESEARCH CHARGE', 'RESEARCH PROTOSSGROUNDWEAPONSLEVEL1', 'RESEARCH PROTOSSGROUNDWEAPONSLEVEL2',
    'RESEARCH PROTOSSGROUNDWEAPONSLEVEL3', 'RESEARCH PROTOSSGROUNDARMORSLEVEL1',
    'RESEARCH PROTOSSGROUNDARMORSLEVEL2', 'RESEARCH PROTOSSGROUNDARMORSLEVEL3',
    'RESEARCH PROTOSSSHIELDSLEVEL1', 'RESEARCH PROTOSSSHIELDSLEVEL2', 'RESEARCH PROTOSSSHIELDSLEVEL3',
    'RESEARCH EXTENDEDTHERMALLANCE', 'RESEARCH GRAVITICDRIVE', 'RESEARCH OBSERVERGRAVITICBOOSTER',
    'RESEARCH PSISTORMTECH', 'RESEARCH VOIDRAYSPEEDUPGRADE', 'RESEARCH PHOENIXRANGEUPGRADE',
    'RESEARCH TEMPESTGROUNDATTACKUPGRADE', 'SCOUTING PROBE', 'SCOUTING OBSERVER', 'SCOUTING ZEALOT',
    'SCOUTING PHOENIX', 'MULTI-ATTACK', 'MULTI-RETREAT',
    'CHRONOBOOST NEXUS', 'CHRONOBOOST CYBERNETICSCORE', 'CHRONOBOOST TWILIGHTCOUNCIL',
    'CHRONOBOOST STARGATE', 'CHRONOBOOST FORGE', 'EMPTY ACTION'
]


class OpenAIStarCraftAgent:
    TRACK = "TRACK1"

    def __init__(self):
        self.client = openai.OpenAI()
        self.last_action = "N/A"

    def act(self, obs):
        game_info = obs.get("game_info", {}) or {}
        current_state = obs.get("obs_str", "") or ""
        if not current_state:
            return self._format_actions(["EMPTY ACTION"])

        num_actions = max(1, int(game_info.get("num_actions", 5)))
        valid_actions = list(game_info.get("action_dict", {}).keys()) or DEFAULT_ACTIONS

        response = self.client.responses.create(
            model=MODEL,
            input=USER_PROMPT.format(
                obs_text=current_state,
                valid_actions="\n".join(valid_actions),
                last_action=self.last_action,
                num_actions=num_actions,
            ),
            instructions=SYSTEM_PROMPT,
            reasoning={"effort": "low"},
        )

        output = response.output_text.strip()
        parsed = self._parse_actions(output, valid_actions, num_actions)
        self.last_action = parsed
        return parsed

    # Helpers -------------------------------------------------------------
    def _parse_actions(self, text: str, valid_actions: List[str], num_actions: int) -> str:
        valid_set = {a.upper() for a in valid_actions}
        candidates: List[str] = []

        # Prefer explicit "i: ACTION" lines
        for line in text.splitlines():
            match = re.search(r"\d+\s*:\s*([A-Za-z _]+)", line)
            if match:
                action = match.group(1).strip().upper()
                if action in valid_set:
                    candidates.append(action)

        # Fallback: grab bare action tokens
        if not candidates:
            tokens = re.findall(r"[A-Za-z][A-Za-z _]+", text)
            for tok in tokens:
                action = tok.strip().upper()
                if action in valid_set:
                    candidates.append(action)

        # Trim or pad
        actions = candidates[:num_actions]
        while len(actions) < num_actions:
            actions.append("EMPTY ACTION")

        return self._format_actions(actions)

    def _format_actions(self, actions: List[str]) -> str:
        return "\n".join(f"{i}: {action}" for i, action in enumerate(actions))
