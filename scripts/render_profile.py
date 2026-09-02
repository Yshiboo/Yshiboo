from __future__ import annotations

import argparse
import calendar
import html
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, Sequence
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
PLANT_STATES = {
    0: "soil",
    1: "seed",
    2: "sprout",
    3: "leafy",
    4: "millet",
}


@dataclass(frozen=True, order=True)
class ContributionDay:
    date: date
    level: int


@dataclass(frozen=True)
class ContributionMetrics:
    active_days_month: int
    current_streak: int
    harvest_days_month: int
    active_days_year: int


class _ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.days: list[ContributionDay] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        raw_date = attributes.get("data-date")
        raw_level = attributes.get("data-level")
        if raw_date is None or raw_level is None:
            return
        try:
            parsed_date = date.fromisoformat(raw_date)
            level = int(raw_level)
        except (TypeError, ValueError):
            return
        if level not in PLANT_STATES:
            return
        self.days.append(ContributionDay(parsed_date, level))


def parse_contribution_html(source: str) -> list[ContributionDay]:
    parser = _ContributionParser()
    parser.feed(source)
    unique = {day.date: day for day in parser.days}
    days = sorted(unique.values())
    if not days:
        raise ValueError("GitHub contribution calendar contained no contribution days")
    return days


def fetch_contribution_html(username: str, start: date, end: date) -> str:
    url = (
        f"https://github.com/users/{username}/contributions"
        f"?from={start.isoformat()}&to={end.isoformat()}"
    )
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Yshiboo-profile-renderer/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def plant_state(level: int) -> str:
    try:
        return PLANT_STATES[level]
    except KeyError as exc:
        raise ValueError(f"unsupported contribution level: {level}") from exc


def summarize_contributions(
    days: Sequence[ContributionDay], today: date
) -> ContributionMetrics:
    day_map = {item.date: item.level for item in days}
    active_days_month = sum(
        1
        for item in days
        if item.date.year == today.year
        and item.date.month == today.month
        and item.level > 0
    )
    harvest_days_month = sum(
        1
        for item in days
        if item.date.year == today.year
        and item.date.month == today.month
        and item.level == 4
    )
    active_days_year = sum(
        1 for item in days if item.date.year == today.year and item.level > 0
    )

    current_streak = 0
    cursor = today
    while day_map.get(cursor, 0) > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    return ContributionMetrics(
        active_days_month=active_days_month,
        current_streak=current_streak,
        harvest_days_month=harvest_days_month,
        active_days_year=active_days_year,
    )


def _svg_header(width: int, height: int, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{html.escape(title)}">'
    )


def _leaf(cx: float, cy: float, rx: float, ry: float, rotation: float, color: str) -> str:
    return (
        f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
        f'fill="{color}" transform="rotate({rotation:.1f} {cx:.1f} {cy:.1f})"/>'
    )


