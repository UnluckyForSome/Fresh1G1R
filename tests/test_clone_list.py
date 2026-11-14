import tempfile
import unittest
from pathlib import Path

import automate

REDUMP_PSP_CLONE_LIST = "Sony - PlayStation Portable (Redump).json"
PSN_DECRYPTED = Path(
    "Sony - PlayStation Portable (PSN) (Decrypted) (20251223-124222).dat"
)


class CloneListOverrideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.retool_dir = Path(self.tmp.name)
        clone_lists = self.retool_dir / "clonelists"
        clone_lists.mkdir()
        (clone_lists / REDUMP_PSP_CLONE_LIST).write_text("{}", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def clone_list_arg(self):
        return ["--clonelist", str(self.retool_dir / "clonelists" / REDUMP_PSP_CLONE_LIST)]

    def test_no_intro_psp_psn_decrypted_uses_the_redump_psp_clone_list(self):
        args = automate.extra_retool_args(PSN_DECRYPTED, "no-intro", self.retool_dir)

        self.assertEqual(args, self.clone_list_arg())

    def test_no_intro_psp_psn_encrypted_uses_the_redump_psp_clone_list(self):
        dat = Path("Sony - PlayStation Portable (PSN) (Encrypted) (20251223-124222).dat")

        self.assertEqual(
            automate.extra_retool_args(dat, "no-intro", self.retool_dir),
            self.clone_list_arg(),
        )

    def test_psp_psn_minis_are_not_given_the_redump_disc_list(self):
        dat = Path(
            "Sony - PlayStation Portable (PSN) (Minis) (Decrypted) (20251222-175857).dat"
        )

        self.assertEqual(automate.extra_retool_args(dat, "no-intro", self.retool_dir), [])

    def test_redump_psp_is_left_for_retool_to_match_by_name(self):
        dat = Path(
            "Sony - PlayStation Portable - Datfile (3455) (2026-02-21 19-24-23).dat"
        )

        self.assertEqual(automate.extra_retool_args(dat, "redump", self.retool_dir), [])

    def test_other_no_intro_systems_are_unchanged(self):
        dat = Path("Nintendo - Game Boy (20231029-220453).dat")

        self.assertEqual(automate.extra_retool_args(dat, "no-intro", self.retool_dir), [])

    def test_missing_clone_list_is_not_passed_to_retool(self):
        (self.retool_dir / "clonelists" / REDUMP_PSP_CLONE_LIST).unlink()

        self.assertEqual(
            automate.extra_retool_args(PSN_DECRYPTED, "no-intro", self.retool_dir),
            [],
        )


if __name__ == "__main__":
    unittest.main()
