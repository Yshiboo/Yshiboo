# Dynamic Cultivation GitHub Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved light, living GitHub Profile README with a day/night sky, real GitHub contribution data rendered as a seed-to-millet activity field, real project names, a compact tech stack, and a privacy-safe contribution summary.

**Architecture:** `README.md` owns composition only. One Python renderer fetches/parses the public GitHub contribution calendar, computes privacy-safe metrics, and generates the sky, garden, and activity-summary SVGs. GitHub Actions runs the renderer hourly and commits changed generated assets only after a successful render.

**Tech Stack:** Python 3.12 standard library, SVG, GitHub Actions YAML, GitHub-flavored Markdown/HTML.

**Spec:** `docs/superpowers/specs/2026-09-02-github-profile-design.md`

## Global Constraints

- Light, airy, spring-like palette.
- Day is 06:00–18:00 Europe/London; night is 18:00–06:00 Europe/London.
- Activity states map GitHub intensity levels 0–4 to bare soil, seed, sprout, leafy plant, mature millet.
- Private commit messages, PR/issue titles, branch names, internal paths, and other private-repository details must never be written to the public profile repository.
- Public project names are `ihhr`, `ai-literacy`, and `mlpractical`.
- One canonical renderer owns contribution parsing, plant-state mapping, and derived metrics.
- Generated SVGs must be deterministic for the same input.
- Workflow failure must preserve the previous generated assets.
- No external always-on rendering server.
- No fabricated stars, forks, contribution counts, or repository names.

---

## File Structure

- `README.md` — GitHub README composition, project list, tech-stack copy, generated asset embeds.
- `scripts/render_profile.py` — single canonical renderer: fetch, parse, metrics, day/night state, SVG generation, atomic writes.
- `assets/sky.svg` — generated environment header.
- `assets/garden.svg` — generated contribution cultivation field.
- `assets/activity-summary.svg` — generated privacy-safe contribution summary.
- `tests/test_render_profile.py` — deterministic unit tests for all renderer behavior.
- `tests/fixtures/contributions.html` — small offline GitHub contribution-calendar fixture.
- `.github/workflows/render-profile.yml` — manual/hourly render workflow.

### Task 1: Contribution data model and parser

**Files:**
- Create: `scripts/render_profile.py`
- Create: `tests/test_render_profile.py`
- Create: `tests/fixtures/contributions.html`

**Interfaces:**
- Produces: `ContributionDay(date: datetime.date, level: int)`
- Produces: `parse_contribution_html(html: str) -> list[ContributionDay]`
- Produces: `fetch_contribution_html(username: str, start: date, end: date) -> str`

- [ ] **Step 1: Write the offline fixture**

Create `tests/fixtures/contributions.html` with representative GitHub calendar cells:

```html
<table>
  <tbody>
    <tr>
      <td class="ContributionCalendar-day" data-date="2026-08-30" data-level="0"></td>
      <td class="ContributionCalendar-day" data-date="2026-08-31" data-level="1"></td>
      <td class="ContributionCalendar-day" data-date="2026-09-01" data-level="3"></td>
      <td class="ContributionCalendar-day" data-date="2026-09-02" data-level="4"></td>
    </tr>
  </tbody>
</table>
```

- [ ] **Step 2: Write failing parser tests**

```python
from datetime import date
from pathlib import Path
from scripts.render_profile import ContributionDay, parse_contribution_html

FIXTURE = Path("tests/fixtures/contributions.html")

def test_parse_contribution_html_reads_date_and_level():
    days = parse_contribution_html(FIXTURE.read_text(encoding="utf-8"))
    assert days == [
        ContributionDay(date(2026, 8, 30), 0),
        ContributionDay(date(2026, 8, 31), 1),
        ContributionDay(date(2026, 9, 1), 3),
        ContributionDay(date(2026, 9, 2), 4),
    ]

def test_parse_contribution_html_rejects_empty_calendar():
    try:
        parse_contribution_html("<html></html>")
    except ValueError as exc:
        assert "contribution calendar" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 3: Run tests and verify failure**

Run: `python -m unittest tests.test_render_profile -v`

Expected: import/function failures because the renderer does not yet exist.

- [ ] **Step 4: Implement the minimal parser and fetcher**

Use standard-library `html.parser.HTMLParser`, `urllib.request`, and an immutable dataclass:

```python
@dataclass(frozen=True, order=True)
class ContributionDay:
    date: date
    level: int
