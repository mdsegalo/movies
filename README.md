# Movie Night: Segalo family movie tracker (PWA)

A static, offline-first web app. No build step, no CDNs, relative paths only, so it runs from GitHub Pages
at `https://mdsegalo.github.io/movies/`.

On iPhone: open it in Safari, tap Share, then **Add to Home Screen**. It runs full-screen.

## Tabs
* **Family**: the ranked top 100 to watch. Each card has the title, year, rating, genre, why you'll like it, a parent note
  (scenes worth skipping are flagged "Heads up"), the streaming services and the best disc format (4K UHD, Blu-ray or DVD only).
  Filters: search, decade, genre, streaming service (or "Rent/buy only") and "Disc (Blu-ray+)".
* Tap a movie for details, a JustWatch link and **Mark watched** (date defaults to today, who watched, 1-5 stars, note),
  **Seen already** (goes to Watched with date "earlier") or **Not interested**. Every action has an Undo in the toast.
  When a movie leaves the list, the next movie from the reserve queue fills in, so Family stays at 100 (marked "New pick").
* **Watched**: what you marked in the app (tap to edit or Unwatch, which puts it back on the list), the history from before
  Nov 2026, and "Not interested" movies (tap to bring one back).
* **Solo**: Michael's own list, no content limits.
* **Settings**: sync token, data status, refresh, export backup.

## Files
| File | What it is |
|---|---|
| `index.html` | The whole app: CSS and JS inlined |
| `data/movies.json` | **Demo** catalog (8 family, 3 reserve, 3 solo). The real one lives in the private repo |
| `sw.js` | Service worker: network-first with a 2.5 s timeout, cache fallback offline |
| `manifest.webmanifest`, `icons/` | Install metadata and icons (192, 512, maskable 512, apple-touch 180) |
| `tools/push_data.py` | Publish a new catalog to the private repo (run from the box) |
| `tools/pull_state.py` | Read what the phone marked (state.json) from the private repo |

## Sync token (one time, per device)
Your list and history live in the **private** repo `mdsegalo/movies-data`. The app needs a token that can only touch that repo.

1. On github.com go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**
   (direct link: https://github.com/settings/personal-access-tokens/new).
2. Name: `movies app`. Expiration: your choice (1 year is fine).
3. Resource owner: **mdsegalo**. Repository access: **Only select repositories → mdsegalo/movies-data**.
4. Permissions → Repository permissions → **Contents: Read and write** (Metadata: Read-only is added automatically). Nothing else.
5. Generate, copy the `github_pat_…` token.
6. In the app: **Settings → paste the token → Save → Test sync**. It should say "Sync works ✓" and the Family tab shows your full 100.

The token is stored only in this device's localStorage (`movies_gh_token`), shown masked, and never goes into
backups or state.json. **Remove token** wipes it and the cached private list, and the app goes back to demo mode.
Use the same token on each device (phone, iPad); they merge through the repo.

## Data model
`data/movies.json` (private repo; same shape as the demo here):
```json
{
  "schema": 1, "updated": "2026-11-14", "streamingAsOf": "2026-11-14", "familySize": 100,
  "family": ["raiders-of-the-lost-ark-1981", "..."],      // ranked order
  "reserve": ["indiana-jones-and-the-temple-of-doom-1984"], // backfill queue, in order
  "solo": ["the-shawshank-redemption-1994"], "soloReserve": [],
  "seedWatched": [{ "id": "seed-top-gun-1986", "t": "Top Gun", "y": "1986", "date": "Before Nov 2026", "note": "" }],
  "catalog": { "<id>": { "id": "...", "t": "Title", "y": 1981, "r": "PG", "g": "Adventure", "why": "...", "note": "...",
                         "s": ["Prime Video", "Paramount+"], "disc": "4K UHD", "jw": "https://www.justwatch.com/us/movie/..." } }
}
```
* The Family tab shows `family` then `reserve`, skipping anything marked, capped at `familySize`. To add picks, append ids to
  `reserve` (and their entries to `catalog`) and run `tools/push_data.py`. Never rename an id: marks key off it.
* `s` is the US subscription/free/library services from JustWatch (empty = rent/buy only). Free = ad-supported apps
  (Tubi, Pluto, Roku Channel, YouTube free, Plex). Kanopy and Hoopla work with a library card. `disc` is the best format
  listed for sale (`4K UHD`, `Blu-ray`, `DVD only`, or `check`).

`state.json` (private repo, written by the app):
```json
{ "app": "movies", "version": "1.0.0", "exported": "...",
  "marks": { "<id>": { "st": "w|s|x|h|null", "date": "2026-11-14|earlier", "who": "Family", "stars": 5, "note": "", "list": "family", "t": "...", "y": 1981, "at": 1763164800000 } },
  "watched": [ ... ], "notInterested": [ ... ] }
```
`st`: `w` watched, `s` seen already, `x` not interested, `h` hidden history row, `null` undone. Devices merge per id
(the newer `at` wins). `watched` and `notInterested` are convenience lists for reading.

## Sync behavior
About 4 s after any change, the app GETs `state.json`, merges, and PUTs it if anything differs (coalesced; one commit
per burst, message `sync YYYY-MM-DD`). sha conflicts (409/422) refetch and retry. Offline or on failure the change stays
queued and retries on `online`, on open and on returning to the app (backoff 30 s → 15 min). On open it also pulls
`state.json` so another device's marks show up.

## Updating the app
Edit `index.html` and bump `VERSION` in `sw.js` so installed phones refresh. Pages serves from `main` / root.
