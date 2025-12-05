import openai
import re

SYSTEM_PROMPT = """
You are the best and most aggressive Street Fighter III: 3rd Strike player in the world. Your goal is to defeat your opponent as quickly and efficiently as possible using optimal strategies.
Analyze the current game state, the distance between your character's and the opponent's character, and remaining health. Then, determine the best next actions to execute, ensuring you maintain offensive pressure.

### Strategy Guidelines ###
1. You can only output at most TWO actions in the output.
2. Choose the appropriate move based on the distance from the opponent and the current situation.
3. Utilize defensive or evasive techniques to minimize incoming damage.
4. Combine normal attacks and special moves to control space and apply pressure on the opponent.
5. If the super bar gauge is full, use Super Action to maximize damage.
6. If the distance is close, use close-range attacks to reduce the opponent's health.
7. If the distance is far, you can either approach the opponent or use long-range attacks to reduce their health.
8. Strategically choose the best action based on current game state.
9. If your opponent get stunned, try powerful moves to maximize damage.
10. Super attack is a special move that can be used when the super count is non-zero.

### Valid action set ###
{skill_library}

### Decision Output Format ###
Analyze the provided game state and determine the **next actions** to take next.

Return your decision in the following exact format:
### Reasoning
<a detailed summary of why this action was chosen>
### Actions
<at most two consecutive actions in the valid action set>

Ensure that:
- The '### Reasoning' field provides a clear explanation of why the action is the best choice.
- The '### Actions' field contains only at most two of the valid actions.
"""

USER_PROMPT = """
### Target task
{task_description}

### Previous state:
{prev_state_str}

### Last executed action:
{action}

### Current state:
{cur_state_str}

Based on the above information, analyze the current situation for what you should do for the next step. Then, you should output the exact actions you want to execute in the game.
You should only respond with actions from the valid action set.
You should only respond in the format described below, and you should not output comments or other information.
Provide your response in the strict format:
### Reasoning
- ...
- ...
- ...
### Actions
- ...
- ...
"""

MODEL = "gpt-5-nano"

class OpenAIStreetFighterAgent:
    def __init__(self):
        self.client = openai.OpenAI()
        self.last_action = "No action yet"
        self.prev_state_str = "N/A"
    
    def act(self, obs):
        game_info = obs.get("game_info", {})
        cur_state_str = obs.get("obs_str", "")
        
        task_description = game_info.get("task_description", "Defeat your opponent")
        skill_library = game_info.get("skill_library", "No skill library provided")
        
        formatted_system_prompt = SYSTEM_PROMPT.format(
            skill_library=skill_library
        )
        
        formatted_user_prompt = USER_PROMPT.format(
            task_description=task_description,
            prev_state_str=self.prev_state_str,
            action=self.last_action,
            cur_state_str=cur_state_str
        )

        response = self.client.responses.create(
            model=MODEL,
            input=formatted_user_prompt,
            instructions=formatted_system_prompt,
            reasoning={"effort": "low"}
        )
        
        output = response.output_text.strip()
        actions = self._parse_actions(output)

        self.prev_state_str = cur_state_str
        self.last_action = actions

        return actions
    
    def _parse_actions(self, output):
        """
        Return the full string after ### Actions.
        """
        actions_match = re.search(r"### Actions\s*\n(.+)", output, re.IGNORECASE | re.DOTALL)
        if actions_match:
            actions_section = actions_match.group(1).strip()
            return actions_section
        return ""