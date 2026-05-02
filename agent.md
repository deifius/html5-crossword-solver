# AGENT.md — INASRA Solver Development Guide

This repository is being adapted from the Crossword Nexus HTML5 Solver into the public solving surface for INASRA-generated crosswords.

The goal is not to turn the solver into the INASRA builder. The goal is to make this solver a stable, themed, embeddable, public-facing runtime for finished INASRA crossword artifacts.

## Core product direction

INASRA builds puzzles client-side in JavaScript. When a user chooses to publish or share a finished puzzle, the browser sends a completed puzzle snapshot to the INASRA server. The server stores that snapshot and returns a stable public solving URL.

Canonical public URLs should look like:

```text
https://inasra.me/<username>/solve/<public_puzzle_id>
```

Example:

```text
https://inasra.me/dafe/solve/xw_01jzn7w9k3p7m8q4v2fxh6n
```

The `<public_puzzle_id>` must be opaque. It must not contain the seed, the title answer, 1-Across, or any answer-derived slug. A URL should never spoil the puzzle.

## Development principles

### Keep the solver runtime small and boring

The solver should remain mostly a puzzle player. Do not move the INASRA construction engine into this repo unless there is a clear reason.

Prefer:

- small loader hooks
- CSS/theme overrides
- optional INASRA boot scripts
- read-only wallpaper manifests
- stable public puzzle fetch routes

Avoid:

- rewriting the crossword engine unnecessarily
- entangling builder state with public solving state
- adding a heavy JavaScript build system unless the project truly needs one

### Preserve upstream solver behavior where practical

The existing solver can already load puzzle files with `?file=...` and can initialize from JavaScript parameters. Keep those modes working.

INASRA mode should be an additional first-class loading mode, probably driven by a global injected server config:

```js
window.INASRA_SOLVE = {
  username: "dafe",
  puzzleId: "xw_01jzn7w9k3p7m8q4v2fxh6n",
  puzzleUrl: "/api/puzzles/dafe/xw_01jzn7w9k3p7m8q4v2fxh6n.ipuz",
  manifestUrl: "/api/puzzles/dafe/xw_01jzn7w9k3p7m8q4v2fxh6n",
  theme: "inasra"
};
```

The pretty route should not require a `?file=` query string.

### Published puzzles are snapshots

A public puzzle should be treated as a stored artifact:

- IPUZ puzzle data
- public metadata
- INASRA construction metadata
- wallpaper manifest
- owner
- visibility
- revision number

The public solver consumes the stored artifact. It should not depend on the creator's current in-browser builder state.

### Use opaque IDs and non-spoiler metadata

Never expose puzzle answers in:

- public URLs
- filenames
- page titles
- Open Graph metadata
- public dashboard listings
- image alt text
- visible puzzle descriptions

If the original seed/title is spoilery, support a separate public title such as `Untitled INASRA Crossword`, `A Puzzle by <username>`, or a creator-provided non-spoiler title.

### Separate builder metadata from solver metadata

Some metadata is useful to the builder and dashboard but should not be sent to anonymous solvers.

Public solver payloads may include:

- public puzzle title
- author username/display name
- IPUZ URL
- wallpaper manifest
- theme information

Private/owner-only metadata may include:

- seed/source article titles
- construction trace
- relephant sources
- internal clue-generation diagnostics
- draft history

### The Ken Burns wallpaper is a shared visual layer

The solver should support a read-only INASRA wallpaper layer behind the crossword UI.

Recommended structure:

```html
<div id="inasra-wallpaper-layer"></div>
<div class="inasra-solver-shell">
  <!-- existing crossword UI -->
</div>
```

Recommended manifest shape:

```json
{
  "mode": "kenburns",
  "settings": {
    "enabled": true,
    "opacity": 0.32,
    "transition_seconds": 8,
    "hold_seconds": 12,
    "motion": "gentle",
    "fit": "cover"
  },
  "images": [
    {
      "src": "https://example.com/image.webp",
      "thumb": "https://example.com/thumb.webp",
      "alt": "Non-spoiler image description",
      "source_url": "https://example.com/source",
      "license": "unknown"
    }
  ]
}
```

The wallpaper layer must respect `prefers-reduced-motion`. When reduced motion is enabled, avoid pan/zoom animation and use a static image or gentle crossfade.

### CSS should layer, not wrestle

