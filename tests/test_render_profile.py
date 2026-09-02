from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from scripts.render_profile import (
    ContributionDay,
    ContributionMetrics,
    main,
    parse_contribution_html,
    plant_state,
    render_activity_summary_svg,
    render_garden_svg,
    render_sky_svg,
    sky_mode,
    summarize_contributions,
)

FIXTURE = Path("tests/fixtures/contributions.html")
LONDON = ZoneInfo("Europe/London")


class RenderProfileTests(unittest.TestCase):
    def test_parse_contribution_html_reads_date_and_level(self):
        days = parse_contribution_html(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            days,
            [
                ContributionDay(date(2026, 8, 30), 0),
                ContributionDay(date(2026, 8, 31), 1),
                ContributionDay(date(2026, 9, 1), 3),
                ContributionDay(date(2026, 9, 2), 4),
            ],
        )

    def test_parse_contribution_html_rejects_empty_calendar(self):
        with self.assertRaisesRegex(ValueError, "contribution calendar"):
            parse_contribution_html("<html></html>")

    def test_plant_state_maps_github_levels(self):
        self.assertEqual(
            [plant_state(i) for i in range(5)],
            ["soil", "seed", "sprout", "leafy", "millet"],
        )

    def test_summarize_contributions_uses_real_levels(self):
        days = [
            ContributionDay(date(2026, 8, 31), 1),
            ContributionDay(date(2026, 9, 1), 3),
            ContributionDay(date(2026, 9, 2), 4),
        ]
        metrics = summarize_contributions(days, date(2026, 9, 2))
        self.assertEqual(metrics.active_days_month, 2)
        self.assertEqual(metrics.current_streak, 3)
        self.assertEqual(metrics.harvest_days_month, 1)
        self.assertEqual(metrics.active_days_year, 3)

    def test_garden_svg_contains_month_and_weekday_labels(self):
        svg = render_garden_svg([
            ContributionDay(date(2026, 8, 31), 1),
            ContributionDay(date(2026, 9, 1), 3),
            ContributionDay(date(2026, 9, 2), 4),
        ])
        self.assertIn("<svg", svg)
        self.assertIn("Sep", svg)
        self.assertIn("Mon", svg)
        self.assertIn("Wed", svg)
        self.assertIn("Fri", svg)

    def test_garden_svg_renders_distinct_growth_states(self):
        svg = render_garden_svg([
            ContributionDay(date(2026, 8, 30), 0),
            ContributionDay(date(2026, 8, 31), 1),
            ContributionDay(date(2026, 9, 1), 2),
            ContributionDay(date(2026, 9, 2), 3),
            ContributionDay(date(2026, 9, 3), 4),
        ])
        for marker in [
            "state-soil",
            "state-seed",
            "state-sprout",
            "state-leafy",
            "state-millet",
        ]:
            self.assertIn(marker, svg)

    def test_garden_svg_is_deterministic(self):
        days = [ContributionDay(date(2026, 9, 2), 4)]
        self.assertEqual(render_garden_svg(days), render_garden_svg(days))

    def test_sky_mode_switches_at_six(self):
        self.assertEqual(sky_mode(datetime(2026, 9, 2, 5, 59, tzinfo=LONDON)), "night")
        self.assertEqual(sky_mode(datetime(2026, 9, 2, 6, 0, tzinfo=LONDON)), "day")
        self.assertEqual(sky_mode(datetime(2026, 9, 2, 17, 59, tzinfo=LONDON)), "day")
        self.assertEqual(sky_mode(datetime(2026, 9, 2, 18, 0, tzinfo=LONDON)), "night")

    def test_day_sky_has_sun_and_clouds(self):
        svg = render_sky_svg(datetime(2026, 9, 2, 12, 0, tzinfo=LONDON))
        self.assertIn("sky-sun", svg)
        self.assertIn("sky-cloud", svg)
        self.assertNotIn("sky-moon", svg)

    def test_night_sky_has_moon(self):
        svg = render_sky_svg(datetime(2026, 9, 2, 23, 0, tzinfo=LONDON))
        self.assertIn("sky-moon", svg)
        self.assertNotIn("sky-sun", svg)

    def test_activity_summary_uses_metrics_without_private_metadata(self):
        metrics = ContributionMetrics(
            active_days_month=12,
            current_streak=4,
            harvest_days_month=3,
            active_days_year=91,
        )
        svg = render_activity_summary_svg(metrics, "September 2026")
        self.assertIn("12 active days", svg)
        self.assertIn("4 day streak", svg)
        self.assertIn("3 harvest days", svg)
        self.assertIn("91 active days this year", svg)
        self.assertNotIn("commit", svg.lower())
        self.assertNotIn("pull request", svg.lower())

    def test_cli_writes_all_assets_to_temp_directory(self):
        with TemporaryDirectory() as tmp:
            exit_code = main([
                "--contributions-html", str(FIXTURE),
                "--now", "2026-09-02T12:00:00+01:00",
                "--output-dir", tmp,
            ])
            self.assertEqual(exit_code, 0)
            output = Path(tmp)
            self.assertTrue((output / "sky.svg").exists())
            self.assertTrue((output / "garden.svg").exists())
            self.assertTrue((output / "activity-summary.svg").exists())


if __name__ == "__main__":
    unittest.main()
