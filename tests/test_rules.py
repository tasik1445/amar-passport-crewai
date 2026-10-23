from pathlib import Path
from policy_store import ensure_cache, cache_fees
from passport_rules import Applicant, compute, render_report, delivery_for
from official_lookup import parse_official_fee_text, resolve_fees


def assess(p):
    return compute(p, cache_fees(), "offline cache")


def test_fee_cache(tmp_path):
    path = tmp_path / "policy_cache.db"
    ensure_cache(path)
    fees = cache_fees(path)
    assert len(fees) == 12
    assert fees[(48, 10, "express")] == 8050
    assert fees[(64, 10, "express")] == 10350


def test_minor_cannot_request_ten_years():
    r = assess(Applicant(age=15, profession="student", requested_validity=10, has_nid=False, has_brc=True, has_parent_nid=True))
    assert r["validity"] == 5
    assert r["pages"] == 48
    assert any("INELIGIBLE REQUEST" in x for x in r["flags"])
    assert r["total_bdt_including_vat"] == 4025


def test_minor_cannot_request_64_pages():
    r = assess(Applicant(age=12, profession="student", requested_pages=64, requested_validity=5, has_brc=True))
    assert r["pages"] == 48
    assert any("48-page" in x for x in r["flags"])


def test_64_page_fee_warns_and_offer_48():
    r = assess(Applicant(age=24, requested_pages=64, requested_validity=10, trip_in_days=14))
    assert r["total_bdt_including_vat"] == 8050
    assert r["requested_fee_reference_bdt"] == 10350
    assert not r["requested_option_available"]
    assert any("64-page" in x for x in r["flags"])


def test_no_double_vat():
    r = assess(Applicant(age=24, delivery="express"))
    assert (r["base_bdt"], r["vat_15_percent_bdt"], r["total_bdt_including_vat"]) == (7000, 1050, 8050)


def test_age_boundary_18_to_20():
    r = assess(Applicant(age=20, has_nid=False, has_brc=True))
    assert not any("DOCUMENT MISSING" in x for x in r["flags"])


def test_over_twenty_nid_required():
    r = assess(Applicant(age=21, has_nid=False, has_brc=True))
    assert any("NID is required" in x for x in r["flags"])


def test_over_65_not_invalid():
    r = assess(Applicant(age=70, requested_validity=10))
    assert r["validity"] == 10
    assert not any("INELIGIBLE" in x for x in r["flags"])


def test_government_noc_concession():
    r = assess(Applicant(age=34, profession="government", has_noc=True, delivery="express"))
    assert r["charged_delivery_tier"] == "regular"
    assert r["total_bdt_including_vat"] == 5750
    assert "GO/NOC" in " ".join(r["documents"])


def test_child_photo_only_under_six():
    young = assess(Applicant(age=5, has_nid=False, has_brc=True, has_parent_nid=True))
    older = assess(Applicant(age=15, has_nid=False, has_brc=True, has_parent_nid=True))
    assert any("3R" in x for x in young["documents"])
    assert not any("3R" in x for x in older["documents"])


def test_changes_require_supporting_docs():
    r = assess(Applicant(age=30, marital_change=True, name_change=True))
    assert any("Marriage certificate" in x for x in r["documents"])
    assert any("identity/name change" in x for x in r["documents"])


def test_report_contains_english_table_and_bangla():
    md = render_report(assess(Applicant(age=24, requested_pages=64, trip_in_days=14)))
    assert "| Field | Assessment |" in md
    assert "## বাংলা সারসংক্ষেপ" in md
    assert "8,050 BDT" in md


def test_full_official_parse():
    lines = ["e-Passport fees for inside Bangladesh (Including 15% VAT)"]
    for pages in (48, 64):
        for years in (5, 10):
            lines.append(f"e-Passport with {pages} pages and {years} years validity")
            lines.extend(["Regular delivery: TK 4,025", "Express delivery: TK 6,325", "Super Express delivery: TK 8,625"])
    lines.append("e-Passport fees for Bangladesh Mission's General Applicants")
    r = parse_official_fee_text(" ".join(lines))
    assert len(r) == 12
    assert r[(48, 5, "express")] == 6325


def test_scrape_rejects_incomplete():
    import pytest
    with pytest.raises(ValueError):
        parse_official_fee_text("e-Passport fees for inside Bangladesh 48 pages only")


def test_offline_fallback():
    fees, source, warning = resolve_fees(offline=True)
    assert len(fees) == 12 and "SQLite" in source and "Offline" in warning


def test_input_validation():
    import pytest
    with pytest.raises(ValueError):
        Applicant(age=15, requested_pages=36)


def test_foreign_mission_applicant_requires_separate_fees():
    import pytest
    with pytest.raises(ValueError):
        Applicant(age=24, applying_abroad=True)
