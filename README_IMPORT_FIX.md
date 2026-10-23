# Amar Passport — CrewAI ImportError diagnostic patch

This patch prints the actual traceback rather than just `ImportError` when CrewAI live execution fails. It makes **no change** to `crew_pipeline.py`, deterministic eligibility rules, fees, task context, or `.env`.

## Apply in VS Code (PowerShell)

1. Extract this ZIP and copy its `main.py` and `scripts/diagnose_crewai.py` into `D:\Amar_Passport_CrewAI`, preserving the folder structure. Back up your current `main.py` if you have customized it. Do not replace `.env`, `data/` or existing CrewAI agents.
2. Run:

```powershell
cd D:\Amar_Passport_CrewAI
.\.venv\Scripts\Activate.ps1
python scripts\diagnose_crewai.py
```

3. If all four import stages PASS, run:

```powershell
python main.py --live --offline --no-save
```

If CrewAI still fails, the Terminal now prints the full traceback between `CREWAI LIVE ERROR TRACEBACK` and `END CREWAI TRACEBACK`. Copy the **last error lines**, but never include `.env` or your API key.

## Typical meanings

- `cannot import name 'LLM' from 'crewai'`: installed CrewAI version may not expose the class. Check that `.venv` is active and `python -m pip show crewai`; align dependencies using `python -m pip install --upgrade "crewai[litellm]>=1.10,<2"` if applicable.
- `No module named 'litellm'`: install LiteLLM support in the same virtualenv: `python -m pip install --upgrade "crewai[litellm]>=1.10,<2"`.
- `cannot import name 'tool'`: confirm the source uses `from crewai.tools import tool`, not `from crewai_tools import tool`.
- Errors deeper inside a dependency: **use the exact traceback**, not one-size-fits-all package upgrades.

For an operational three-agent assignment, `--demo` is not a substitute for a successful `--live` run.
