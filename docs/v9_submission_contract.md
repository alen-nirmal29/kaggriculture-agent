# V9 submission contract

Source of truth: the installed `kaggle-environments==1.32.7` Kaggriculture
`README.md`, `AGENTS.md`, environment schema, and implementation.

- Upload a Python file named `main.py` at the archive root, or submit that file
  directly. It must expose `agent(obs)`.
- A notebook is not required. The official CLI accepts
  `kaggle competitions submit kaggriculture -f main.py -m "message"`.
- Competition rules must first be accepted through **Join Competition**.
- Each action must be a dictionary with `farmer`, `hands`, and `market` keys.
- The action timeout is one second. A match has 720 turns.
- Reward is final banked money; higher reward wins and equal rewards draw.
- The uploaded program cannot depend on this repository. The frozen artifact
  therefore embeds its dependency closure and uses only Python's standard
  library. `kaggle-environments` is needed by the evaluator, not by `agent`.

The exact upload object is `submission/main.py`. `submission/final_agent.py` is
an identical, descriptive copy. No archive or auxiliary file is required.
