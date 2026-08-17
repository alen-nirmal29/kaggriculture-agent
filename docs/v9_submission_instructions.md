# V9 Kaggle submission instructions

Upload exactly [submission/main.py](../submission/main.py). Do not upload
`final_agent.py`, the repository, or a directory. No notebook or archive
extraction is required.

1. Open the Kaggriculture competition page and choose **Join Competition** to
   accept the rules if this account has not already done so. The exact current
   Kaggle button placement is **VERIFY IN KAGGLE UI**.
2. Submit the direct file through the competition's submission UI, selecting
   `submission/main.py`; or use the authenticated CLI from `submission/`:
   `..\.venv\Scripts\python.exe -m kaggle competitions submit kaggriculture -f main.py -m "V9 final"`.
3. Confirm Kaggle accepts the file and runs `agent(obs)` without import,
   invalid-action, or timeout errors. A successful run should reach 720 turns.
4. If validation fails, inspect the submission's Kaggle log/error panel. Its
   exact current UI location is **VERIFY IN KAGGLE UI**. Verify that the chosen
   file is named `main.py` before investigating strategy behavior.

The locally installed Kaggriculture documentation explicitly supports direct
single-file submission. Rules acceptance is required. A notebook is not.
