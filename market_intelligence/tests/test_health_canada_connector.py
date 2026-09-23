from connectors.health_canada import normalize_mdall

SAMPLE_HTML = """
<table id="results" class="wb-tables table table-hover table-striped">
<thead><tr><th id="deviceName" scope="col">Device name listing</th></tr></thead>
<tbody>
<tr>
  <td>
    <a href="/mdall-limh/information?deviceId=1030742&amp;deviceName=ART%20FILLER%20FINE%20LINES&amp;licenceId=107790&amp;type=active&amp;lang=eng" title="Click on the device name to see the licence.">ART FILLER FINE LINES</a><br>
    <div>
      <span>Licence No.:</span>
      <span>107790</span>
    </div>
    <strong><span>FROM:</span></strong>
    <a href="/mdall-limh/information?companyId=165231&amp;type=active&amp;lang=eng" title="Click on the company name to see all its active licences.">LABORATOIRES FILL-MED</a><br>
    <span class="col-xs-offset-1">38 Cours Albert 1er</span>
    <span>Paris, 75, FR, 75008</span>
  </td>
</tr>
</tbody>
</table>
"""


def test_normalize_mdall_extracts_device_and_company():
    results = normalize_mdall(SAMPLE_HTML)
    assert len(results) == 1
    assert results[0].title == "ART FILLER FINE LINES"
    assert results[0].company == "LABORATOIRES FILL-MED"
    assert results[0].identifier == "107790"


def test_normalize_mdall_extracts_country_from_address():
    results = normalize_mdall(SAMPLE_HTML)
    assert results[0].country == "FR"


def test_normalize_mdall_handles_missing_table():
    assert normalize_mdall("<html><body>no results</body></html>") == []
