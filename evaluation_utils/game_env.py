import logging
import json
from fastmcp.client import Client
import backoff

from evaluation_utils.commons import logger, log_handler

class GameEnv:
    def __init__(self, mcp_url: str):
        self.client = Client(mcp_url, log_handler=log_handler)
    
    async def wait_for_ping(self):
        await self.client.ping()
    
    async def _call_tool(self, tool_name: str, *args, **kwargs):
        logging.getLogger(__name__).debug("Calling tool %s with args=%s kwargs=%s", tool_name, args, kwargs)
        result = await self.client.call_tool(tool_name, *args, **kwargs)
        logging.getLogger(__name__).debug("Tool %s result: %s", tool_name, result)
        return json.loads(result.structured_content["result"])

    async def load_obs(self):
        return await self._call_tool("load-obs")
    
    async def dispatch_final_action(self, action: str):
        return await self._call_tool("dispatch-final-action", {"action_str": action})
