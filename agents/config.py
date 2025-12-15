from agents.random_mario import RandomMarioAgent
from agents.openai_mario import OpenAIMarioAgent

from agents.random_pokemon import RandomPokemonAgent
from agents.openai_pokemon import OpenAIPokemonAgent

from agents.random_twenty_fourty_eight import RandomTwentyFourtyEightAgent
from agents.openai_twenty_fourty_eight import OpenAITwentyFourtyEightAgent

from agents.random_starcraft import RandomStarCraftAgent
from agents.openai_starcraft import OpenAIStarCraftAgent

# Toggle between OpenAI agents and lightweight heuristics
PokemonAgent = OpenAIPokemonAgent  # or RandomPokemonAgent
TwentyFourtyEightAgent = OpenAITwentyFourtyEightAgent  # or RandomTwentyFourtyEightAgent
SuperMarioAgent = OpenAIMarioAgent  # or RandomMarioAgent
StarCraftAgent = OpenAIStarCraftAgent  # or RandomStarCraftAgent
