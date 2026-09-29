import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ema import normalize_ema  # noqa: E402
from fda import normalize_fda  # noqa: E402


def fda_record(**over):
    rec = {
        "application_number": "NDA017381",
        "sponsor_name": "ACME",
        "openfda": {"generic_name": ["DRUGINE"]},
        "products": [{"brand_name": "DRUGO", "dosage_form": "TABLET", "route": "ORAL",
                      "marketing_status": "Prescription", "te_code": "AB",
                      "active_ingredients": [{"name": "DRUGINE", "strength": "5MG"}]}],
        "submissions": [
            {"submission_type": "SUPPL", "submission_status": "AP", "submission_status_date": "20200101"},
            {"submission_type": "ORIG", "submission_status": "AP", "submission_status_date": "19731126",
             "submission_class_code_description": "Type 1 - New Molecular Entity"},
        ],
    }
    rec.update(over)
    return rec


def test_fda_uses_original_approval_date_not_supplement():
    (row,) = normalize_fda([fda_record()])
    assert row["approval_date"] == "1973-11-26"
    assert row["approval_year"] == 1973
    assert row["application_type"] == "NDA"
    assert row["approval_category"] == "Type 1 - New Molecular Entity"
    assert row["inn"] == "drugine"
    assert row["source_url"].endswith("ApplNo=017381")


def test_fda_skips_tentative_only_applications():
    rec = fda_record(submissions=[{"submission_type": "ORIG", "submission_status": "TA",
                                   "submission_status_date": "20240101"}])
    assert normalize_fda([rec]) == []


def test_fda_anda_type_and_discontinued_status():
    rec = fda_record(application_number="ANDA123456")
    rec["products"][0]["marketing_status"] = "Discontinued"
    (row,) = normalize_fda([rec])
    assert row["application_type"] == "ANDA"
    assert row["status"] == "Discontinued"


def ema_record(**over):
    rec = {
        "category": "Human", "name_of_medicine": "Keytruda", "ema_product_number": "EMEA/H/C/003820",
        "medicine_status": "Authorised", "opinion_status": "",
        "international_non_proprietary_name_common_name": "pembrolizumab",
        "marketing_authorisation_developer_applicant_holder": "MSD",
        "marketing_authorisation_date": "17/07/2015", "european_commission_decision_date": "17/07/2015",
        "opinion_adopted_date": "22/05/2015", "last_updated_date": "28/09/2026",
        "orphan_medicine": "No", "biosimilar": "No", "generic": "No",
    }
    rec.update(over)
    return rec


def test_ema_date_is_ddmmyyyy_authorisation_not_last_updated():
    (row,) = normalize_ema([ema_record()])
    assert row["approval_date"] == "2015-07-17"
    assert row["approval_year"] == 2015
    assert row["orphan_designation"] is False


def test_ema_orphan_is_boolean():
    (row,) = normalize_ema([ema_record(orphan_medicine="Yes")])
    assert row["orphan_designation"] is True


def test_ema_skips_veterinary_refused_and_withdrawn_applications():
    records = [
        ema_record(category="Veterinary"),
        ema_record(medicine_status="Refused", marketing_authorisation_date="", european_commission_decision_date=""),
        ema_record(medicine_status="Application withdrawn", marketing_authorisation_date="", european_commission_decision_date=""),
    ]
    assert normalize_ema(records) == []


def test_ema_keeps_withdrawn_after_authorisation_and_positive_opinion():
    records = [
        ema_record(medicine_status="Withdrawn"),
        ema_record(name_of_medicine="Newdrug", ema_product_number="X", medicine_status="Opinion",
                   opinion_status="Positive", marketing_authorisation_date="", european_commission_decision_date="",
                   opinion_adopted_date="10/09/2026"),
    ]
    rows = normalize_ema(records)
    assert [r["status"] for r in rows] == ["Withdrawn", "CHMP positive opinion (awaiting EC decision)"]
    assert rows[1]["approval_date"] == "2026-09-10"


from labels import _best, _clean  # noqa: E402


def test_label_text_drops_heading_and_truncates_at_sentence():
    text = _clean(["1 INDICATIONS AND USAGE  Drugo treats A.  It also treats B; and more C " * 1], 40)
    assert text.startswith("Drugo treats A.")
    assert text.endswith("...")
    assert _clean([], 100) is None


def test_label_choice_prefers_matching_brand_and_newest():
    def label(brand, when, ind="x"):
        return {"openfda": {"application_number": ["NDA1"], "brand_name": [brand],
                            "product_type": ["HUMAN PRESCRIPTION DRUG"]},
                "effective_time": when, "indications_and_usage": [ind]}
    labels_ = [label("REPACK", "20260101"), label("DRUGO", "20200101"), label("DRUGO", "20240101")]
    assert _best(labels_, "NDA1", "DRUGO")["effective_time"] == "20240101"
    assert _best(labels_, "NDA9", "DRUGO") is None
