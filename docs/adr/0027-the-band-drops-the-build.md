# ADR-0027 — the band drops the build

- **Status:** accepted, 2026-10-20
- **Ticket:** #316
- **Supersedes:** [ADR-0008](0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)'s
  amendment of 2026-09-30, where it puts the build on the band
- **Related:** [ADR-0023](0023-the-chrome-comes-from-look.md) (the chrome
  comes from look)

## Context

ADR-0008's amendment of 2026-09-30 puts the **build** and the **link** on the
band. #301 draws the build beside the link's `look-dot` while the station is
answering.

How the band fits a narrow screen is look's (ADR-0023). On a narrow band look
cuts the build short with "…", so the band shows part of a commit.

The releases view shows the build as well, and marks the **release** whose
**tag** matches it.

## Decision

**d.1** The band does not carry the build. The link's dot carries no text
while the station is answering, and `dcc-ex offline` while it is not.

**d.2** The build is the releases view's. What it is and when it is blank
stay as ADR-0008 d.3 says.

## Consequences

- The band shows nothing that look has to cut short at a phone's width.
- An operator reads the build in the releases view, one press away on the
  rail.