```

The parser accepts only `data-level` values 0–4 and sorts by date.

The fetch URL is:

```text
https://github.com/users/{username}/contributions?from={YYYY-MM-DD}&to={YYYY-MM-DD}
```

Use a short timeout and a normal browser-like `User-Agent`.

- [ ] **Step 5: Run tests and verify pass**

Run: `python -m unittest tests.test_render_profile -v`

Expected: parser tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/render_profile.py tests/test_render_profile.py tests/fixtures/contributions.html
git commit -m "feat: parse GitHub contribution calendar"
```

### Task 2: Canonical plant-state mapping and contribution metrics

**Files:**
- Modify: `scripts/render_profile.py`
- Modify: `tests/test_render_profile.py`

**Interfaces:**
- Consumes: `ContributionDay`
- Produces: `plant_state(level: int) -> str`
- Produces: `ContributionMetrics(active_days_month: int, current_streak: int, harvest_days_month: int, active_days_year: int)`
- Produces: `summarize_contributions(days: Sequence[ContributionDay], today: date) -> ContributionMetrics`

- [ ] **Step 1: Write failing mapping and summary tests**

```python
def test_plant_state_maps_github_levels():
    assert [plant_state(i) for i in range(5)] == [
        "soil", "seed", "sprout", "leafy", "millet"
    ]

def test_summarize_contributions_uses_real_levels():
    days = [
        ContributionDay(date(2026, 8, 31), 1),
        ContributionDay(date(2026, 9, 1), 3),
        ContributionDay(date(2026, 9, 2), 4),
    ]
    metrics = summarize_contributions(days, date(2026, 9, 2))
    assert metrics.active_days_month == 2
    assert metrics.current_streak == 3
    assert metrics.harvest_days_month == 1
    assert metrics.active_days_year == 3
```

- [ ] **Step 2: Run targeted tests and verify failure**

Run: `python -m unittest tests.test_render_profile -v`

Expected: missing function failures.

- [ ] **Step 3: Implement the single mapping table and summary logic**

Use exactly one mapping:

```python
PLANT_STATES = {
    0: "soil",
    1: "seed",
    2: "sprout",
    3: "leafy",
    4: "millet",
}
```

A streak counts consecutive calendar days ending at `today` whose level is greater than zero.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m unittest tests.test_render_profile -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/render_profile.py tests/test_render_profile.py
git commit -m "feat: derive cultivation states and activity metrics"
```

### Task 3: Deterministic garden SVG renderer

**Files:**
- Modify: `scripts/render_profile.py`
- Modify: `tests/test_render_profile.py`
- Create: `assets/garden.svg`

**Interfaces:**
- Consumes: ordered `ContributionDay` values
- Produces: `render_garden_svg(days: Sequence[ContributionDay], width: int = 760, height: int = 470) -> str`

- [ ] **Step 1: Write failing SVG tests**

```python
def test_garden_svg_contains_month_and_weekday_labels():
    svg = render_garden_svg([
        ContributionDay(date(2026, 9, 1), 3),
        ContributionDay(date(2026, 9, 2), 4),
    ])
    assert "<svg" in svg
    assert "Sep" in svg
    assert "Mon" in svg
    assert "Wed" in svg
    assert "Fri" in svg

