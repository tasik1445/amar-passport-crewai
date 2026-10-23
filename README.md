# Amar Passport — CrewAI Multi-Agent Assignment

A Bangladesh e-Passport **educational readiness assistant**, with 3 specialized CrewAI agents, age/identity policy validation, official VAT-inclusive BDT fees, customized documents, an English Markdown table and Bangla summary. It is **not an official passport application** and cannot promise approval or urgent delivery.

## Important 2026 audit notes

- 15-year-old applicants **cannot request 10-year validity**; under 18 requires **5 years and 48 pages**.
- Identity: under 18 English BRC; 18–20 NID or English BRC; over 20 domestic NID.
- The over-65 mandatory five-year-only restriction was **cancelled** per the current [official instructions](https://www.epassport.gov.bd/instructions/instructions).
- Published [official fee table](https://www.epassport.gov.bd/instructions/passport-fees) ALREADY INCLUDES 15% VAT. Do not multiply by 1.15 again.
- Official [64-page suspension notice](https://www.epassport.gov.bd/landing/notices/151) says issuance was suspended starting 15 January 2023. This repository has not verified an official resumption. Treat 64-page prices as historical/listed reference figures only and confirm actual availability.
- Delivery timelines begin after biometric enrolment and may be affected by verification and appointments.
- All fee calculations here are for **inside Bangladesh**, not embassy fees. Additional official charges where applicable are outside the published passport base table.

## Components

- `policy_store.py`: initializes `data/passport_cache.db` (SQLite) from the versioned `data/rules_2026.json` snapshot.
- `official_lookup.py`: attempts live official portal fee page extraction; if unavailable, falls back to the local SQLite fee database **with an explicit warning**. It never mixes an incomplete web page with cached fees.
- `passport_rules.py`: deterministic validity, age restrictions, NID/BRC, VAT calculations, speed/fee selection, profession documents, and warnings. The LLM is not allowed to invent policy or amounts.
- `crew_pipeline.py`: 3 CrewAI `Agent`s with descriptive personas and 3 sequential `Task`s; Fee Task uses `context=[policy_task]`; Document Task uses `context=[policy_task, fee_task]`. `verbose=True` prints execution logs (not hidden model thought processes).
- `main.py`: CLI; saves Markdown report to `outputs/`.

## VS Code / Windows Setup

Requires **Python 3.10–3.13** (3.12 recommended), VS Code, and optional Groq API access for actual multi-agent execution. Keep this project separate from other assignments.

```powershell
cd D:\
mkdir Amar_Passport_CrewAI
cd Amar_Passport_CrewAI
# Extract repository ZIP contents here (or git clone repository).
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in VS Code, fill in `GROQ_API_KEY` (you can reuse your Groq account key from your prior project, but never copy `.env` into GitHub). Correct CrewAI/LiteLLM prefix: `CREWAI_MODEL=groq/openai/gpt-oss-20b`.

## Commands

Offline test without any API:

```powershell
python -m pytest -q
python main.py --demo --offline
python main.py --demo --offline --profile examples/minor_inconsistent.json
python main.py --demo --offline --profile examples/government_employee.json
```

**Real multi-agent execution** (Groq free-tier quotas apply):

```powershell
python main.py --live --offline
```

Remove `--offline` to try official online fee scraping (may fail on client-rendered pages; SQLite fallback will be clearly flagged):

```powershell
python main.py --live
```

You can alter the applicant by editing a JSON file in `examples/`; fields include `age`, `profession`, `requested_pages`, `requested_validity`, `delivery` (`auto`, `regular`, `express`, `super_express`), `trip_in_days`, `has_nid`, `has_brc`, `has_parent_nid`, `has_noc`, `marital_change`, `name_change`, `reissue`, `lost_passport`, and `location`.

## Examples to demonstrate

1. **24-year-old private employee**, 64 pages, 10 years, business trip in 14 days: listed 64-page Express fee is Tk 10,350 including VAT **for reference only**. Official suspension warning leads to a **48-page 10-year Express recommendation at Tk 8,050** including VAT. Actual ability to travel in two weeks is not guaranteed.
2. **15-year-old asks for 10-year**: show red-flag-style `INELIGIBLE REQUEST`, automatically analyze 5-year/48-page option, English BRC and parent ID conditions.
3. **Government employee with valid NOC**, 48-page 10-year Express: show official concession of Express service at Regular fee (Tk 5,750). Confirm eligibility and evidence at passport office.

## Submission and 2-minute demonstration video outline

1. Introduce applicant/profile and three CrewAI roles with `role`, `goal`, and `backstory`.
2. Show `fee_task = Task(..., context=[policy_task])` and `doc_task` using both contexts.
3. Run `python main.py --live --offline`; point out `verbose=True` logs and locally cached official fee schedule.
4. Show bilingual Markdown report with English table; explain VAT is included.
5. Run 15-year-old invalid-request example and show automatic flag.
6. Explain fallback: official web site can fail or be dynamic, so the program uses `passport_cache.db`; flag provenance and verify official source before payment.

## Official sources

- Fee table: https://www.epassport.gov.bd/instructions/passport-fees
- Applicant instructions: https://www.epassport.gov.bd/instructions/instructions
- Documents checklist: https://www.epassport.gov.bd/landing/notices/160
- Changes of particulars: https://www.epassport.gov.bd/landing/faqs/21
- Minor photos: https://www.epassport.gov.bd/landing/faqs/4
- 64-page availability notice: https://www.epassport.gov.bd/landing/notices/151

Updated for assignment design on 2026-10-24. Recheck the live portal for subsequent changes.
