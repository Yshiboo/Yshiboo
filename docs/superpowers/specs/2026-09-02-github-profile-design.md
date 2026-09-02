# Yshiboo GitHub Profile — Design Specification

Date: 2026-09-02

## Goal

Turn the GitHub profile into a living "cultivation" system rather than a static portfolio image.

The visual metaphor is:

**idea → cultivation → growth → harvest**

The page keeps GitHub's live character. Decorative artwork provides identity; real GitHub data drives the activity field and project content.

## Visual direction

- Light, airy, spring-like palette.
- Main colors: grass green, sky blue, warm sunlight yellow, small wheat-gold accents.
- Avoid dark-mode dashboard styling.
- Avoid large static hero artwork and rigid card-heavy layouts.
- The README should feel spacious and organic rather than like a product dashboard.

## Sky

The top visual contains only environmental atmosphere:

- daytime: sun, clouds, breeze / drifting leaves;
- nighttime: moon, stars, softer night breeze;
- no profile introduction inside the sky;
- no large project or process illustrations inside the sky.

The line **“春种一粒粟，秋收万颗子。”** appears as a small, understated footer line rather than the main headline.

## Projects

Project content must come from the user's real GitHub repositories.

The current repositories visible to the connected account are:

- my_resume
- mlpractical
- intelligentHR
- iHR
- ihhr
- ai-literacy

All are currently private. The public profile must not expose private repository names, commit titles, PR titles, issue bodies, or internal metadata unless the user explicitly chooses to publish them.

Therefore the first implementation will keep the project section privacy-safe. Public project cards are added only for projects the user explicitly approves for public display.

## Activity field

The custom activity visualization is the core interaction.

It does **not** replace or modify GitHub's native contribution graph. Instead, the README renders a separate SVG driven by the user's contribution data.

Each day maps to one plant state:

- 0 contributions: bare soil / empty plot
- low activity: seed
- light activity: sprout
- medium activity: leafy growth
- high activity: millet / wheat-like mature plant

The mapping is based on contribution intensity for that day, not simply on chronological position. A heavily active day can mature into a tall plant even if the days before it were quiet.

A watering can visually waters the activity field. Water is a metaphor for ongoing work, not a separate static explanatory block.

## Dynamic rendering

One canonical renderer owns all generated visual state.

Files:

- `README.md` — composition only
- `scripts/render_profile.py` — canonical data-to-SVG renderer
- `assets/sky.svg` — generated sky
- `assets/garden.svg` — generated activity field
- `.github/workflows/render-profile.yml` — scheduled regeneration

The renderer is responsible for both sky and garden generation so there is no second implementation of the same visual logic.

## Day / night behavior

The workflow regenerates the sky on a schedule.

Initial rule:

- 06:00–18:00 Europe/London → daytime sky
- 18:00–06:00 Europe/London → nighttime sky

The implementation may later switch to sunrise/sunset data, but the first version keeps the logic deterministic and self-contained.

## GitHub data

The activity renderer should use GitHub contribution counts where available.

Private contribution privacy is preserved:

- contribution intensity may be displayed;
- private repository names and private activity details are not embedded in public generated assets;
- no secrets or private repository contents are written to the public profile repository.

## README layout

1. Dynamic sky
2. Compact public project area
3. Dynamic cultivation / activity field
4. Small tech-stack area
5. Minimal closing line: “春种一粒粟，秋收万颗子。”

The README should remain usable on desktop and mobile. SVGs must scale responsively.

## Non-goals

- Rebuilding GitHub's whole profile UI.
- Replacing GitHub's native contribution graph.
- Publishing private repository information.
- Heavy animations or a large JavaScript frontend.
- External always-on server dependency.
- Multiple competing generators for the same visual.

## Implementation quality bar

- One renderer owns dynamic profile generation.
- Generated SVGs are deterministic for the same input.
- No private metadata leaks into the public repository.
- Workflow failures leave the previous generated assets intact.
- README remains readable if generated assets fail to load.