def test_garden_svg_renders_distinct_growth_states():
    svg = render_garden_svg([
        ContributionDay(date(2026, 8, 30), 0),
        ContributionDay(date(2026, 8, 31), 1),
        ContributionDay(date(2026, 9, 1), 2),
        ContributionDay(date(2026, 9, 2), 3),
        ContributionDay(date(2026, 9, 3), 4),
    ])
    for marker in ["state-soil", "state-seed", "state-sprout", "state-leafy", "state-millet"]:
        assert marker in svg

def test_garden_svg_is_deterministic():
    days = [ContributionDay(date(2026, 9, 2), 4)]
    assert render_garden_svg(days) == render_garden_svg(days)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_render_profile -v`

Expected: renderer missing.

- [ ] **Step 3: Implement the visual grammar**

Use only SVG primitives so the asset is self-contained:

- pale soil baseline;
- week columns horizontally;
- weekday rows vertically;
- seed as a small brown ellipse;
- sprout as a short stem + two leaves;
- leafy plant as a taller stem + four leaves;
- millet as a tall green stem + gold grain head;
- watering can in the lower-left with water arcs landing on the field;
- month labels calculated from real dates;
- legend: soil → seed → sprout → leafy → millet.

Every plant group gets a `data-state` marker or class-like `id` string used by tests.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m unittest tests.test_render_profile -v`

Expected: PASS.

- [ ] **Step 5: Generate the first garden asset from fixture data**

Run:

```bash
python scripts/render_profile.py --contributions-html tests/fixtures/contributions.html --now 2026-09-02T12:00:00+01:00 --output-dir assets
```

Expected: `assets/garden.svg` exists and is valid UTF-8 SVG.

- [ ] **Step 6: Commit**

```bash
git add scripts/render_profile.py tests/test_render_profile.py assets/garden.svg
git commit -m "feat: render contribution garden"
```

### Task 4: Day/night sky renderer

**Files:**
- Modify: `scripts/render_profile.py`
- Modify: `tests/test_render_profile.py`
- Create: `assets/sky.svg`

**Interfaces:**
- Produces: `sky_mode(now: datetime) -> Literal["day", "night"]`
- Produces: `render_sky_svg(now: datetime, width: int = 1200, height: int = 320) -> str`

- [ ] **Step 1: Write failing day/night tests**

```python
from datetime import datetime
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")

def test_sky_mode_switches_at_six():
    assert sky_mode(datetime(2026, 9, 2, 5, 59, tzinfo=LONDON)) == "night"
    assert sky_mode(datetime(2026, 9, 2, 6, 0, tzinfo=LONDON)) == "day"
    assert sky_mode(datetime(2026, 9, 2, 17, 59, tzinfo=LONDON)) == "day"
    assert sky_mode(datetime(2026, 9, 2, 18, 0, tzinfo=LONDON)) == "night"

def test_day_sky_has_sun_and_clouds():
    svg = render_sky_svg(datetime(2026, 9, 2, 12, 0, tzinfo=LONDON))
    assert "sky-sun" in svg
    assert "sky-cloud" in svg
    assert "sky-moon" not in svg

def test_night_sky_has_moon():
    svg = render_sky_svg(datetime(2026, 9, 2, 23, 0, tzinfo=LONDON))
    assert "sky-moon" in svg
    assert "sky-sun" not in svg
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_render_profile -v`

Expected: sky functions missing.

- [ ] **Step 3: Implement day and night from one render function**

Day:
- very light blue vertical gradient;
- warm yellow sun near upper-right;
- soft white cloud groups;
- thin breeze curves;
- a few green leaves;
- grass and small flowers only at the lower edge.

Night:
- muted blue gradient;
- pale moon in the same visual anchor as the sun;
- sparse stars;
- softer clouds and breeze;
- same lower-edge grass silhouette.

