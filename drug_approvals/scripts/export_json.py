"""Fetch FDA and EMA approvals, merge with the TGA rows, write the JSON the tracker page loads.

    python scripts/export_json.py [--out data/out] [--split-mb 8]

Writes approvals-N.json (newest first), manifest.json, meta.json.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ema, fda, tga  # noqa: E402


def build_rows() -> tuple[list[dict], list[dict]]:
    sources, rows = [], []
    for name, load, normalize in (
        (fda.SOURCE, fda.load_drugsfda, fda.normalize_fda),
        (ema.SOURCE, ema.load_ema_medicines, ema.normalize_ema),
        ("manual: tga_artg", tga.load_tga, lambda r: r),
    ):
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            part = normalize(load())
            status = "ok" if part else "empty"
        except Exception as exc:  # keep going; the page shows per-source status
            part, status = [], f"error: {exc}"
        rows += part
        sources.append({"source": name, "last_run": started, "status": status, "count": len(part)})
    for r in rows:
        if not str(r["id"]).startswith(r["region"] + "-"):
            r["id"] = f"{r['region']}-{r['id']}"
    rows.sort(key=lambda r: (r["approval_date"] or "", r["id"]), reverse=True)
    return rows, sources


def write(rows, sources, out: Path, split_mb: float):
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("approvals*.json"):
        old.unlink()
    parts, current, size = [], [], 0
    for r in rows:
        line = len(json.dumps(r, separators=(",", ":")))
        if current and size + line > split_mb * 1_000_000:
            parts.append(current)
            current, size = [], 0
        current.append(r)
        size += line
    parts.append(current)
    names = []
    for i, part in enumerate(parts):
        name = f"approvals-{i}.json"
        (out / name).write_text(json.dumps(part, separators=(",", ":")), encoding="utf-8")
        names.append(name)
    (out / "manifest.json").write_text(json.dumps({"approvals_files": names}))
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "approval_count": len(rows),
        "sources": sources,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "out"))
    ap.add_argument("--split-mb", type=float, default=8)
    args = ap.parse_args()
    rows, sources = build_rows()
    meta = write(rows, sources, Path(args.out), args.split_mb)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
