"""Download official sources without modifying existing raw data.

Run with ``python -m enem_analysis.data.acquire enem`` or ``catalog PATH``.
All paths are relative to the repository, never to a user's home directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"
STAGING = ROOT / "data" / "processed" / "download_cache"
MANIFESTS = ROOT / "docs" / "sources" / "manifests"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    official = ("inep.gov.br", "ibge.gov.br", "ipeadata.gov.br", "ipea.gov.br")
    official_host = any(host == d or host.endswith("." + d) for d in official)
    official_page = host == "www.gov.br" and parsed.path.startswith("/inep/")
    if parsed.scheme not in {"https", "http"} or not (official_host or official_page):
        raise ValueError(f"Source is outside the declared official providers: {url}")


def download(source: dict) -> dict:
    """Preserve completed raw files; resume only a disposable partial download."""
    validate_url(source["url"])
    source_id = source["id"]
    if not source_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Invalid source ID")
    target = (RAW / source["path"]).resolve()
    if RAW.resolve() not in target.parents:
        raise ValueError("Target must be inside data/raw")
    manifest_path = MANIFESTS / f"{source_id}.json"
    if target.exists():
        if not manifest_path.exists():
            raise FileExistsError(
                f"Unregistered raw file; refusing overwrite: {target}"
            )
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        if record["url"] != source["url"] or record["path"] != source["path"]:
            raise ValueError(f"Source identity mismatch: {source_id}")
        if record["sha256"] != sha256(target):
            raise ValueError(f"Raw integrity mismatch: {target}")
        print(f"EXISTS {source_id} SHA256 verified", flush=True)
        return record

    STAGING.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    part = STAGING / f"{source_id}.part"
    headers = STAGING / f"{source_id}.headers"
    started = datetime.now(UTC).isoformat()
    print(f"DOWNLOAD {source_id} {source['url']}", flush=True)
    command = [
        "curl.exe",
        "--location",
        "--fail",
        "--show-error",
        "--silent",
        "--connect-timeout",
        "30",
        "--max-time",
        "7200",
        "--retry",
        "5",
        "--retry-delay",
        "3",
        "--continue-at",
        "-",
        "--dump-header",
        str(headers),
        "--output",
        str(part),
        source["url"],
    ]
    if source.get("format") == "zip":
        command.insert(1, "--retry-all-errors")
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise RuntimeError(f"curl failed ({result.returncode}): {source_id}")
    kind = source.get("format", target.suffix.lstrip("."))
    inventory = None
    if kind in {"zip", "xlsx"}:
        with zipfile.ZipFile(part) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"Invalid ZIP CRC: {source_id}: {bad}")
            inventory = [
                {"name": i.filename, "bytes": i.file_size, "crc32": f"{i.CRC:08x}"}
                for i in archive.infolist()
                if not i.is_dir()
            ]
    elif kind == "json":
        content = json.loads(part.read_text(encoding="utf-8-sig"))
        if not content or (isinstance(content, dict) and "error" in content):
            raise ValueError(f"Empty/error response: {source_id}")
    header_text = headers.read_text(encoding="iso-8859-1")
    selected_headers = {}
    for line in header_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.lower() in {"last-modified", "etag", "content-type"}:
                selected_headers[key.lower()] = value.strip()
    record = {
        **source,
        "download_started_utc": started,
        "download_completed_utc": datetime.now(UTC).isoformat(),
        "bytes": part.stat().st_size,
        "sha256": sha256(part),
        "http_metadata": selected_headers,
        "zip_crc_validated": inventory is not None,
    }
    if inventory is not None:
        record["members"] = inventory
    # Rename is confined to a single validated file; no raw file is overwritten.
    part.rename(target)
    write_json(manifest_path, record)
    print(f"OK {source_id} {record['bytes']:,} bytes {record['sha256']}", flush=True)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    enem = commands.add_parser("enem")
    enem.add_argument(
        "--years", type=int, nargs="+", default=list(range(2022, 2009, -1))
    )
    enem.add_argument("--workers", type=int, choices=[1, 2, 3], default=2)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "enem":
        sources = [
            {
                "id": f"enem_{year}",
                "provider": "INEP",
                "year": year,
                "url": f"https://download.inep.gov.br/microdados/microdados_enem_{year}.zip",
                "landing_page": "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem",
                "path": f"enem/{year}/microdados_enem_{year}.zip",
                "format": "zip",
            }
            for year in args.years
        ]
    else:
        sources = json.loads(args.path.read_text(encoding="utf-8"))["sources"]
    errors = []
    with ThreadPoolExecutor(max_workers=getattr(args, "workers", 1)) as pool:
        jobs = {pool.submit(download, source): source for source in sources}
        for future in as_completed(jobs):
            source = jobs[future]
            try:
                future.result()
            except Exception as exc:
                errors.append({"id": source["id"], "error": str(exc)})
                print(f"FAILED {source['id']}: {exc}", flush=True)
    write_json(
        ROOT / "data" / "processed" / f"acquisition_{args.command}_status.json",
        {"checked_at_utc": datetime.now(UTC).isoformat(), "errors": errors},
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