No text is embedded into `sky.svg`.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m unittest tests.test_render_profile -v`

Expected: PASS.

- [ ] **Step 5: Generate initial sky asset**

Run:

```bash
python scripts/render_profile.py --contributions-html tests/fixtures/contributions.html --now 2026-09-02T12:00:00+01:00 --output-dir assets
```

Expected: `assets/sky.svg` contains `sky-sun`.

- [ ] **Step 6: Commit**

```bash
git add scripts/render_profile.py tests/test_render_profile.py assets/sky.svg
git commit -m "feat: add dynamic day and night sky"
```

### Task 5: Privacy-safe contribution summary SVG

**Files:**
- Modify: `scripts/render_profile.py`
- Modify: `tests/test_render_profile.py`
- Create: `assets/activity-summary.svg`

**Interfaces:**
- Consumes: `ContributionMetrics`
- Produces: `render_activity_summary_svg(metrics: ContributionMetrics, month_label: str) -> str`

- [ ] **Step 1: Write failing summary SVG test**

```python
def test_activity_summary_uses_metrics_without_private_metadata():
    metrics = ContributionMetrics(
        active_days_month=12,
        current_streak=4,
        harvest_days_month=3,
        active_days_year=91,
    )
    svg = render_activity_summary_svg(metrics, "September 2026")
    assert "12 active days" in svg
    assert "4 day streak" in svg
    assert "3 harvest days" in svg
    assert "91 active days this year" in svg
    assert "commit" not in svg.lower()
    assert "pull request" not in svg.lower()
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_render_profile -v`

Expected: missing renderer.

- [ ] **Step 3: Implement compact summary card**

Render four short metric rows with small plant-themed marks. Do not include repo names or private activity titles.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m unittest tests.test_render_profile -v`

Expected: PASS.

- [ ] **Step 5: Generate asset and commit**

```bash
python scripts/render_profile.py --contributions-html tests/fixtures/contributions.html --now 2026-09-02T12:00:00+01:00 --output-dir assets
git add scripts/render_profile.py tests/test_render_profile.py assets/activity-summary.svg
git commit -m "feat: add privacy-safe activity summary"
```

### Task 6: README composition matching the approved reference

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: `assets/sky.svg`, `assets/garden.svg`, `assets/activity-summary.svg`
- Produces: public GitHub profile README layout

- [ ] **Step 1: Create the README with the approved hierarchy**

Use:

```markdown
<p align="center">
  <img src="./assets/sky.svg" width="100%" alt="A living sky that changes from sun to moon with London time" />
</p>

<table>
<tr>
<td width="24%" valign="top">

### 🌿 Projects I'm Building

**ihhr**  
Intelligent HR system, current product line.

**ai-literacy**  
AI-literacy and Next Token Lab research work.

**mlpractical**  
Machine-learning practical work.

</td>
<td width="52%" valign="top">

### 🌱 Activity

<img src="./assets/garden.svg" width="100%" alt="GitHub contribution activity shown as seeds, sprouts, plants and millet" />

</td>
<td width="24%" valign="top">

### 🌿 Tech Stack

`Python` · `TypeScript` · `React`  
`FastAPI` · `PostgreSQL`  
`Docker` · `Git`

### 〽️ Contribution activity

<img src="./assets/activity-summary.svg" width="100%" alt="Privacy-safe GitHub contribution summary" />

</td>
</tr>
</table>

<p align="center"><sub>春种一粒粟，秋收万颗子。</sub></p>
```

Repository names are intentionally plain text in v1 because the repositories are private and public links would return 404 to visitors.

- [ ] **Step 2: Validate forbidden private details are absent**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path("README.md").read_text()
for forbidden in ["pull request #", "Merge pull request", "fix(ci):", "codex/"]:
    assert forbidden not in text
print("privacy check passed")
PY
```

Expected: `privacy check passed`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "feat: compose cultivation profile README"
```

### Task 7: Scheduled GitHub Actions regeneration

**Files:**
- Create: `.github/workflows/render-profile.yml`
- Modify: `scripts/render_profile.py`
- Modify: `tests/test_render_profile.py`

**Interfaces:**
- CLI: `python scripts/render_profile.py --username Yshiboo --output-dir assets`
- Optional deterministic test inputs: `--contributions-html PATH`, `--now ISO8601`

