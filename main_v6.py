"""Kaggle-compatible V6 entry point and controlled livestock-policy factory."""
from agent_v6.animals import Mode
from agent_v6.state import GameState
from agent_v6.strategy import SAFE_ACTION, decide
DEFAULT_MAX_HANDS=4; DEFAULT_MANAGED_PLOT_LIMIT=24; DEFAULT_MODE: Mode="COW_ONLY"
DEFAULT_CAPS={"GOOSE":0,"COW":1,"SHEEP":0}; DEFAULT_FERTILIZER=True

def make_agent(mode: Mode=DEFAULT_MODE, caps=None, fertilizer_enabled: bool=DEFAULT_FERTILIZER):
    selected_caps = dict(DEFAULT_CAPS if caps is None else caps)
    def configured_agent(obs):
        try: state=GameState.from_observation(obs)
        except (AttributeError,IndexError,KeyError,TypeError,ValueError): return SAFE_ACTION.copy()
        return decide(state,DEFAULT_MAX_HANDS,DEFAULT_MANAGED_PLOT_LIMIT,mode=mode,caps=selected_caps,fertilizer_enabled=fertilizer_enabled)
    return configured_agent
agent=make_agent()
