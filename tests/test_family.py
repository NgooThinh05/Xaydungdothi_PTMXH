import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "extraction"))
from family import family_relation  # noqa: E402


class FamilyTest(unittest.TestCase):
    def test_parent_direction(self):
        self.assertEqual(family_relation("child", "parent", " là con gái của "),
                         ("parent", "PARENT_OF", "child"))
        self.assertEqual(family_relation("parent", "child", " là mẹ của "),
                         ("parent", "PARENT_OF", "child"))

    def test_unstated_relationship_is_not_inferred(self):
        self.assertIsNone(family_relation("a", "b", " cùng tham dự với "))


if __name__ == "__main__":
    unittest.main()
