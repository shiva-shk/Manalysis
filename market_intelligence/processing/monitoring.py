"""Detects what's new since the last time a query was run.

There's no background scheduler in a Streamlit app, so monitoring here
means: re-run a saved search on demand (or via an external cron calling
this module) and diff the result identifiers against what's already
stored, rather than truly polling continuously.
"""


def find_new_results(results: list, known_identifiers: set) -> list:
    """Results whose identifier hasn't been seen before for this query.
    Results without an identifier can't be diffed reliably and are
    excluded rather than risk false "new" alerts on every re-run."""
    return [r for r in results if r.identifier and r.identifier not in known_identifiers]
