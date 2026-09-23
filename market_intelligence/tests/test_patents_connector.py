import os

import pytest

from connectors.base import ConnectorError
from connectors.patents import normalize_patents, search_patents

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ops:world-patent-data xmlns:ops="http://ops.epo.org" xmlns:ex="http://www.epo.org/exchange">
  <ex:exchange-documents>
    <ex:exchange-document country="EP" doc-number="1234567" kind="A1">
      <ex:bibliographic-data>
        <ex:publication-reference>
          <ex:document-id>
            <ex:date>20200101</ex:date>
          </ex:document-id>
        </ex:publication-reference>
        <ex:parties>
          <ex:applicants>
            <ex:applicant>
              <ex:applicant-name>
                <ex:name>Example Aesthetics Ltd</ex:name>
              </ex:applicant-name>
            </ex:applicant>
          </ex:applicants>
        </ex:parties>
        <ex:invention-title lang="en">Cross-linked hyaluronic acid composition</ex:invention-title>
      </ex:bibliographic-data>
    </ex:exchange-document>
  </ex:exchange-documents>
</ops:world-patent-data>
"""


def test_search_patents_without_credentials_raises_connector_error():
    os.environ.pop("EPO_OPS_CONSUMER_KEY", None)
    os.environ.pop("EPO_OPS_CONSUMER_SECRET", None)
    with pytest.raises(ConnectorError):
        search_patents("hyaluronic acid")


def test_normalize_patents_extracts_title_and_number():
    results = normalize_patents(SAMPLE_XML)
    assert len(results) == 1
    assert results[0].identifier == "EP1234567A1"
    assert "hyaluronic" in results[0].title.lower()
