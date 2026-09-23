from connectors.clinicaltrials import normalize_clinical_trials
from connectors.openfda import normalize_openfda_devices
from connectors.pubmed import normalize_pubmed


def test_normalize_clinical_trials():
    raw = {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT01234567",
                        "briefTitle": "Study of PDRN in skin rejuvenation",
                    },
                    "statusModule": {"overallStatus": "RECRUITING"},
                    "sponsorCollaboratorsModule": {
                        "leadSponsor": {"name": "Example Sponsor"}
                    },
                    "designModule": {"enrollmentInfo": {"count": 120}},
                    "conditionsModule": {"conditions": ["Skin aging"]},
                    "armsInterventionsModule": {
                        "interventions": [{"name": "PDRN injection"}]
                    },
                    "contactsLocationsModule": {
                        "locations": [{"country": "South Korea"}]
                    },
                }
            }
        ]
    }
    results = normalize_clinical_trials(raw)
    assert len(results) == 1
    assert results[0].identifier == "NCT01234567"
    assert results[0].company == "Example Sponsor"
    assert results[0].country == "South Korea"


def test_normalize_openfda_devices():
    raw = {
        "results": [
            {
                "k_number": "K123456",
                "device_name": "Example Dermal Filler",
                "applicant": "Example Manufacturer",
                "product_code": "LMH",
                "decision_description": "SUBSTANTIALLY EQUIVALENT",
            }
        ]
    }
    results = normalize_openfda_devices(raw)
    assert len(results) == 1
    assert results[0].identifier == "K123456"
    assert results[0].country == "United States"


def test_normalize_pubmed():
    raw = {
        "resultList": {
            "result": [
                {
                    "pmid": "12345678",
                    "title": "Efficacy of PDRN in dermal repair",
                    "authorString": "Smith J, Doe A",
                    "abstractText": "This study evaluates...",
                }
            ]
        }
    }
    results = normalize_pubmed(raw)
    assert len(results) == 1
    assert results[0].identifier == "12345678"
    assert "pubmed.ncbi.nlm.nih.gov" in results[0].source_url
