"""Read-only CrewAI import diagnostics. No API calls and no secrets printed."""
from __future__ import annotations
import importlib.metadata
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    print("=== Amar Passport: CrewAI Import Diagnostics ===", flush=True)
    print("Python:", sys.version.split()[0], flush=True)
    print("Interpreter:", sys.executable, flush=True)
    print("Working directory:", Path.cwd(), flush=True)
    for package in ("crewai", "litellm", "pydantic", "python-dotenv"):
        try:
            print(f"Installed {package}: {importlib.metadata.version(package)}", flush=True)
        except importlib.metadata.PackageNotFoundError:
            print(f"Installed {package}: NOT FOUND", flush=True)
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    print("Groq key configured:", bool(os.getenv("GROQ_API_KEY")), flush=True)

    stages = [
        ("CrewAI top-level import", "from crewai import Agent, Crew, Task, Process, LLM"),
        ("CrewAI tool decorator", "from crewai.tools import tool"),
        ("LiteLLM import", "import litellm"),
        ("Project CrewAI pipeline", "from crew_pipeline import run_crew"),
    ]
    failures = 0
    for label, source in stages:
        print(f"\n[{label}]", flush=True)
        try:
            exec(source, {})  # fixed trusted module import statements only
            print("PASS", flush=True)
        except Exception:
            failures += 1
            traceback.print_exc(file=sys.stdout)
    print("\n=== IMPORT DIAGNOSTICS:", "PASS" if not failures else f"{failures} FAILED", "===", flush=True)
    print("No Groq requests were made.", flush=True)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
