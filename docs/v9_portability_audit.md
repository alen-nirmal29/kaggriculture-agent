# V9 portability audit

Artifact audited: `submission/main.py` (identical to
`submission/final_agent.py`). The generated program contains embedded internal
module names, but resolves them from source held inside the artifact; it never
loads repository modules or local files.

Final size: 64,228 bytes (62.723 KiB, 0.06125 MiB). SHA-256:
`D50E5D697CF1CB7A0656605B20635969643F0B7ABCA78374557B3955C886A325`.

| Check | Result | Evidence |
|---|---|---|
| Repository dependency | PASS | dependency closure is embedded; clean-directory full episode |
| Top-level imports | PASS | only `sys` and `types` |
| Third-party imports | PASS | none required by the agent artifact |
| File reads/writes | PASS | none at agent runtime |
| Network access | PASS | no network modules, URLs, or calls |
| Subprocess/shell | PASS | absent |
| Absolute paths | PASS | absent |
| Environment variables | PASS | absent |
| Secrets/credentials | PASS | no keys, tokens, passwords, `.env`, or user paths |
| Dynamic downloads/models | PASS | absent |
| Debug/evaluation code | PASS | absent |
| Callable | PASS | `agent(obs)` |
| Official layout | PASS | direct root file is named `main.py` |

The upload artifact is generated deterministically by
`evaluation/build_v9_submission.py`. Tournament JSON and documentation are not
included. The exact competition file-size ceiling was not stated in the local
Kaggriculture-specific material, so no limit is invented here.
