import sys
import os
import json
from datetime import datetime
from typing import Tuple
import omegaconf
import logging
import time
import base64
from io import BytesIO
import traceback

from mcp.server.fastmcp import FastMCP
from mcp_game_servers.utils.module_creator import EnvCreator

from evaluation_utils.commons import GAME_DATA_DIR, GAME_RESULTS_PATH, setup_logging, MAX_STEPS, MAX_EPISODES

logger = logging.getLogger(__name__)

GAME_ID = os.getenv("GAME_ID", "")

if sys.platform == 'win32':
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

def set_log_path(cfg, expand_log_path: bool = True):
    if expand_log_path:
        log_path = os.path.join(
            cfg.log_path,
            cfg.env_name,
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        cfg.env.log_path = log_path
        os.makedirs(log_path, exist_ok=True)
    
    setup_logging()

class MCPGameServer:

    def __init__(self, mcp_server: FastMCP, config_path: str, expand_log_path: bool = True):
        self.cfg = self.create_config(config_path, expand_log_path)
        logger.info(f"config_path: {config_path}")
        self.mcp = mcp_server
        self.register_tools()

        # set env
        self.env = EnvCreator(self.cfg).create()

        # set temp var
        self.obs = None
        self.first_loading = True

        self._score = 0
        self._start_time = None
        self._end_time = None
        self._steps_times = []
        self._episodes = 0
        self._max_steps = MAX_STEPS[GAME_ID]

    def create_config(self, config_path: str, expand_log_path: bool):
        cfg = omegaconf.OmegaConf.load(config_path)
        set_log_path(cfg, expand_log_path)
        return cfg

    def image2str(self, image):
        buffered = BytesIO()
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def load_current_obs(self) -> Tuple[str, dict]:
        if self.first_loading:
            self.obs = self.env.initial_obs()
            self.first_loading = False
        obs_str, obs_image = self.obs.to_text(), getattr(self.obs, 'image', None)
        game_info = self.env.get_game_info()

        # encode image to base64
        if obs_image is not None:
            obs_image_str = self.image2str(obs_image)
        else:
            obs_image_str = ""
        return obs_str, obs_image_str, game_info
    
    def log_game_results(self):
        self._end_time = time.time()
        with open(GAME_RESULTS_PATH, "w") as fp:
            json.dump({
                "score": self._score,
                "avg_score": self._score / (self._episodes + 1),
                "start_time": self._start_time,
                "end_time": self._end_time,
                "steps_times": self._steps_times,
                "game_info": self.env.get_game_info()
            }, fp)

    def reset_env(self):
        try:
            self.env.reset()
        except Exception as e:
            # recreate game env for new episode
            self.env = EnvCreator(self.cfg).create()
            self.first_loading = True

    def dispatch_action_and_get_score(self, action_str: str) -> Tuple[int, bool]:
        score = -1
        action = self.env.text2action(action_str)
        logger.info(f"executing actions: {action}")
        try:
            self.obs, reward, terminated, truncated, info = self.env.step(action)
        except Exception as e:
            logger.error(traceback.format_exc())
            raise e
        score, done = self.env.evaluate(self.obs)
        # retries = 0
        # while score is None and retries < 30:
        #     self.obs, reward, terminated, truncated, info = self.env.step(action)
        #     score, done = self.env.evaluate(self.obs)
        #     retries += 1
        #     time.sleep(10)
        # if score is None:
        #     raise Exception("Failed to get score, is the game running?")
        is_finished = terminated or truncated or done
        logger.info(f"score: {score}, is_finished: {is_finished}")
        self._score += score
        if len(self._steps_times) >= self._max_steps:
            is_finished = True
            self._episodes += 1
        
        if self._episodes < MAX_EPISODES:
            self.reset_env()
        
        return score, is_finished

    def register_tools(self):
        @self.mcp.tool(name="load-obs", description="Load observation and game info from the server.")
        def load_obs() -> str:
            if not self._start_time:
                self._start_time = time.time()
            else:
                self._steps_times.append(time.time())
            
            try:
                obs_str, obs_image_str, game_info = self.load_current_obs()
            except Exception as e:
                logger.error(traceback.format_exc())
                raise e
            logger.info(f"load_obs result: {obs_str}, \n{game_info}")
            return json.dumps({
                "obs_str": obs_str,
                "obs_image_str": obs_image_str,
                "game_info": game_info
            })

        @self.mcp.tool(name="send-action-set", description="Send a action set to the server.")
        def send_action_set(action_set: list) -> str:
            self.env.send_action_set(action_set)
            return "Action set sent"
        
        @self.mcp.tool(name='get-current-state', description='Get the current state of the game')
        def get_current_state() -> str:
            return json.dumps({
                "current_state": self.env._receive_state()
            })

        @self.mcp.tool(name="dispatch-final-action", description="Dispatch a client final action to the server and return score and termination flag")
        def dispatch_final_action(action_str: str) -> str:
            try:
                score, is_finished = self.dispatch_action_and_get_score(action_str)
            except Exception as e:
                logger.error(traceback.format_exc())
                raise e
            logger.info(f"dispatch_final_action result: {score}, {is_finished}")
            if is_finished:
                self.log_game_results()
            return json.dumps({
                "score": score,
                "avg_score": self._score / (self._episodes + 1),
                "is_finished": is_finished
            })
        
        @self.mcp.tool(name="get-game-config", description="Get the game config")
        def get_game_config() -> str:
            return json.dumps({
                "game_id": GAME_ID,
                "max_steps": self._max_steps,
                "max_episodes": MAX_EPISODES
            })

    async def run(self):
        await self.mcp.run_streamable_http_async()
