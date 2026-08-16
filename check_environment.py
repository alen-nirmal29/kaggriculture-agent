"""Display the locally installed Kaggriculture environment details."""

from pprint import pprint

from kaggle_environments import make


env = make("kaggriculture", debug=True)

print("Kaggriculture loaded successfully.")
print(f"Environment name: {env.name}")
print(f"Built-in agents: {list(env.agents.keys())}")
print("Environment configuration:")
pprint(dict(env.configuration))
print("Action specification:")
pprint(env.specification.action)
