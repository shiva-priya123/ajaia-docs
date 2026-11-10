# AI-Native Workflow Note

## Tools

**Claude, in Anthropic's Cowork mode,** was the only AI tool. It worked as an agent with access to my project folder: it read files, ran commands, wrote code, ran the test suites, and drove a headless browser to check the UI. I directed the work, reviewed the changes and made the product calls.

## Where AI materially sped things up

- **Reviewing the first-pass scaffold.** It read the design docs and the existing backend and listed concrete defects with file-level evidence before anything was built on top of them. That was faster than a manual audit, and it caught issues I'd likely have hit later in deployment.
- **Boilerplate-heavy, well-specified code.** Pydantic schemas, typed API clients, React components with consistent Tailwind styling, and test scaffolding. These are cases where the spec is clear and the main risk is typos.
- **The HTML → TipTap converter.** Mapping python-markdown and mammoth output onto the editor schema is fiddly: whitespace collapsing, the rule that a list item must start with a paragraph, no empty text nodes. AI produced a working first version quickly, and tests pinned down the edge cases.
- **Verification at a scale I wouldn't do by hand.** A Playwright script with three simultaneous users, a phone-sized viewport and a concurrent-edit conflict ran in seconds and produced screenshots to review.

## What I changed or rejected in AI-generated output

From the initial scaffold:

- **The import converter stripped all formatting.** It flattened Markdown and Word headings and lists into plain paragraphs, which defeats the point of a rich-text editor. It was rewritten around an HTML intermediate with a schema-safe subset.
- **Raw uploads were served from a public `/uploads` route** with no auth check. The route was removed, and raw files are no longer stored.
- **Dependency pins that wouldn't install cleanly.** `passlib` with an unpinned `bcrypt` pulls bcrypt 5, which breaks it. Replaced passlib with bcrypt directly, swapped the unmaintained `python-jose` for PyJWT, and updated the pins to versions with Python 3.11–3.13 wheels.
- **The test suite couldn't even start.** Two `204` delete routes crashed FastAPI at import time.
- **Frontend and backend disagreed on the contract.** Login expected `access_token` while the API returned `token`, and upload expected a Document. On top of that, the 401 interceptor reloaded the page on a *wrong password*, wiping the error message.

During the build, problems that review or testing caught in AI output:

- **Timestamps were emitted without a timezone** (SQLite drops it), so "edited 5m ago" would have been off by the viewer's UTC offset. Fixed at the API boundary.
- **The share dialog was clipped to the header** because the header's `backdrop-filter` became the containing block for a `position: fixed` modal. Caught in screenshot review and fixed with a portal.
- **The mobile editor header overflowed**: the title collapsed to zero width. Spotted in a screenshot.
- **One of the AI's own end-to-end assertions was a false positive.** It checked for the text "Saved", which also matches "Un**saved** changes". The test passed while the save hadn't happened yet. The assertion was tightened to an exact match, and the run repeated, before any results were trusted.
- **Rejected:** keeping hyperlinks as a link mark on import. The editor schema has no link mark yet, and ProseMirror throws on unknown marks, so text-only is the safe choice until links are a real feature.

## How I verified correctness, UX quality and reliability

- **Automated tests:** 60 backend and 14 frontend tests, plus TypeScript strict mode. The tests target behaviour that matters to users: permission boundaries, conflict handling, the auto-save state machine, and formatting preservation on import.
- **A real browser run of every user flow,** with three users at once, against the production build served by FastAPI. The screenshots were reviewed, not just the pass/fail output, which is how the two layout bugs above were found.
- **Deployment checks.** Ran the Dockerfile's build and start steps exactly as written: `npm ci` against the lockfile, the build, a runtime-only install, start on a Render-style `$PORT`, and the health check. Also checked deep-link routing and that the SPA catch-all can't be used for path traversal. Confirmed dependency wheels exist for Windows and Linux on Python 3.11–3.13.
- **Reading the diff, not just the tests.** Tests prove what they assert. Changes were also read for things tests don't catch: what reaches the user, what's stored, and what an unauthenticated caller can reach.

**Rule of thumb I followed:** AI output is a draft until something independent (a test, a type check, a screenshot or a second read) has confirmed it. The bugs above were all plausible-looking code.
