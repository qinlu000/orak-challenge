from agents.random_mario import RandomMarioAgent
from agents.openai_mario import OpenAIMarioAgent

from agents.random_pokemon import RandomPokemonAgent

from agents.random_twenty_fourty_eight import RandomTwentyFourtyEightAgent
from agents.openai_twenty_fourty_eight import OpenAITwentyFourtyEightAgent

from agents.random_starcraft import RandomStarCraftAgent
from agents.openai_starcraft import OpenAIStarCraftAgent

from agents.random_street_fighter import RandomStreetFighterAgent
from agents.openai_street_fighter import OpenAIStreetFighterAgent

PokemonAgent = RandomPokemonAgent

TwentyFourtyEightAgent = OpenAITwentyFourtyEightAgent
# TwentyFourtyEightAgent = RandomTwentyFourtyEightAgent

SuperMarioAgent = OpenAIMarioAgent
# SuperMarioAgent = RandomMarioAgent

StarCraftAgent = OpenAIStarCraftAgent
# StarCraftAgent = RandomStarCraftAgent

StreetFighterAgent = OpenAIStreetFighterAgent
# StreetFighterAgent = RandomStreetFighterAgent
