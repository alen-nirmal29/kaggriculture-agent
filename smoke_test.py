"""Run a complete Kaggriculture game using built-in agents."""

from kaggle_environments import make


env = make("kaggriculture", debug=True)
env.run(["starter", "random"])

print("Kaggriculture episode completed successfully.")
for player_index, player in enumerate(env.state):
    print(
        f"Player {player_index}: status={player.status}, reward={player.reward}"
    )

try:
    rendered = env.render(mode="ansi")
except (NotImplementedError, TypeError, ValueError):
    rendered = None

if rendered:
    print("Final render:")
    print(rendered)
else:
    print("Final ANSI/text render is not supported by Kaggriculture.")