- [ ] **Step 1: Add CLI test**

```python
def test_cli_writes_all_assets_to_temp_directory():
    # invoke main([...]) against the fixture and fixed London timestamp
    # assert sky.svg, garden.svg, activity-summary.svg all exist
```

Implement this test with `tempfile.TemporaryDirectory` and direct `main([...])` invocation, not a subprocess.

- [ ] **Step 2: Implement atomic asset writes**

Render all three SVG strings in memory first.

Write each to `*.tmp`, then replace the target files only after all rendering and parsing succeeds. If fetch/parse/render raises, no existing generated asset is replaced.

- [ ] **Step 3: Run the full test suite**

Run: `python -m unittest tests.test_render_profile -v`

Expected: all tests PASS.

- [ ] **Step 4: Create the workflow**

```yaml
name: Render profile

on:
  workflow_dispatch:
  schedule:
    - cron: "17 * * * *"

permissions:
  contents: write

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Render dynamic profile assets
        run: python scripts/render_profile.py --username Yshiboo --output-dir assets

      - name: Commit changed assets
        run: |
          if git diff --quiet -- assets; then
            echo "No generated changes."
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add assets
          git commit -m "chore: refresh profile garden"
          git push
```

- [ ] **Step 5: Validate YAML and renderer locally**

Run:

```bash
python -m unittest tests.test_render_profile -v
python scripts/render_profile.py --contributions-html tests/fixtures/contributions.html --now 2026-09-02T12:00:00+01:00 --output-dir assets
git diff --check
```

Expected: tests PASS, renderer exits 0, `git diff --check` has no output.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/render-profile.yml scripts/render_profile.py tests/test_render_profile.py assets
git commit -m "ci: refresh dynamic profile hourly"
```

### Task 8: Final verification against the approved design

**Files:**
- Review: `README.md`
- Review: `assets/sky.svg`
- Review: `assets/garden.svg`
- Review: `assets/activity-summary.svg`
- Review: `.github/workflows/render-profile.yml`

**Interfaces:**
- Final public output: `https://github.com/Yshiboo`

- [ ] **Step 1: Run all automated checks**

```bash
python -m unittest tests.test_render_profile -v
git diff --check
```

Expected: all tests PASS, no whitespace errors.

- [ ] **Step 2: Run day and night deterministic renders**

```bash
rm -rf /tmp/profile-day /tmp/profile-night
python scripts/render_profile.py --contributions-html tests/fixtures/contributions.html --now 2026-09-02T12:00:00+01:00 --output-dir /tmp/profile-day
python scripts/render_profile.py --contributions-html tests/fixtures/contributions.html --now 2026-09-02T23:00:00+01:00 --output-dir /tmp/profile-night
grep -q "sky-sun" /tmp/profile-day/sky.svg
grep -q "sky-moon" /tmp/profile-night/sky.svg
```

Expected: all commands exit 0.

- [ ] **Step 3: Verify public-repository privacy boundary**

Run:

```bash
grep -RniE "Merge pull request|fix\(ci\)|codex/|proof-cashier|PR #[0-9]+" README.md assets scripts .github || true
```

Expected: no private activity text in README or generated assets. Test fixture/source comments must not contain real private text either.

- [ ] **Step 4: Trigger `Render profile` manually on GitHub**

Expected:
- workflow succeeds;
- generated asset commit appears only if assets changed;
- README renders on the profile;
- day/night sky matches London time;
- garden reflects the public contribution-calendar intensity levels.

- [ ] **Step 5: Compare visually with the approved reference**

Acceptance criteria:
- sky is the dominant top element;
- no intro/process cards;
- project list left, activity center, stack/activity summary right;
- watering can waters the activity field;
- activity cells are plant states rather than green squares;
- footer poem is small;
- layout remains readable on mobile.

- [ ] **Step 6: Final commit if verification required any tiny layout adjustment**

```bash
git add README.md assets scripts .github tests
git commit -m "chore: polish profile layout"
```
