import tempfile
import unittest
import zipfile
from pathlib import Path

import release

DAT = """<?xml version="1.0"?>
<datafile>
\t<header>
\t\t<name>Nintendo - Game Boy (Retool)</name>
\t\t<date>{date}</date>
\t</header>
\t<game name="{game}"/>
</datafile>
"""


def write_dat(path: Path, game: str = "Tetris (World)", date: str = "2026-11-21 09-40-58") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DAT.format(game=game, date=date), encoding="utf-8")


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "config" / "Hearto-NoDemos").mkdir(parents=True)
        write_dat(self.root / "daily-1g1r-dat" / "Hearto-NoDemos" / "no-intro"
                  / "Nintendo - Game Boy (No-Intro - Fresh1G1R - Hearto-NoDemos).dat")
        write_dat(self.root / "daily-virgin-dat" / "redump"
                  / "Sega - Dreamcast - Datfile (1519) (2026-11-15 16-33-57).dat")
        report = self.root / "report" / "Hearto-NoDemos" / "no-intro" / "Nintendo - Game Boy report.txt"
        report.parent.mkdir(parents=True)
        report.write_text("report", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_asset_names_map_back_to_their_folders(self):
        for asset_name, folder in release.dat_folders(self.root).items():
            self.assertEqual(release.folder_for_asset(asset_name, self.root), folder)

    def test_reports_and_removed_configs_are_not_unpacked(self):
        self.assertIsNone(release.folder_for_asset("Fresh1G1R-Reports.zip", self.root))
        self.assertIsNone(release.folder_for_asset("Fresh1G1R-Retired-Redump.zip", self.root))

    def test_pack_then_unpack_restores_the_same_dats(self):
        dist = Path(self.tmp.name) / "dist"
        names = sorted(path.name for path in release.pack(dist, self.root))
        self.assertEqual(names, [
            "Fresh1G1R-Hearto-NoDemos-No-Intro.zip",
            "Fresh1G1R-Original-Redump.zip",
            "Fresh1G1R-Reports.zip",
        ])

        restored = Path(self.tmp.name) / "restored"
        (restored / "config" / "Hearto-NoDemos").mkdir(parents=True)
        release.unpack(dist, restored)
        self.assertEqual(release.build_manifest(restored), release.build_manifest(self.root))

    def test_unpack_rejects_paths_inside_the_zip(self):
        source = Path(self.tmp.name) / "evil"
        source.mkdir()
        with zipfile.ZipFile(source / "Fresh1G1R-Original-Redump.zip", "w") as zf:
            zf.writestr("../escape.dat", "x")
        with self.assertRaises(ValueError):
            release.unpack(source, self.root)

    def test_a_new_retool_run_date_alone_is_not_a_change(self):
        old = release.build_manifest(self.root)
        write_dat(self.root / "daily-1g1r-dat" / "Hearto-NoDemos" / "no-intro"
                  / "Nintendo - Game Boy (No-Intro - Fresh1G1R - Hearto-NoDemos).dat",
                  date="2026-11-22 09-12-00")
        changed, _ = release.compare(old, release.build_manifest(self.root))
        self.assertFalse(changed)

    def test_an_updated_source_dat_counts_as_updated_not_added(self):
        old = release.build_manifest(self.root)
        folder = self.root / "daily-virgin-dat" / "redump"
        (folder / "Sega - Dreamcast - Datfile (1519) (2026-11-15 16-33-57).dat").unlink()
        write_dat(folder / "Sega - Dreamcast - Datfile (1520) (2026-11-22 08-00-00).dat", game="Shenmue (Europe)")

        changed, notes = release.compare(old, release.build_manifest(self.root))
        self.assertTrue(changed)
        self.assertIn("**Original-Redump**\n- Updated (1): Sega - Dreamcast", notes)

    def test_first_release_has_no_previous_manifest(self):
        changed, _ = release.compare(None, release.build_manifest(self.root))
        self.assertTrue(changed)


if __name__ == "__main__":
    unittest.main()
