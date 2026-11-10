import unittest

from extraction.event_identity import assertion_id, explicit_event_date


class EventIdentityTest(unittest.TestCase):
    def test_explicit_date_is_not_publication_date(self):
        self.assertEqual(explicit_event_date("Quyết định ngày 5 tháng 11 năm 2026"), "2026-11-05")
        self.assertEqual(explicit_event_date("Quyết định ngày 31/02/2026"), "")
        self.assertEqual(explicit_event_date("Ông A được bổ nhiệm."), "")

    def test_same_pair_in_two_sentences_remains_distinct(self):
        first = assertion_id("article", 2, "BO_NHIEM", "org:a", "per:b", "bổ nhiệm")
        repeated = assertion_id("article", 2, "BO_NHIEM", "org:a", "per:b", "bổ nhiệm")
        second = assertion_id("article", 5, "BO_NHIEM", "org:a", "per:b", "bổ nhiệm")
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
