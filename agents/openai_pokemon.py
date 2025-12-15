import re
import openai

SYSTEM_PROMPT = """
You are a concise Pokémon Red navigation assistant. Choose valid Game Boy button presses to progress the story efficiently (reach early-game milestones).

Allowed buttons (lowercase): up, down, left, right, a, b, start, select.
Return 1–3 buttons separated by spaces, no explanations. Avoid invalid text.

Guidelines:
- Title/Dialog: press 'a' to advance. If a selection box is visible, move cursor then 'a'.
- Field movement: move toward objectives or warp points; explore '?' tiles; avoid walls ('X', 'Cut', barriers).
- Battles: prefer 'a' to confirm default moves; if clearly losing, press 'run_away' is NOT a valid button—use 'b' then 'a' to try to flee.
"""

USER_PROMPT = """
### Current Observation
{obs_text}

### Last Action
{last_action}

Remember: output only space-separated buttons from [up, down, left, right, a, b, start, select]. Avoid other text.
"""

ALLOWED_ACTIONS = ["up", "down", "left", "right", "a", "b", "start", "select"]
MODEL = "openai/gpt-4o-mini"


class OpenAIPokemonAgent:
    TRACK = "TRACK1"

    def __init__(self):
        self.client = openai.OpenAI()
        self.last_action = "a"

    def act(self, obs):
        obs_text = obs.get("obs_str", "") or ""

        response = self.client.responses.create(
            model=MODEL,
            input=USER_PROMPT.format(
                obs_text=obs_text,
                last_action=self.last_action
            ),
            instructions=SYSTEM_PROMPT,
            reasoning={"effort": "low"}
        )

        output = response.output_text.strip()
        actions = self._parse_actions(output)
        self.last_action = actions
        return actions

    # Helpers -------------------------------------------------------------
    def _parse_actions(self, text: str) -> str:
        tokens = re.findall(r"\b(up|down|left|right|a|b|start|select)\b", text, flags=re.IGNORECASE)
        if not tokens:
            return "a"
        # Deduplicate while preserving order, cap at 3
        seen = set()
        filtered = []
        for t in tokens:
            key = t.lower()
            if key in ALLOWED_ACTIONS and key not in seen:
                filtered.append(key)
                seen.add(key)
            if len(filtered) >= 3:
                break
        return " ".join(filtered) if filtered else "a"
