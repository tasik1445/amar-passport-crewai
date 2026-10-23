"""Validate core imports without consuming any Groq API credits."""
from importlib.metadata import version, PackageNotFoundError

for name in ("crewai", "litellm", "mcp"):
    try:
        print(f"{name} version: {version(name)}")
    except PackageNotFoundError:
        print(f"{name}: NOT INSTALLED")

try:
    from crewai import Agent, Crew, Task, Process, LLM
    from crewai.tools import tool
    import litellm
    print("CREWAI AND LITELLM IMPORTS: PASS")
except Exception as exc:
    print(f"IMPORT FAILURE: {type(exc).__name__}: {exc}")
    raise SystemExit(1)

print("Next: python -m pip check")
print("Then: python main.py --live --offline --no-save")
