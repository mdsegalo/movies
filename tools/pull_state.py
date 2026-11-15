#!/usr/bin/env python3
"""Read the phone's watch state from the PRIVATE repo mdsegalo/movies-data (state.json).

Uses `gh api` (logged in as mdsegalo). Saves a copy to /workspace/movies/sync/state.json and prints
what was watched, seen already, and skipped (newest first).

  python3 pull_state.py          # summary
  python3 pull_state.py --json   # raw state.json to stdout
"""
import base64, json, os, subprocess, sys

REPO = "mdsegalo/movies-data"
OUT = "/workspace/movies/sync/state.json"


def main():
    r = subprocess.run(["gh", "api", f"repos/{REPO}/contents/state.json"], capture_output=True, text=True)
    if r.returncode != 0:
        if "Not Found" in r.stderr or "404" in r.stderr:
            print("No state.json yet (the app hasn't synced).")
            return 0
        print("gh api failed:", r.stderr.strip()[:300], file=sys.stderr)
        return 2
    doc = json.loads(base64.b64decode(json.loads(r.stdout)["content"]).decode("utf-8"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    if "--json" in sys.argv:
        print(json.dumps(doc, indent=1, ensure_ascii=False))
        return 0
    w = sorted(doc.get("watched", []), key=lambda x: (x.get("date") != "earlier", x.get("date") or ""), reverse=True)
    print(f"state.json exported {doc.get('exported')} · app {doc.get('version')}")
    print(f"Watched/seen: {len(w)}")
    for x in w:
        stars = "★" * (x.get("stars") or 0)
        print(f"  {x.get('date'):<10} {x.get('t')} ({x.get('y')}) [{x.get('list')}]"
              f"{' seen already' if x.get('seen') else ''} {x.get('who') or ''} {stars} {x.get('note') or ''}".rstrip())
    ni = doc.get("notInterested", [])
    if ni:
        print(f"Not interested: {len(ni)}")
        for x in ni:
            print(f"  {x.get('t')} ({x.get('y')}) [{x.get('list')}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
