# Yshiboo GitHub Profile — Design Specification

Date: 2026-09-02
Status: approved against the final reference image

## Goal

Turn the GitHub profile into a living cultivation system rather than a static portfolio image.

The visual metaphor is:

**work → watering → growth → harvest**

Decorative artwork provides identity. Real GitHub data drives the cultivation field and the activity summary.

## Final visual reference

The approved composition is the final reference image supplied on 2026-09-02.

Inside the Profile README, preserve this hierarchy:

1. a wide, airy sky panel;
2. a three-column content row:
   - left: `Projects I'm Building`;
   - center: `Activity`, dominated by the cultivation field;
   - right: `Tech Stack` above `Contribution activity`;
3. the line **“春种一粒粟，秋收万颗子。”** centered and visually minimized at the bottom.

The surrounding GitHub profile chrome and native profile sidebar remain GitHub-owned. The README does not attempt to redraw them.

## Visual direction

- Light, airy, spring-like palette.
- Main colors: grass green, sky blue, warm sunlight yellow, small wheat-gold accents.
- No dark dashboard styling.
- No large static profile illustration.
- No rigid process cards such as Seed → Water → Sunlight → Harvest.
- No explanatory introduction block.
- The page should feel organic and spacious rather than like a product dashboard.

## Sky

The top visual is environmental atmosphere only.

### Day

- large warm sun;
- soft white clouds;
- very light blue sky;
- a few drifting leaves / wind lines;
- low grass and small flowers along the lower edge.

### Night

- moon instead of sun;
- subdued stars;
- soft clouds;
- night breeze / sparse drifting leaves;
- the same ground silhouette so day and night feel like one world.

No profile bio, project card, process diagram, or large text appears inside the sky.

Day/night state is determined by Europe/London local time:

- 06:00–18:00 → day;
- 18:00–06:00 → night.

## Projects I'm Building

The left column uses the user's actual GitHub repositories rather than invented repositories.

To avoid duplicate generations of the same HR product line, the current canonical public-facing selection is:

- `ihhr` — current HR-system line;
- `ai-literacy` — AI-literacy / Next Token Lab work;
- `mlpractical` — ML practical work.

Older `intelligentHR` and `iHR` repositories are not shown beside `ihhr` by default because they represent earlier versions of the same product line.

The user explicitly asked for the project section to reflect the real GitHub account. Repository names above may therefore be displayed publicly. Private commit titles, issue bodies, PR titles, branch names, internal file names, and other private-repository details remain private.

Each project entry stays compact:
- repository/display name;
- one short neutral description;
- primary technology where known;
- no fabricated stars, forks, or public status.

## Activity field

The custom activity visualization is the core element.

It does not modify GitHub's native contribution graph. The README renders a separate SVG driven by the user's real GitHub contribution calendar.

Each calendar day maps to one plant state based on GitHub contribution intensity:

- level 0 → bare soil;
- level 1 → seed;
- level 2 → sprout;
- level 3 → leafy plant;
- level 4 → mature millet / grain head.

The plant state is determined independently for each day. It is not a fake left-to-right growth animation.

A watering can sits at the lower-left edge of the activity panel and visually waters the field. Water must land on the activity field itself.

The garden preserves GitHub's calendar semantics:
- weeks run horizontally;
- Monday / Wednesday / Friday labels are visible;
- month labels are visible;
- the legend progresses from bare soil to mature grain;
- the visualization is responsive.

## Contribution activity

The right-side `Contribution activity` panel is real but privacy-safe.

Because the user's working repositories are private, the public profile does not expose recent private commit messages or PR/issue titles.

Instead the panel summarizes the same real contribution calendar, for example:
- active days this month;
- current contribution streak;
- high-activity / harvest days this month;
- total active days in the visible year.

These metrics are derived from the contribution levels used by the garden. There is one canonical data source.

## Tech Stack

The right-side `Tech Stack` block is compact and text/icon oriented.

Current stack to display:
- Python
- TypeScript
- React
- FastAPI
- PostgreSQL
- Docker
- Git

Do not add technologies merely to fill space.

## Dynamic rendering

One canonical renderer owns generated visual state and derived contribution metrics.

Files:

- `README.md` — composition and public project/stack copy;
- `scripts/render_profile.py` — canonical contribution fetch/parse, metrics, sky rendering, and garden rendering;
- `assets/sky.svg` — generated sky;
- `assets/garden.svg` — generated activity field;
- `assets/activity-summary.svg` — generated privacy-safe contribution summary;
- `.github/workflows/render-profile.yml` — scheduled/manual regeneration;
- `tests/test_render_profile.py` — deterministic renderer tests;
- `tests/fixtures/contributions.html` — offline contribution-calendar fixture.

There is no second contribution parser or second plant-level mapping elsewhere.

## GitHub contribution data

The renderer uses GitHub's public contribution-calendar endpoint for `Yshiboo` and reads GitHub's own intensity levels.

This keeps the profile secret-free. If GitHub is configured to show private contributions anonymously, those contribution levels can be reflected without publishing the private repository identity.

The renderer never writes private repository metadata into generated assets.

If the contribution endpoint cannot be fetched or parsed, the workflow fails before overwriting the previous generated assets.

## Workflow behavior

GitHub Actions runs:
- manually through `workflow_dispatch`;
- hourly at a non-zero minute to refresh day/night state and contribution data.

The Python renderer resolves Europe/London time internally, including daylight-saving transitions.

The workflow commits generated assets only when their contents changed.

## README layout implementation

GitHub controls README CSS, so the implementation uses supported Markdown/HTML rather than attempting arbitrary page CSS.

The README composition is:

- full-width `assets/sky.svg`;
- a three-column HTML table approximating the approved reference:
  - left project list;
  - center `assets/garden.svg`;
  - right tech stack plus `assets/activity-summary.svg`;
- centered small footer line: “春种一粒粟，秋收万颗子。”

On narrow screens the content must remain readable even if GitHub horizontally compresses the table.

## Non-goals

- Rebuilding GitHub's whole profile UI.
- Replacing or restyling GitHub's native contribution graph.
- Publishing private commit/PR/issue details.
- A large JavaScript frontend.
- An external always-on rendering server.
- Multiple competing generators for the same visual.
- Fake stars, fake contribution counts, or invented repository names.

## Implementation quality bar

- One renderer owns contribution parsing, plant-state mapping, and derived metrics.
- Generated SVGs are deterministic for the same inputs.
- No private metadata leaks into the public profile repository.
- Workflow failure preserves the previous generated assets.
- README remains understandable if a generated asset fails to load.
- Tests cover contribution parsing, level mapping, day/night selection, summary metrics, and deterministic SVG generation.
