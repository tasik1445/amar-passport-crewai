# Amar Passport — LiteLLM / MCP `CacheableResult` fix

The log shows `litellm.completion()` attempting `from mcp.types import CacheableResult` and failing. This is not a Groq authentication error and not a passport policy error. Recent LiteLLM 1.106.x tool-calling paths can trigger this when `mcp` 1.x is installed.

## Windows VS Code / PowerShell

1. Extract this ZIP into `D:\Amar_Passport_CrewAI`, replacing **only** `requirements.txt` and adding `scripts/check_dependencies.py`. Do not replace `.env`, `main.py`, `crew_pipeline.py`, passport policies, or databases.
2. Activate the virtual environment:

```powershell
cd D:\Amar_Passport_CrewAI
.\.venv\Scripts\Activate.ps1
python -m pip install "litellm==1.105.1"
python -m pip check
python scripts/check_dependencies.py
```

3. If dependencies check passes, run:

```powershell
python -m pytest -q
python main.py --live --offline --no-save
```

4. If `pip check` reports CrewAI specifically requires a different LiteLLM version, or the first error remains, share version info and the first traceback error without sharing API keys:

```powershell
python -m pip show crewai litellm mcp
python -m pip check
```

### Important
- Do **not** blindly upgrade MCP to v2: the current Python MCP SDK v2 has breaking changes relative to v1.
- `--offline` disables official website lookup only; `--live` still makes actual Groq requests.
- The fallback deterministic report is not proof of completed CrewAI execution.
- Pin `litellm==1.105.1` in `requirements.txt` to keep fresh installs reproducible. For an existing env, don't reinstall everything unless needed.
