#!/usr/bin/env python3
"""
Script: sincronizza i body delle release GitHub con i file in tools/release-notes/.
- Se la release esiste → aggiorna il body
- Se la release non esiste → la salta (le release GitHub vengono create dal workflow CI)

Uso:
    GITHUB_TOKEN=<token> python3 tools/update_github_releases.py
oppure:
    python3 tools/update_github_releases.py --token <token>

Richiede un PAT GitHub con permesso 'contents: write' sul repo.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

GITHUB_BASE = "https://api.github.com"
REPO        = "systempal/nsis-plugin-ns7zip"
NOTES_DIR   = Path(__file__).parent / "release-notes"


def api(method: str, path: str, token: str, data: dict | None = None) -> dict:
    url = f"{GITHUB_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "update_github_releases/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} {e.reason} — {e.read().decode()}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Update GitHub release bodies")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub API token")
    args = parser.parse_args()

    if not args.token:
        sys.exit("Errore: token mancante. Usa --token oppure imposta GITHUB_TOKEN.")

    note_files = sorted(NOTES_DIR.glob("v*.md"))
    if not note_files:
        sys.exit(f"Nessun file trovato in {NOTES_DIR}")

    for note_path in note_files:
        tag = note_path.stem
        body = note_path.read_text(encoding="utf-8").strip()

        print(f"[{tag}] recupero release...", end=" ", flush=True)
        try:
            release = api("GET", f"/repos/{REPO}/releases/tags/{tag}", args.token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("SALTATO (release non trovata su GitHub)")
            else:
                print("ERRORE")
            continue

        release_id = release["id"]
        print(f"id={release_id}, aggiorno body...", end=" ", flush=True)
        try:
            api("PATCH", f"/repos/{REPO}/releases/{release_id}", args.token, {"body": body})
            print("OK")
        except urllib.error.HTTPError:
            print("FALLITO")


if __name__ == "__main__":
    main()
