import unittest

from gazetteer.enrich_wiki import _parse_infobox_details


class WikiCandidateTest(unittest.TestCase):
    def test_birth_place_and_hometown_are_distinct(self):
        details = _parse_infobox_details("{{Thông tin viên chức\n| ngày sinh = 1 tháng 1 năm 1960\n| nơi sinh = Hà Nội\n| quê quán = Nam Định\n}}")
        self.assertEqual(details["birth_place"], "Hà Nội")
        self.assertEqual(details["hometown"], "Nam Định")


if __name__ == "__main__":
    unittest.main()
