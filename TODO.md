# TODO — INASRA Public Crossword Solver Integration

This TODO breaks the larger INASRA publishing and public-solving effort into small, low-story-point pieces. Items are grouped by milestone, but each checkbox should be small enough to become its own commit or pull request.

## Milestone 0 — Repo orientation and safety rails

- [x] Add `AGENT.md` describing INASRA solver development conventions.
- [x] Update `README.md` with the intended INASRA publishing architecture.
- [x] Add this TODO checklist.
- [x] Identify every place where `sw.js` is registered.
- [x] Document current solver loading modes: `?file=...`, URL hash, direct JS init.
- [x] Add a simple sample INASRA config object to documentation.

## Milestone 1 — Opaque public puzzle IDs

- [ ] Add an opaque public ID generator in the main INASRA app.
- [ ] Ensure public IDs are not based on seed/title/answer text.
- [ ] Decide ID format: `xw_<ULID>` for v1 unless there is a strong reason otherwise.
- [ ] Add validation tests confirming generated IDs contain no answer-derived slug.
- [ ] Add a server helper that builds canonical solve URLs from username + public ID.

## Milestone 2 — Server-side published puzzle storage

- [ ] Add a `puzzles` table/model.
- [ ] Add a `puzzle_revisions` table/model, even if v1 only uses one revision.
- [ ] Store owner user ID, public ID, public title, visibility, and timestamps.
- [ ] Store IPUZ JSON in a revision record.
- [ ] Store INASRA metadata JSON in a revision record.
- [ ] Store wallpaper manifest JSON in a revision record.
- [ ] Add a migration for the new tables.
- [ ] Add basic model tests.

## Milestone 3 — Publish API

- [ ] Add `POST /api/puzzles` for logged-in users.
- [ ] Validate required IPUZ fields.
- [ ] Reject oversized JSON payloads.
- [ ] Sanitize public title and clue strings.
- [ ] Limit wallpaper image count.
- [ ] Validate wallpaper URLs are `http` or `https`.
- [ ] Assign an opaque `public_id` server-side.
- [ ] Return `{ ok, public_id, solve_url }`.
- [ ] Add tests for success, unauthenticated request, invalid IPUZ, and oversized payload.

## Milestone 4 — Public puzzle fetch API

- [ ] Add `GET /api/puzzles/<username>/<public_id>` for public metadata and manifest.
- [ ] Add `GET /api/puzzles/<username>/<public_id>.ipuz` for the raw IPUZ payload.
- [ ] Make private puzzles inaccessible to anonymous users.
- [ ] Make unlisted puzzles accessible by direct URL.
- [ ] Make public puzzles accessible by direct URL and future listing pages.
- [ ] Add cache headers that do not trap stale puzzle JSON during development.
- [ ] Add tests for visibility rules.

## Milestone 5 — Pretty solve route

- [ ] Add `GET /<username>/solve/<public_id>` in the main INASRA app.
- [ ] Serve the solver shell from that route.
- [ ] Inject `window.INASRA_SOLVE` with `username`, `puzzleId`, `puzzleUrl`, `manifestUrl`, and `theme`.
- [ ] Ensure the HTML title uses a non-spoiler public title.
- [ ] Ensure Open Graph/Twitter metadata contains no answers.
- [ ] Add a smoke test that the pretty route returns the expected config.

## Milestone 6 — Solver boot support

- [x] Add `js/inasra-solver-boot.js`.
- [x] Teach the solver to prefer `window.INASRA_SOLVE.puzzleUrl` when present.
- [x] Preserve existing `?file=...` loading behavior.
- [x] Preserve existing hash/share loading behavior.
- [x] Key local solve progress by `public_id` when available.
- [x] Add a tiny sample hosted-mode HTML page for local testing.
- [ ] Manually smoke test with a sample `.ipuz` file in a browser.

## Milestone 7 — INASRA visual theme

- [x] Add `css/inasra-solver.css`.
- [x] Load INASRA CSS after upstream solver CSS in hosted mode.
- [x] Add a top bar with INASRA branding, public puzzle title, author, and Create link.
- [x] Theme background, panels, clue areas, buttons, and active cells.
- [x] Keep grid and clue text legible over dark backgrounds.
- [x] Verify keyboard focus states remain visible.
- [ ] Check mobile layout in a browser/device after merge.

## Milestone 8 — Ken Burns wallpaper on solver side

- [x] Add `#inasra-wallpaper-layer` behind the solver UI.
- [x] Add `js/inasra-wallpaper.js`.
- [x] Load wallpaper manifest from `window.INASRA_SOLVE.manifestUrl`.
- [x] Support empty/missing wallpaper manifests gracefully.
- [x] Preload the next image before crossfade.
- [x] Add pan/zoom animation with opacity controls.
- [x] Respect `prefers-reduced-motion` by disabling pan/zoom.
- [ ] Add a visible/off toggle if needed for readability.
- [x] Confirm the puzzle remains playable without wallpaper by making wallpaper optional/no-op when missing.


## Milestone 6.5 — First solver-side bite follow-up

- [ ] Open `inasra-example.html` through a local static server and visually inspect desktop behavior.
- [ ] Open `inasra-example.html` on a narrow/mobile viewport and inspect layout.
- [ ] Decide whether the INASRA top bar should be present on embedded iframe solves or only full-page solves.
- [ ] Decide whether the hosted solver should keep the upstream app manifest/PWA behavior disabled permanently.
- [ ] Replace remote sample wallpaper URLs with server-cached images when the backend media cache exists.

## Milestone 9 — Share button in INASRA builder

- [ ] Add a `Share Puzzle` button near export controls.
- [ ] Convert current client-side puzzle state to stable IPUZ before publishing.
- [ ] Collect or generate a non-spoiler public title.
- [ ] Package INASRA metadata separately from public metadata.
- [ ] Package wallpaper manifest with non-spoiler alt text.
- [ ] POST the completed snapshot to `/api/puzzles`.
- [ ] Show returned solve URL.
- [ ] Add Copy URL and Open Solver buttons.
- [ ] Handle publish errors clearly.

## Milestone 10 — Published crossword management

- [ ] Add `/dashboard/puzzles` or equivalent logged-in management page.
- [ ] List owner puzzles with title, visibility, created date, updated date, and solve URL.
- [ ] Add Copy URL action.
- [ ] Add Open Solver action.
- [ ] Add Download IPUZ action.
- [ ] Add visibility toggle: private, unlisted, public.
- [ ] Add Unpublish action.
- [ ] Add Archive/Delete action.
- [ ] Add Replace Published Version action after revision support is stable.

## Milestone 11 — Revisions

- [ ] Treat every replacement as a new `puzzle_revisions` row.
- [ ] Keep `puzzles.current_revision_id` pointing to the active public revision.
- [ ] Add owner-only revision history view.
- [ ] Ask for confirmation before replacing a public version.
- [ ] Preserve stable solve URL across revisions.
- [ ] Consider optional `?r=<revision_number>` support later.

## Milestone 12 — Later niceties

- [ ] Add server-side wallpaper image caching.
- [ ] Add thumbnails for dashboard listings.
- [ ] Add solve counts and completion counts.
- [ ] Add public profile puzzle gallery.
- [ ] Add fork/remix support.
- [ ] Add comments or reactions only after moderation strategy is clear.
- [ ] Revisit service worker support with versioned caches and network-first puzzle APIs.
