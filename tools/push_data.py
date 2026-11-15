#!/usr/bin/env python3
"""Publish the movie catalog to the PRIVATE repo mdsegalo/movies-data at data/movies.json.

The app (with a sync token) reads that file on open. Local clone: /workspace/movies/data-repo.

  python3 push_data.py                         # publish /workspace/movies/movies.json
  python3 push_data.py --file other.json -m "Add 10 reserve picks"

Checks before pushing: valid JSON; every id in family/reserve/solo/soloReserve exists in catalog with
t, y, r, g, why, note, s (list), disc; no id repeated across lists. Pulls with rebase first (the phone
commits state.json through the API). Never writes to the public app repo.
"""
import argparse, datetime as dt, json, os, shutil, subprocess, sys

REPO, CLONE = "mdsegalo/movies-data", "/workspace/movies/data-repo"
SRC = "/workspace/movies/movies.json"
FIELDS = ("t", "y", "r", "g", "why", "note", "s", "disc")


def git(*a, check=True):
    r = subprocess.run(["git", "-C", CLONE, *a], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(a)} failed: {r.stderr.strip()[:400]}")
    return r


def validate(doc):
    cat = doc.get("catalog") or {}
    seen = {}
    for lst in ("family", "reserve", "solo", "soloReserve"):
        for i in doc.get(lst) or []:
            if i not in cat:
                raise SystemExit(f"{lst}: id {i} missing from catalog")
            miss = [f for f in FIELDS if f not in cat[i]]
            if miss:
                raise SystemExit(f"{i}: missing fields {miss}")
            if not isinstance(cat[i]["s"], list):
                raise SystemExit(f"{i}: 's' must be a list")
            if i in seen:
                raise SystemExit(f"{i} is in both {seen[i]} and {lst}")
            seen[i] = lst
    return {k: len(doc.get(k) or []) for k in ("family", "reserve", "solo", "soloReserve")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=SRC)
    ap.add_argument("-m", "--message")
    a = ap.parse_args()
    with open(a.file) as f:
        doc = json.load(f)
    counts = validate(doc)
    if not os.path.isdir(os.path.join(CLONE, ".git")):
        r = subprocess.run(["gh", "repo", "clone", REPO, CLONE, "--", "-q"], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("clone failed: " + r.stderr.strip()[:400])
    git("pull", "--rebase", "-q", check=False)
    os.makedirs(os.path.join(CLONE, "data"), exist_ok=True)
    shutil.copyfile(a.file, os.path.join(CLONE, "data", "movies.json"))
    git("add", "data/movies.json")
    if not git("status", "--porcelain").stdout.strip():
        print("No change.", counts)
        return 0
    git("commit", "-q", "-m", a.message or f"movies {dt.date.today().isoformat()}")
    for _ in range(3):
        if git("push", "-q", check=False).returncode == 0:
            print("Pushed data/movies.json to", REPO, counts)
            return 0
        git("pull", "--rebase", "-q", check=False)
    raise SystemExit("push failed after retries")


if __name__ == "__main__":
    sys.exit(main())
