"""Deterministic safety/fee policy and bilingual report builder.

Educational, non-official guidance. Only domestic ordinary e-passport fees.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from policy_store import load_seed

@dataclass(frozen=True)
class Applicant:
    age: int
    profession: str = "private"
    requested_pages: int = 48
    requested_validity: int = 10
    delivery: str = "auto"
    trip_in_days: int | None = None
    has_nid: bool = True
    has_brc: bool = False
    has_parent_nid: bool = False
    has_noc: bool = False
    marital_change: bool = False
    name_change: bool = False
    reissue: bool = False
    lost_passport: bool = False
    location: str = "Dhaka"
    applying_abroad: bool = False

    def __post_init__(self):
        if not isinstance(self.age, int) or isinstance(self.age, bool) or not 0 <= self.age <= 115:
            raise ValueError("Age must be a whole number from 0 to 115")
        if self.requested_pages not in (48, 64) or self.requested_validity not in (5, 10):
            raise ValueError("Pages must be 48 or 64; validity must be 5 or 10")
        if self.delivery not in ("auto", "regular", "express", "super_express"):
            raise ValueError("Delivery must be auto/regular/express/super_express")
        if self.trip_in_days is not None and (type(self.trip_in_days) is not int or self.trip_in_days < 0):
            raise ValueError("trip_in_days must be non-negative integer")
        if not self.profession.strip():
            raise ValueError("Profession must not be empty")
        if self.applying_abroad:
            raise ValueError("Foreign-mission applicants use different USD fees. This demo supports applications within Bangladesh only.")


def delivery_for(profile: Applicant) -> str:
    if profile.delivery != "auto":
        return profile.delivery
    if profile.trip_in_days is None:
        return "regular"
    return "super_express" if profile.trip_in_days <= 4 else ("express" if profile.trip_in_days <= 21 else "regular")


def compute(profile: Applicant, fees: dict, provenance: str, lookup_warning: str = "") -> dict:
    flags: list[str] = []
    if profile.age < 18:
        allowed_validity = 5
        allowed_pages = 48
        if profile.requested_validity != 5:
            flags.append("INELIGIBLE REQUEST: Applicant under 18 cannot request 10-year validity; adjusted to 5 years.")
        if profile.requested_pages != 48:
            flags.append("INELIGIBLE REQUEST: Applicant under 18 requires a 48-page booklet; adjusted to 48 pages.")
    else:
        allowed_validity = profile.requested_validity
        allowed_pages = profile.requested_pages
    if allowed_pages == 64:
        flags.append("AVAILABILITY ALERT: Published official notice says 64-page booklet distribution is suspended; confirm resumption before paying. A 48-page alternative is recommended.")
        allowed_pages = 48
    if profile.age > 65:
        flags.append("SENIOR POLICY NOTE: The old mandatory 5-year validity restriction for over-65 applicants was cancelled according to updated official instructions.")
    if profile.age < 18:
        ids = ["English online Birth Registration Certificate (BRC)"]
        if not profile.has_brc:
            flags.append("DOCUMENT MISSING: English online BRC required for applicants under 18.")
        if not profile.has_nid:
            ids.append("Father's or mother's NID number")
            if not profile.has_parent_nid:
                flags.append("DOCUMENT MISSING: Parent's NID number required when minor has no NID.")
    elif profile.age <= 20:
        ids = ["NID or English online BRC"]
        if not (profile.has_nid or profile.has_brc):
            flags.append("DOCUMENT MISSING: NID or English BRC required for ages 18–20.")
    else:
        ids = ["National ID (NID)"]
        if not profile.has_nid:
            flags.append("DOCUMENT MISSING: NID is required for domestic applicants over 20.")
    speed = delivery_for(profile)
    profession = profile.profession.strip().lower()
    is_government = any(k in profession for k in ("government", "govt", "সরকারি", "civil servant"))
    charged_speed = speed
    if is_government and profile.has_noc:
        charged_speed = {"regular": "regular", "express": "regular", "super_express": "express"}[speed]
    actual_total = fees[(allowed_pages, allowed_validity, charged_speed)]
    base = int((Decimal(actual_total) / Decimal("1.15")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    vat = actual_total - base
    checklist = ["Printed online application / application summary", "Payment slip or A-Challan receipt (as applicable)", *ids]
    if profile.age < 6:
        checklist.append("3R lab-print photo with grey background (under 6 years)")
    if profile.age < 15:
        checklist.append("Parents' photographs (per official minor photo FAQ; confirm at RPO)")
    if is_government:
        checklist.append("Applicable government GO/NOC or official permission (verify issuing authority)")
        if not profile.has_noc and speed != "regular":
            flags.append("No NOC confirmed: special government delivery-fee concession was NOT applied.")
    elif profession in ("student", "শিক্ষার্থী"):
        checklist.append("Student ID / proof of profession, if applicable")
    else:
        checklist.append("Profession or employment proof, if requested/required for declared occupation")
    if profile.marital_change:
        checklist.append("Marriage certificate/Nikahnama or divorce document as applicable")
    if profile.name_change:
        checklist.append("Official documents supporting identity/name change; matching NID/BRC")
    if profile.reissue:
        checklist.append("Previous passport (original) for reissue")
    if profile.lost_passport:
        checklist.extend(["Police general diary (GD) report", "Photocopy of lost passport (if available)"])
    if profile.trip_in_days is not None and profile.trip_in_days <= 21:
        flags.append("TIME SENSITIVE: Delivery timelines start from biometric enrolment and are not a guarantee before a trip. Confirm appointment and office eligibility.")
    requested_quote = fees[(profile.requested_pages, profile.requested_validity, speed)]
    if lookup_warning:
        flags.append("SOURCE WARNING: " + lookup_warning)
    return {
        "profile": asdict(profile), "eligibility": "Needs correction" if (profile.age < 18 and (profile.requested_validity != 5 or profile.requested_pages != 48)) else "Check documents and alerts",
        "validity": allowed_validity, "pages": allowed_pages, "delivery": speed,
        "charged_delivery_tier": charged_speed, "total_bdt_including_vat": actual_total,
        "base_bdt": base, "vat_15_percent_bdt": vat,
        "requested_fee_reference_bdt": requested_quote,
        "requested_option_available": profile.requested_pages != 64 and not (profile.age < 18 and (profile.requested_validity != 5 or profile.requested_pages != 48)),
        "identification": ids, "documents": list(dict.fromkeys(checklist)),
        "flags": flags, "source": provenance, "official_sources": load_seed()["sources"],
    }


def render_report(r: dict) -> str:
    p = r["profile"]
    items = [
        ("Applicant", f"Age {p['age']}; {p['profession']}; {p['location']}"),
        ("Request", f"{p['requested_pages']} pages, {p['requested_validity']} years; {p['delivery']} delivery"),
        ("Eligibility", r["eligibility"]),
        ("Permitted / recommended validity", f"{r['validity']} years"),
        ("Recommended page count", str(r["pages"])),
        ("Delivery type", r["delivery"].replace("_", " ").title()),
        ("Fee tier charged", r["charged_delivery_tier"].replace("_", " ").title()),
        ("Fee BEFORE VAT", f"{r['base_bdt']:,} BDT"),
        ("15% VAT (included)", f"{r['vat_15_percent_bdt']:,} BDT"),
        ("TOTAL fee (VAT included)", f"**{r['total_bdt_including_vat']:,} BDT**"),
        ("Requested configuration fee (reference only)", f"{r['requested_fee_reference_bdt']:,} BDT — {'nominal listed amount; NOT available/valid as requested' if not r['requested_option_available'] else 'listed amount'}"),
        ("Identification", ", ".join(r["identification"])),
        ("Required / conditional documents", "; ".join(r["documents"])),
        ("Data source", r["source"]),
        ("Flags / warnings", "; ".join(r["flags"]) if r["flags"] else "None"),
    ]
    clean = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    english = "\n".join(["# Amar Passport — Passport Readiness Report", "", "## English report", "", "| Field | Assessment |", "|---|---|", *[f"| {clean(k)} | {clean(v)} |" for k, v in items]])
    bangla = "\n".join([
        "", "## বাংলা সারসংক্ষেপ", "",
        f"- আবেদনকারীর বয়স: **{p['age']}** বছর; পেশা: **{p['profession']}**।",
        f"- প্রস্তাবিত পাসপোর্ট: **{r['pages']} পৃষ্ঠা**, মেয়াদ **{r['validity']} বছর**, ডেলিভারি **{r['delivery']}**।",
        f"- মোট ফি **{r['total_bdt_including_vat']:,} টাকা**, যার মধ্যে ১৫% VAT **{r['vat_15_percent_bdt']:,} টাকা** অন্তর্ভুক্ত (দ্বিতীয়বার যোগ করবেন না)।",
        "- কাগজপত্র: " + "; ".join(r["documents"]),
        "- সতর্কতা: " + ("; ".join(r["flags"]) if r["flags"] else "উল্লেখযোগ্য কোনো সতর্কতা নেই।"),
        "", "## Official reference links", "",
        *[f"- {name}: {url}" for name, url in r["official_sources"].items()],
        "", "_Educational planning tool; not official approval. Confirm fees, availability, eligibility and appointment rules on the Bangladesh e-Passport portal before paying._",
    ])
    return english + "\n" + bangla + "\n"