Prefer a dedicated INASRA stylesheet loaded after the upstream solver CSS:

```html
<link rel="stylesheet" href="css/crossword.shared.css">
<link rel="stylesheet" href="css/crossword.mobile.css">
<link rel="stylesheet" href="css/inasra-solver.css">
```

The INASRA stylesheet should override variables and layout affordances rather than patching many upstream selectors. When a selector must be overridden, keep it specific, documented, and minimal.

Visual goals:

- dark cosmic base
- translucent panels
- warm gold/violet/teal accents
- soft glow, not eye-searing glow
- puzzle grid remains legible over wallpaper
- controls remain obvious and keyboard-accessible

### Be suspicious of service workers

The upstream solver includes a service worker. INASRA-hosted solver pages should initially avoid registering it.

If service worker support is reintroduced, use versioned caches and network-first behavior for puzzle API responses.

Stale puzzle data and stale JavaScript are worse than no offline mode.

### Server-side validation is mandatory

Because published puzzles originate from client-side JavaScript, the server must validate incoming payloads.

At minimum, validate:

- user is authenticated
- IPUZ has required fields
- grid dimensions are sane
- JSON payload size is within limits
- clue/title fields are sanitized
- wallpaper image count is capped
- wallpaper URLs are `http` or `https`
- visibility is an allowed value

A malformed puzzle should be rejected politely. A malicious puzzle should not become public content.

### Prefer small, low-story-point changes

Make incremental commits that can be reviewed and tested independently. A good INASRA solver commit usually does one thing:

- add the opaque ID generator
- add the puzzle POST route
- add the solve page route
- add the dashboard list
- add the wallpaper layer
- add the INASRA stylesheet

Avoid "one giant sacred crab of a commit" unless the crab is purely decorative.

## Suggested repository boundaries

This repo should contain solver-facing assets and docs:

```text
index.html
css/crossword.shared.css
css/crossword.mobile.css
css/inasra-solver.css       # new INASRA theme layer
js/crossword.shared.js
js/inasra-solver-boot.js    # new INASRA config/manifest loader
js/inasra-wallpaper.js      # new Ken Burns layer
sample_puzzles/
README.md
TODO.md
AGENT.md
```

The main INASRA app should own:

```text
POST /api/puzzles
GET  /<username>/solve/<public_id>
GET  /api/puzzles/<username>/<public_id>
GET  /api/puzzles/<username>/<public_id>.ipuz
GET  /dashboard/puzzles
PATCH/DELETE puzzle management routes
user identity and authorization
puzzle storage and revisions
```

## Testing expectations

For each meaningful change, test at least one direct solver mode and one INASRA mode.

Manual smoke tests:

1. `index.html?file=sample_puzzles/Route_66.ipuz` still loads.
2. A page with `window.INASRA_SOLVE.puzzleUrl` loads the same puzzle without a query string.
3. The INASRA CSS does not make clue text unreadable.
4. Wallpaper enabled: puzzle remains readable.
5. Wallpaper disabled or absent: solver still works.
6. `prefers-reduced-motion` disables pan/zoom.
7. Public URL contains no answer-derived words.
8. Local progress keys use the public puzzle ID when available.

## Naming conventions

Use `public_id` for the opaque public puzzle identifier.

Use `puzzle_id` only for internal database IDs or local code where ambiguity is impossible.

Use `revision_id` or `revision_number` for stored puzzle versions.

Use `public_title` for the non-spoiler title shown to solvers.

Use `source_title`, `seed`, or `answer` only in owner-only metadata.

## First implementation target

The first working vertical slice should be:

1. Add an INASRA-themed solver shell.
2. Add support for `window.INASRA_SOLVE.puzzleUrl`.
3. Disable service worker registration in hosted INASRA mode.
4. Add server-side storage for published IPUZ snapshots in the main INASRA app.
5. Add `POST /api/puzzles` to publish a puzzle from the client.
6. Add `GET /<username>/solve/<public_id>` to serve the themed solver page.
7. Add `GET /api/puzzles/<username>/<public_id>.ipuz` for puzzle fetches.
8. Add a minimal dashboard for copy/open/unpublish/delete.
9. Add the Ken Burns wallpaper manifest and read-only solver wallpaper layer.

Ship the creature walking. Teach it to recite the Akashic crossword almanac later.
