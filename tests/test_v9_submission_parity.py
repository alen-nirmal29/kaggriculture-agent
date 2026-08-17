"""Full-episode parity and clean-room checks for the exact upload artifact."""
from __future__ import annotations

import ast
import importlib.util
import inspect
from pathlib import Path
import shutil

import pytest
from kaggle_environments import make

from main_v8 import make_agent as make_v8
from main_v9 import make_agent as make_v9

ARTIFACT = Path("submission/main.py").resolve()


def load_artifact(name):
    spec = importlib.util.spec_from_file_location(name, ARTIFACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


@pytest.mark.parametrize("seed,position", [(1590100, 0), (1590101, 1)])
def test_complete_episode_exact_parity(seed, position):
    packaged, standalone = make_v9(), load_artifact(f"standalone_{seed}")
    mismatches = []

    def parity(obs, configuration=None):
        expected = packaged(obs)
        actual = standalone(obs)
        if actual != expected:
            mismatches.append((obs.step, expected, actual))
        return actual

    agents = [make_v8(), make_v8()]
    agents[position] = parity
    env = make("kaggriculture", configuration={"seed": seed}, debug=True)
    env.run(agents)
    assert not mismatches
    assert len(env.steps) == 720 and all(x.status == "DONE" for x in env.state)


def test_clean_directory_import_and_full_self_play(tmp_path, monkeypatch):
    clean = tmp_path / "main.py"
    shutil.copyfile(ARTIFACT, clean)
    monkeypatch.chdir(tmp_path)

    def load(name):
        spec = importlib.util.spec_from_file_location(name, clean)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.agent

    env = make("kaggriculture", configuration={"seed": 1590200}, debug=True)
    env.run([load("clean_a"), load("clean_b")])
    assert len(env.steps) == 720 and all(x.status == "DONE" for x in env.state)


def test_exact_callable_signature():
    assert str(inspect.signature(load_artifact("signature_check"))) == "(obs)"


def test_official_single_file_layout():
    assert ARTIFACT.name == "main.py" and ARTIFACT.parent.name == "submission"


def test_top_level_imports_are_standard_library_only():
    tree = ast.parse(ARTIFACT.read_text(encoding="utf-8"))
    names = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append((node.module or "").split(".")[0])
    assert set(names) <= {"sys", "types"}


@pytest.mark.parametrize("needle", [
    "C:\\Users\\", "http://", "https://", "subprocess", "socket",
    "requests", "API_KEY", "KAGGLE_KEY", ".env",
])
def test_no_secret_network_or_host_dependency(needle):
    assert needle not in ARTIFACT.read_text(encoding="utf-8")
