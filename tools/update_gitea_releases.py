#!/usr/bin/env python3
"""
Script: sincronizza le release Gitea con i file in tools/release-notes/.
- Se la release esiste → aggiorna il body
- Se la release non esiste → la crea (richiede che il tag git esista già)

Uso:
    GITEA_TOKEN=<token> python3 tools/update_gitea_releases.py
oppure:
    python3 tools/update_gitea_releases.py --token <token>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

GITEA_BASE = "https://gitea.emulab.it/api/v1"
REPO       = "Simone/nsis-plugin-ns7zip"
NOTES_DIR  = Path(__file__).parent / "release-notes"


def api(method: str, path: str, token: str, data: dict | None = None) -> dict:
    url = f"{GITEA_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} {e.reason} — {e.read().decode()}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Update Gitea release bodies")
    parser.add_argument("--token", default=os.environ.get("GITEA_TOKEN"), help="Gitea API token")
    args = parser.parse_args()

    if not args.token:
        sys.exit("Errore: token mancante. Usa --token oppure imposta GITEA_TOKEN.")

    print("Recupero lista release da Gitea...", flush=True)
    try:
        releases = api("GET", f"/repos/{REPO}/releases?limit=50", args.token)
    except urllib.error.HTTPError:
        sys.exit("Errore nel recupero delle release.")

    existing = {r["tag_name"]: r["id"] for r in releases}

    note_files = sorted(NOTES_DIR.glob("v*.md"))
    if not note_files:
        sys.exit(f"Nessun file trovato in {NOTES_DIR}")

    for note_path in note_files:
        tag = note_path.stem
        body = note_path.read_text(encoding="utf-8").strip()

        if tag in existing:
            release_id = existing[tag]
            print(f"[{tag}] id={release_id}, aggiorno body...", end=" ", flush=True)
            try:
                api("PATCH", f"/repos/{REPO}/releases/{release_id}", args.token, {"body": body})
                print("OK")
            except urllib.error.HTTPError:
                print("FALLITO")
        else:
            print(f"[{tag}] release non trovata, creo...", end=" ", flush=True)
            try:
                result = api("POST", f"/repos/{REPO}/releases", args.token, {
                    "tag_name": tag,
                    "name": tag,
                    "body": body,
                    "draft": False,
                    "prerelease": False,
                })
                print(f"OK (id={result['id']})")
            except urllib.error.HTTPError:
                print("FALLITO (il tag git esiste su Gitea?)")


if __name__ == "__main__":
    main()
