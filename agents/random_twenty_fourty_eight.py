import copy
import re
from typing import List, Tuple

from evaluation_utils.mcp_game_servers.twenty_fourty_eight.game.logic import move


class RandomTwentyFourtyEightAgent:
    """
    Heuristic 2048 agent:
    - Parses the board from obs_str.
    - Filters out invalid moves (no board change).
    - Scores valid moves using a simple heuristic to keep the board stable.
    """

    TRACK = "TRACK1"

    def __init__(self):
        self.fallback_order = ["left", "up", "right", "down"]

    def act(self, obs):
        obs_text = obs.get("obs_str", "") or ""
        board = self._parse_board(obs_text)

        # If parsing fails, keep a deterministic fallback to avoid invalid output
        if not board:
            return self.fallback_order[0]

        candidates = []
        for direction in ["left", "up", "right", "down"]:
            new_board, merge_score = move(direction, copy.deepcopy(board))
            if new_board != board:
                score = self._score_board(new_board, merge_score)
                candidates.append((score, direction))

        if not candidates:
            return self.fallback_order[0]

        # Pick best-scoring direction
        candidates.sort(reverse=True)
        return candidates[0][1]

    # Helpers -------------------------------------------------------------
    def _parse_board(self, text: str) -> List[List[int]] | None:
        board: List[List[int]] = []
        for line in text.splitlines():
            if not line.strip().startswith("["):
                continue
            row = [int(x) for x in re.findall(r"-?\d+", line)]
            if row:
                board.append(row)
        if len(board) == 4 and all(len(r) == 4 for r in board):
            return board
        return None

    def _score_board(self, board: List[List[int]], merge_score: int) -> float:
        empty_cells = sum(cell == 0 for row in board for cell in row)
        max_tile = max(cell for row in board for cell in row)
        monotonic = self._monotonic_score(board)
        return 2.5 * empty_cells + 1.5 * monotonic + 0.5 * (merge_score / 10) + 0.3 * max_tile

    def _monotonic_score(self, board: List[List[int]]) -> float:
        # Reward rows that decrease left->right and columns that decrease top->bottom
        row_score = 0
        for row in board:
            for a, b in zip(row, row[1:]):
                row_score += 1 if a >= b else -1
        col_score = 0
        for c in range(4):
            for r in range(3):
                col_score += 1 if board[r][c] >= board[r + 1][c] else -1
        return row_score + col_score
