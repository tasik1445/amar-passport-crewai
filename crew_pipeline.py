"""Three real CrewAI agents with explicit task context dependencies.

CrewAI verbose logs show operational execution/tool logs, not private chain-of-thought.
The final fee/eligibility report is produced by verified Python rules, not LLM prose.
"""
from __future__ import annotations
import json
import os
from passport_rules import Applicant
from groq_compat import groq_cache_compatibility


def run_crew(profile: Applicant, assessment: dict) -> tuple[str, list[str]]:
    # Lazy imports: no CrewAI/API needed for deterministic --demo or pytest.
    from crewai import Agent, Crew, Task, Process, LLM
    from crewai.tools import tool

    @tool("PassportPolicyReference")
    def policy_reference() -> str:
        """Return verified Bangladesh e-passport identification and age rules."""
        return ("Under 18: 5-year, 48-page passport only; English BRC required; parent NID number when child lacks NID. "
                "18–20: NID or English BRC. Over 20 (domestic): NID required. "
                "The formerly mandatory 5-year restriction for over-65 applicants was cancelled. "
                "Official: https://www.epassport.gov.bd/instructions/instructions")

    @tool("VerifiedFeeLookup")
    def verified_fee_lookup() -> str:
        """Return the already verified VAT-inclusive BDT fee and applicable flags."""
        return json.dumps({k: assessment[k] for k in
               ("validity", "pages", "delivery", "charged_delivery_tier",
                "total_bdt_including_vat", "base_bdt", "vat_15_percent_bdt",
                "requested_fee_reference_bdt", "requested_option_available", "flags", "source")}, ensure_ascii=False)

    @tool("DocumentChecklistReference")
    def document_reference() -> str:
        """Return age- and profession-dependent verified checklist items."""
        return json.dumps({"documents": assessment["documents"], "identification": assessment["identification"]}, ensure_ascii=False)

    model = os.getenv("CREWAI_MODEL", "groq/openai/gpt-oss-20b")
    llm = LLM(model=model, temperature=0.1)
    agent_policy = Agent(
        role="The Policy Guardian — Bangladesh Passport Policy Expert",
        goal="Audit age eligibility, identity evidence, validity and page restrictions without inventing rules.",
        backstory="An experienced, evidence-led consular eligibility officer who always flags mismatches and distinguishes historic rules from current guidance.",
        llm=llm, tools=[policy_reference], verbose=True, allow_delegation=False, max_iter=3,
    )
    agent_fee = Agent(
        role="The Chancellor of the Exchequer — Passport Fee Auditor",
        goal="Check the official Bangladesh VAT-inclusive fee, never double-charge VAT, and distinguish quoted fee from available product.",
        backstory="A meticulous public-sector financial auditor who reconciles page count, delivery speed, and eligibility before quoting a fee.",
        llm=llm, tools=[verified_fee_lookup], verbose=True, allow_delegation=False, max_iter=3,
    )
    agent_docs = Agent(
        role="The Document Architect — Passport Documentation Officer",
        goal="Audit a personalized checklist with clear conditional documents and official source references.",
        backstory="A careful passport enrolment specialist experienced with minors, government employees, personal data changes and urgent travel.",
        llm=llm, tools=[document_reference], verbose=True, allow_delegation=False, max_iter=3,
    )
    policy_task = Task(
        description=("Review applicant profile and authoritative prevalidated facts. Identify every issue. "
                     "Never override deterministic official-policy checks. Call PassportPolicyReference. "
                     f"PROFILE: {json.dumps(profile.__dict__, ensure_ascii=False)}\n"
                     f"VALIDATED ASSESSMENT: {json.dumps(assessment, ensure_ascii=False)}"),
        expected_output="Short age-and-identity eligibility audit, with warning flags and policy source.",
        agent=agent_policy,
    )
    fee_task = Task(
        description=("Use the Policy Guardian's report as CONTEXT. Call VerifiedFeeLookup. "
                     "Check validity, page count, delivery, and published VAT-inclusive prices. "
                     "Differentiate unavailable 64-page requests from the 48-page feasible alternative. "
                     "Do not independently add 15% VAT."),
        expected_output="Fee audit identifying exact BDT total, VAT breakdown, charged delivery tier and key alerts.",
        agent=agent_fee, context=[policy_task],
    )
    doc_task = Task(
        description=("Use BOTH previous task outputs as context. Call DocumentChecklistReference. "
                     "Review required identification and profession-specific documents. "
                     "Use English and Bangla, and note any unavailable selection or missing evidence. "
                     "Only verified, precomputed amounts may appear in your response."),
        expected_output="Checklist audit with English and Bangla brief notes, citing official portal sections.",
        agent=agent_docs, context=[policy_task, fee_task],
    )
    crew = Crew(agents=[agent_policy, agent_fee, agent_docs], tasks=[policy_task, fee_task, doc_task],
                process=Process.sequential, verbose=True, memory=False)
    # CrewAI may pass a nonstandard cache_breakpoint attribute that Groq rejects.
    # Restrict the workaround to this synchronous Groq crew execution.
    with groq_cache_compatibility():
        result = crew.kickoff()
    return str(result), ["Policy Guardian", "Chancellor of the Exchequer", "Document Architect"]
