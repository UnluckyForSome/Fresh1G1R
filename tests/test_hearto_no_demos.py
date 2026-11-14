import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_filters(name: str):
    path = ROOT / "config" / name / "filters.py"
    spec = importlib.util.spec_from_file_location(f"filters_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HeartoNoDemosTests(unittest.TestCase):
    def test_drops_demos_and_keeps_the_rest_of_hearto(self):
        hearto = load_filters("Hearto")
        variant = load_filters("Hearto-NoDemos")

        self.assertEqual(variant.flags, hearto.flags)
        self.assertEqual(set(variant.exclude), set(hearto.exclude + "d"))
        self.assertEqual(variant.exclude.count("d"), 1)
        self.assertNotIn("D", variant.exclude)

    def test_uses_heartos_retool_user_config(self):
        hearto = (ROOT / "config" / "Hearto" / "user-config.yaml").read_bytes()
        variant = (ROOT / "config" / "Hearto-NoDemos" / "user-config.yaml").read_bytes()

        self.assertEqual(variant, hearto)


if __name__ == "__main__":
    unittest.main()
