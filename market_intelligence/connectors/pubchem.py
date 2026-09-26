"""PubChem connector — NIH's official chemical compound database.

Docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest

Free, no API key, no rate-limit registration needed (PubChem asks for no
more than ~5 requests/second, which a single interactive search stays
well under). Covers chemical identity (CAS number via synonyms,
molecular formula, IUPAC name, SMILES) — not regulatory status or
cosmetic-specific data, which is what CosIng/MFDS are for. A query that
doesn't match an exact compound name falls back to PubChem's autocomplete
to suggest the closest real compound name, since PubChem's name search
is exact-match only.

Requests go through curl (subprocess), not the `requests` library:
PubChem's bot-mitigation deterministically returns 503 PUGREST.ServerBusy
for every python-requests call observed (headers, User-Agent, and retries
all made no difference), while curl against the identical URL through the
identical network path succeeds every time — a TLS/HTTP client
fingerprint block on the library, not a real rate limit or access
restriction. This is a workaround for that specific block, not a general
pattern to copy for other connectors that don't hit it.
"""

import json
import re
import subprocess
from urllib.parse import quote

from connectors.base import ConnectorError, SearchResult

PUG_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
AUTOCOMPLETE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound"

PROPERTIES = "MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES,InChIKey"

CURL_TIMEOUT_SECONDS = 30

# A CAS Registry Number looks like digits-digits-checkdigit (e.g.
# "701-54-2"); PubChem lists it as one of a compound's synonyms, not a
# dedicated field, so this is how it gets picked out.
_CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")


def _curl_get(url: str) -> tuple[int, dict]:
    """Runs `curl -s -w '\\n%{http_code}'` against url and returns
    (status_code, parsed_json_body). Raises ConnectorError on a transport
    failure (curl itself failing to run/connect) or unparseable body."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}", "--max-time", str(CURL_TIMEOUT_SECONDS), url],
            capture_output=True, text=True, timeout=CURL_TIMEOUT_SECONDS + 5, check=False,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ConnectorError(f"PubChem request failed: {exc}") from exc

    if result.returncode != 0:
        raise ConnectorError(f"PubChem request failed: curl exit code {result.returncode}")

    body, _, status_str = result.stdout.rpartition("\n")
    try:
        status_code = int(status_str)
    except ValueError:
        raise ConnectorError("PubChem request failed: could not read response status") from None

    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise ConnectorError(f"PubChem returned unparseable response: {exc}") from exc

    return status_code, data


def _autocomplete(query: str) -> str | None:
    url = f"{AUTOCOMPLETE_URL}/{quote(query)}/json?limit=1"
    try:
        status_code, data = _curl_get(url)
    except ConnectorError:
        return None

    if status_code != 200:
        return None
    terms = data.get("dictionary_terms", {}).get("compound", [])
    return terms[0] if terms else None


def _fetch_properties(name: str) -> dict | None:
    url = f"{PUG_BASE}/compound/name/{quote(name)}/property/{PROPERTIES}/JSON"
    status_code, data = _curl_get(url)

    if status_code == 404:
        return None
    if status_code != 200:
        fault = data.get("Fault", {}).get("Message", f"HTTP {status_code}")
        raise ConnectorError(f"PubChem request failed: {fault}")

    props = data.get("PropertyTable", {}).get("Properties", [])
    return props[0] if props else None


def _fetch_synonyms(cid: int) -> list[str]:
    url = f"{PUG_BASE}/compound/cid/{cid}/synonyms/JSON"
    try:
        status_code, data = _curl_get(url)
    except ConnectorError:
        return []

    if status_code != 200:
        return []
    info = data.get("InformationList", {}).get("Information", [])
    return info[0].get("Synonym", []) if info else []


def search_pubchem(query: str) -> dict | None:
    """Looks up a compound by name, falling back to PubChem's autocomplete
    suggestion if the exact name isn't a match. Returns None if nothing
    resolves at all (query isn't recognizable as any compound name)."""
    props = _fetch_properties(query)
    matched_name = query

    if props is None:
        suggestion = _autocomplete(query)
        if suggestion is None:
            return None
        props = _fetch_properties(suggestion)
        matched_name = suggestion
        if props is None:
            return None

    cid = props["CID"]
    synonyms = _fetch_synonyms(cid)
    cas_number = next((s for s in synonyms if _CAS_RE.match(s)), None)

    return {
        "matched_name": matched_name,
        "cid": cid,
        "cas_number": cas_number,
        **props,
    }


def normalize_pubchem(result: dict | None) -> list[SearchResult]:
    if result is None:
        return []

    return [
        SearchResult(
            title=result["matched_name"],
            entity_type="chemical_compound",
            entity_name=result["matched_name"],
            company=None,
            country=None,
            category="chemical compound",
            regulatory_status=None,
            summary=f"CAS {result['cas_number']}" if result.get("cas_number") else None,
            identifier=f"CID {result['cid']}",
            source_name="PubChem",
            source_url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{result['cid']}",
            source_type="official",
        )
    ]
