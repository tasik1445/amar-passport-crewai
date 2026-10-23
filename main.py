"""CLI: offline demonstration or actual 3-agent CrewAI execution."""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from passport_rules import Applicant, compute, render_report
from official_lookup import resolve_fees
from policy_store import ensure_cache
import json
import os
import traceback

ROOT = Path(__file__).resolve().parent


def parse_args():
    p = argparse.ArgumentParser(description="Amar Passport — bilingual passport readiness crew")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true", help="Deterministic rule engine only; does not execute CrewAI")
    group.add_argument("--live", action="store_true", help="Execute three CrewAI agents with Groq API")
    p.add_argument("--profile", type=Path, default=ROOT / "examples" / "private_employee.json")
    p.add_argument("--offline", action="store_true", help="Simulate failed/unavailable official site; use local SQLite cache")
    p.add_argument("--no-save", action="store_true", help="Don't save report to outputs folder")
    return p.parse_args()


def run():
    args = parse_args()
    load_dotenv(ROOT / ".env")
    try:
        p = Applicant(**json.loads(args.profile.read_text(encoding="utf-8")))
        ensure_cache()
        fees, provenance, lookup_warning = resolve_fees(offline=args.offline)
        result = compute(p, fees, provenance, lookup_warning)
        crew_note = ""
        crew_failed = False
        if args.live:
            if not os.getenv("GROQ_API_KEY"):
                raise RuntimeError("GROQ_API_KEY not set in .env; use --demo for offline testing")
            from crew_pipeline import run_crew
            try:
                audit, agents = run_crew(p, result)
                crew_note = f"\n## CrewAI execution status\n\nCompleted sequential tasks: {', '.join(agents)}.\n\n"
                print("\nCrewAI task audit:\n", audit[:6000])
            except Exception as exc:
                crew_failed = True
                print("\n=== CREWAI LIVE ERROR TRACEBACK ===")
                traceback.print_exc()
                print("=== END CREWAI TRACEBACK ===\n")
                # The actual error detail belongs in the report, but do not copy
                # secrets or arbitrary API response text into an output file.
                crew_note = (
                    "\n## CrewAI execution status\n\n"
                    f"CrewAI execution FAILED ({type(exc).__name__}). "
                    "The deterministic assessment is NOT evidence of multi-agent execution. "
                    "Check the terminal traceback to identify the missing import.\n\n"
                )
        else:
            crew_note = "\n## Execution mode\n\nOFFLINE DEMO ONLY — no CrewAI agents were executed.\n\n"
        report = render_report(result) + crew_note
        print("\n" + report)
        if not args.no_save:
            output = ROOT / "outputs" / (datetime.now().strftime("passport_readiness_%Y%m%d_%H%M%S") + ".md")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report, encoding="utf-8")
            print("Saved report:", output)
        if crew_failed:
            raise SystemExit(3)  # Live execution failed: do not falsely report CrewAI success.
    except (ValueError, KeyError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        raise SystemExit(2)

if __name__ == "__main__":
    run()
