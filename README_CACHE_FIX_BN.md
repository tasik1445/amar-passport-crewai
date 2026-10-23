# Amar Passport — Groq `cache_breakpoint` compatibility patch

**Error**: `litellm.BadRequestError: GroqException ... property 'cache_breakpoint' is unsupported`.

CrewAI's LiteLLM-based agent sometimes adds `cache_breakpoint` to messages. Groq rejects that nonstandard field. This patch removes **only the top-level marker on Groq-bound messages**, without changing the original message objects or Agent logic.

## Apply on Windows

Extract this ZIP and copy these files into your existing `D:\Amar_Passport_CrewAI`:

- `groq_compat.py` → project root (new file)
- `crew_pipeline.py` → project root (replace old file)
- `tests/test_groq_compat.py` → `tests` (new file)

Do not replace `.env`, `main.py`, `requirements.txt`, your SQLite database, or your other agent files. Keep your working `litellm==1.105.1` environment.

In VS Code PowerShell:

```powershell
cd D:\Amar_Passport_CrewAI
.\.venv\Scripts\Activate.ps1
python -m pytest -q tests/test_groq_compat.py
python -m pytest -q
python main.py --live --offline --no-save
```

**Expected**: 5 new compatibility tests pass; if the live CrewAI tasks complete, `Completed sequential tasks: Policy Guardian, Chancellor of the Exchequer, Document Architect` is printed in the passport report.

## Notes

- The previously observed `RuntimeError: no running event loop` is not the actual blocking error in the supplied stack trace; Python's event loop setup continues successfully.
- This is a **temporary provider-compatibility workaround**, not a permanent CrewAI library fix. It patches a global function *only while one synchronous crew runs*. Don't run multiple crews concurrently in the same process with this patch.
- **Do not rotate your Groq key** or change your passport policy/data files to resolve this error.
- CrewAI `verbose=True` gives process/tool diagnostics, not private model reasoning.
- Real Groq calls use provider quota. Passing mock tests does NOT establish live Agent success.

Reference: https://github.com/crewAIInc/crewAI/issues/5886