def _plant_svg(state: str, x: float, baseline: float) -> str:
    if state == "soil":
        return (
            '<g data-state="state-soil">'
            f'<circle cx="{x:.1f}" cy="{baseline-0.8:.1f}" r="0.75" fill="#cdbb8b" opacity="0.28"/>'
            '</g>'
        )
    if state == "seed":
        return (
            '<g data-state="state-seed">'
            f'<ellipse cx="{x:.1f}" cy="{baseline-3:.1f}" rx="2.3" ry="3.2" '
            'fill="#9b642f" transform="rotate(-28)"/>'
            f'<path d="M{x-4:.1f},{baseline:.1f} Q{x:.1f},{baseline-1.4:.1f} {x+4:.1f},{baseline:.1f}" '
            'stroke="#cdbb8b" stroke-width="1" fill="none"/>'
            '</g>'
        )
    if state == "sprout":
        return (
            '<g data-state="state-sprout">'
            f'<path d="M{x:.1f},{baseline:.1f} Q{x-0.5:.1f},{baseline-8:.1f} {x:.1f},{baseline-14:.1f}" '
            'stroke="#5f8f3f" stroke-width="1.7" fill="none" stroke-linecap="round"/>'
            + _leaf(x - 3.0, baseline - 10.0, 3.0, 1.7, -28, "#7fbf4d")
            + _leaf(x + 3.0, baseline - 12.5, 3.0, 1.7, 28, "#6fad44")
            + f'<path d="M{x-5:.1f},{baseline:.1f} Q{x:.1f},{baseline-1.4:.1f} {x+5:.1f},{baseline:.1f}" stroke="#cdbb8b" stroke-width="1" fill="none"/>'
            + '</g>'
        )
    if state == "leafy":
        return (
            '<g data-state="state-leafy">'
            f'<path d="M{x:.1f},{baseline:.1f} Q{x+0.5:.1f},{baseline-13:.1f} {x:.1f},{baseline-24:.1f}" '
            'stroke="#4e8237" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
            + _leaf(x - 3.4, baseline - 8.0, 3.8, 1.8, -30, "#7bb34d")
            + _leaf(x + 3.6, baseline - 12.0, 4.0, 1.9, 28, "#6ea641")
            + _leaf(x - 3.2, baseline - 17.0, 3.6, 1.8, -28, "#83bd51")
            + _leaf(x + 3.2, baseline - 21.0, 3.5, 1.7, 30, "#5f9939")
            + f'<path d="M{x-5:.1f},{baseline:.1f} Q{x:.1f},{baseline-1.3:.1f} {x+5:.1f},{baseline:.1f}" stroke="#cdbb8b" stroke-width="1" fill="none"/>'
            + '</g>'
        )
    if state == "millet":
        grains = "".join(
            f'<ellipse cx="{x + dx:.1f}" cy="{baseline - 28 - i*2.6:.1f}" rx="1.5" ry="2.1" fill="#e0ab28"/>'
            for i, dx in enumerate((0, -1.8, 1.6, -1.4, 1.2, -0.8))
        )
        return (
            '<g data-state="state-millet">'
            f'<path d="M{x:.1f},{baseline:.1f} Q{x+0.8:.1f},{baseline-17:.1f} {x:.1f},{baseline-32:.1f}" '
            'stroke="#4e8237" stroke-width="1.9" fill="none" stroke-linecap="round"/>'
            + _leaf(x - 3.4, baseline - 9.0, 4.0, 1.8, -30, "#769f3d")
            + _leaf(x + 3.6, baseline - 14.0, 4.0, 1.8, 30, "#6f9837")
            + _leaf(x - 3.0, baseline - 20.0, 3.7, 1.7, -28, "#82aa45")
            + grains
            + f'<path d="M{x-5:.1f},{baseline:.1f} Q{x:.1f},{baseline-1.3:.1f} {x+5:.1f},{baseline:.1f}" stroke="#cdbb8b" stroke-width="1" fill="none"/>'
            + '</g>'
        )
    raise ValueError(f"unknown plant state: {state}")


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def render_garden_svg(
    days: Sequence[ContributionDay], width: int = 760, height: int = 470
) -> str:
    if not days:
        raise ValueError("garden requires contribution days")
    ordered = sorted(days)
    first_week = _week_start(ordered[0].date)
    last_week = _week_start(ordered[-1].date)
    week_count = max(1, ((last_week - first_week).days // 7) + 1)

    left = 54.0
    right = 24.0
    top = 92.0
    row_step = 38.0
    grid_width = width - left - right
    col_step = grid_width / max(week_count, 1)

    parts: list[str] = [
        _svg_header(width, height, "GitHub activity garden"),
        '<defs><linearGradient id="garden-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#fbfdf7"/></linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="18" fill="url(#garden-bg)"/>',
        '<text x="24" y="34" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="18" font-weight="650" fill="#274c2e">Activity</text>',
    ]

    seen_months: set[tuple[int, int]] = set()
    for item in ordered:
        key = (item.date.year, item.date.month)
        if key in seen_months:
            continue
        seen_months.add(key)
        week_index = (_week_start(item.date) - first_week).days // 7
        x = left + week_index * col_step
        parts.append(
            f'<text x="{x:.1f}" y="56" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="10" fill="#647064">{calendar.month_abbr[item.date.month]}</text>'
        )

    for weekday, label in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        y = top + weekday * row_step + 7
        parts.append(
            f'<text x="15" y="{y:.1f}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="10" fill="#6f786f">{label}</text>'
        )

    for weekday in range(7):
        y = top + weekday * row_step + 19
        parts.append(
            f'<path d="M{left-4:.1f},{y:.1f} Q{width/2:.1f},{y+2:.1f} {width-right:.1f},{y:.1f}" stroke="#eee4c7" stroke-width="0.7" fill="none" opacity="0.65"/>'
        )

    for item in ordered:
        week_index = (_week_start(item.date) - first_week).days // 7
        weekday = item.date.weekday()
        x = left + week_index * col_step + col_step / 2
        baseline = top + weekday * row_step + 19
        parts.append(_plant_svg(plant_state(item.level), x, baseline))

    can_y = height - 91
    parts.extend(
        [
            '<g id="watering-can">',
            f'<path d="M42,{can_y+22} h34 q8,0 8,8 v22 q0,8 -8,8 h-34 z" fill="#6d9b83" stroke="#4e745f" stroke-width="2"/>',
            f'<path d="M48,{can_y+20} q10,-18 22,-2" fill="none" stroke="#4e745f" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M80,{can_y+30} L116,{can_y+10} L121,{can_y+17} L85,{can_y+42} Z" fill="#6d9b83" stroke="#4e745f" stroke-width="2"/>',
            f'<path d="M116,{can_y+10} q8,3 11,10" fill="none" stroke="#4e745f" stroke-width="4" stroke-linecap="round"/>',
            f'<path d="M124,{can_y+18} Q148,{can_y-8} 176,{can_y-44}" fill="none" stroke="#7cc9eb" stroke-width="2.2" stroke-linecap="round"/>',
            f'<path d="M126,{can_y+24} Q156,{can_y-2} 190,{can_y-38}" fill="none" stroke="#9bdcf4" stroke-width="1.8" stroke-linecap="round"/>',
            f'<circle cx="176" cy="{can_y-44}" r="2.5" fill="#7cc9eb"/><circle cx="190" cy="{can_y-38}" r="2" fill="#9bdcf4"/>',
            '</g>',
        ]
    )

    legend_y = height - 25
    legend_states = ["soil", "seed", "sprout", "leafy", "millet"]
    parts.append(
        f'<text x="{width-188}" y="{legend_y+3}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" fill="#6f786f">Less</text>'
    )
    for i, state in enumerate(legend_states):
        x = width - 142 + i * 25
        parts.append(_plant_svg(state, x, legend_y + 3))
    parts.append(
        f'<text x="{width-12}" y="{legend_y+3}" text-anchor="end" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" fill="#6f786f">More</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def sky_mode(now: datetime) -> Literal["day", "night"]:
    local = now.astimezone(LONDON) if now.tzinfo is not None else now.replace(tzinfo=LONDON)
    return "day" if 6 <= local.hour < 18 else "night"


def _cloud(x: float, y: float, scale: float, fill: str, opacity: float = 1.0) -> str:
    return (
        f'<g data-cloud="sky-cloud" opacity="{opacity:.2f}" transform="translate({x:.1f} {y:.1f}) scale({scale:.2f})">'
        f'<ellipse cx="0" cy="14" rx="34" ry="16" fill="{fill}"/>'
        f'<circle cx="-20" cy="6" r="18" fill="{fill}"/>'
        f'<circle cx="2" cy="0" r="24" fill="{fill}"/>'
        f'<circle cx="24" cy="8" r="18" fill="{fill}"/>'
        '</g>'
    )


def render_sky_svg(now: datetime, width: int = 1200, height: int = 320) -> str:
    mode = sky_mode(now)
    day = mode == "day"
    bg_top = "#eaf7ff" if day else "#13233f"
    bg_bottom = "#fffdf3" if day else "#263a59"
    grass = "#8fbd62" if day else "#48634b"
    parts = [
        _svg_header(width, height, f"{mode} sky"),
        f'<defs><linearGradient id="sky-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg_top}"/><stop offset="1" stop-color="{bg_bottom}"/></linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="20" fill="url(#sky-bg)"/>',
    ]

    if day:
        parts.extend(
            [
                '<g id="sky-sun">',
                '<circle cx="980" cy="86" r="52" fill="#f7c84a" opacity="0.20"/>',
                '<circle cx="980" cy="86" r="38" fill="#f8c84e"/>',
                '</g>',
                _cloud(170, 125, 1.1, "#ffffff", 0.90),
                _cloud(470, 105, 0.78, "#ffffff", 0.78),
                _cloud(1080, 155, 0.92, "#ffffff", 0.84),
            ]
        )
    else:
        parts.extend(
            [
                '<g id="sky-moon"><circle cx="980" cy="86" r="40" fill="#f2efcf"/><circle cx="998" cy="72" r="40" fill="#182a49" opacity="0.92"/></g>',
                _cloud(180, 138, 1.0, "#d8e2ef", 0.24),
                _cloud(535, 112, 0.72, "#d8e2ef", 0.18),
                _cloud(1080, 158, 0.88, "#d8e2ef", 0.20),
            ]
        )
        for x, y, r in ((120, 62, 1.8), (260, 84, 1.3), (380, 52, 1.4), (610, 72, 1.2), (730, 42, 1.5), (860, 112, 1.1), (1110, 58, 1.4)):
            parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#f5f0cf" opacity="0.88"/>')

    breeze = "#ffffff" if day else "#adc4d6"
    parts.extend(
        [
            f'<path d="M160,150 C260,120 310,180 420,148 C500,124 560,130 620,150" fill="none" stroke="{breeze}" stroke-width="3" opacity="0.62" stroke-linecap="round"/>',
            f'<path d="M210,178 C300,150 355,198 470,170" fill="none" stroke="{breeze}" stroke-width="2" opacity="0.45" stroke-linecap="round"/>',
            f'<path d="M0,{height-44} C170,{height-80} 340,{height-28} 520,{height-52} C720,{height-78} 930,{height-26} {width},{height-54} L{width},{height} L0,{height} Z" fill="{grass}" opacity="0.42"/>',
            f'<path d="M0,{height-28} C210,{height-60} 410,{height-20} 615,{height-40} C815,{height-58} 1000,{height-22} {width},{height-38} L{width},{height} L0,{height} Z" fill="{grass}" opacity="0.66"/>',
        ]
    )

    leaf_color = "#7cab55" if day else "#6f8a72"
    for x, y, rot in ((260, 72, -24), (370, 118, 18), (720, 92, -30), (840, 142, 12), (1100, 98, -18)):
        parts.append(_leaf(x, y, 8, 3.6, rot, leaf_color))

    flower_color = "#f2c85d" if day else "#c8b870"
    for x in (55, 88, 112, 1040, 1080, 1130):
        base = height - 33 - (x % 3) * 4
        parts.append(f'<path d="M{x},{height-21} L{x},{base}" stroke="#6d9b59" stroke-width="1.4"/>')
        parts.append(f'<circle cx="{x}" cy="{base}" r="3.3" fill="{flower_color}"/>')

    parts.append("</svg>")
    return "".join(parts)


def render_activity_summary_svg(
    metrics: ContributionMetrics, month_label: str, width: int = 300, height: int = 240
) -> str:
    rows = [
        (f"{metrics.active_days_month} active days", "this month"),
        (f"{metrics.current_streak} day streak", "current run"),
        (f"{metrics.harvest_days_month} harvest days", "high activity"),
        (f"{metrics.active_days_year} active days this year", "year to date"),
    ]
    parts = [
        _svg_header(width, height, "Privacy-safe contribution activity summary"),
        '<rect width="300" height="240" rx="18" fill="#fbfdf9"/>',
        '<text x="18" y="28" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="15" font-weight="650" fill="#2a4e31">Contribution activity</text>',
        f'<text x="18" y="48" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="10" fill="#7a857b">{html.escape(month_label)}</text>',
    ]
    y = 78
    for index, (primary, secondary) in enumerate(rows):
        icon_y = y - 4
        parts.append(f'<circle cx="26" cy="{icon_y}" r="7" fill="#eaf5df"/>')
        parts.append(_leaf(26, icon_y, 4.3, 2.0, -24 if index % 2 == 0 else 24, "#71a84c"))
        parts.append(
            f'<text x="45" y="{y}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12" font-weight="600" fill="#324836">{html.escape(primary)}</text>'
        )
        parts.append(
            f'<text x="45" y="{y+15}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" fill="#7b847d">{html.escape(secondary)}</text>'
        )
        y += 42
    parts.append("</svg>")
    return "".join(parts)


def _atomic_write_many(output_dir: Path, files: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for name, content in files.items():
            fd, temp_name = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=output_dir)
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
            staged.append((temp_path, output_dir / name))
        for temp_path, target in staged:
            os.replace(temp_path, target)
    finally:
        for temp_path, _ in staged:
            if temp_path.exists():
                temp_path.unlink()


def _parse_now(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(LONDON)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LONDON)
    return parsed.astimezone(LONDON)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Yshiboo's dynamic GitHub profile assets")
    parser.add_argument("--username", default="Yshiboo")
    parser.add_argument("--output-dir", default="assets")
    parser.add_argument("--contributions-html", type=Path)
    parser.add_argument("--now")
    args = parser.parse_args(argv)

    now = _parse_now(args.now)
    today = now.date()
    if args.contributions_html:
        source = args.contributions_html.read_text(encoding="utf-8")
    else:
        source = fetch_contribution_html(args.username, today - timedelta(days=364), today)

    days = parse_contribution_html(source)
    metrics = summarize_contributions(days, today)
    assets = {
        "sky.svg": render_sky_svg(now),
        "garden.svg": render_garden_svg(days),
        "activity-summary.svg": render_activity_summary_svg(
            metrics, now.strftime("%B %Y")
        ),
    }
    _atomic_write_many(Path(args.output_dir), assets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
