import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "extraction"))
import relations  # noqa: E402
from ner_link import DocContext, Linker, analyse_sentence  # noqa: E402


class RelationsPipelineTest(unittest.TestCase):
    def test_entity_boundary_and_noise_filtering(self):
        lk = Linker()
        ctx = DocContext()

        # 1. Anonymized crime/legal name should not be recognized
        s1 = "Bà Nguyễn Thị L, ở Phú Thọ, là một trường hợp bị hại."
        m1 = [m for m in analyse_sentence(s1, lk, ctx) if m.kind == "PER"]
        self.assertEqual(len(m1), 0)

        # 2. Foreign name preceded by continent / country should not be matched as Vietnamese surname
        s2 = "Chủ tịch Hội đồng châu Âu Antonio Costa đã phát biểu."
        m2 = [m for m in analyse_sentence(s2, lk, ctx) if m.kind == "PER"]
        self.assertEqual(len(m2), 0)

        # 3. Historical leader should not be created as new news politician
        s3 = "Kỷ niệm 135 năm Ngày sinh Chủ tịch Hồ Chí Minh tại địa phương."
        m3 = [m for m in analyse_sentence(s3, lk, ctx) if m.kind == "PER" and m.id.startswith("per:news:")]
        self.assertEqual(len(m3), 0)

        # 4. Lowercase typo recovery on existing politician
        s4 = "Bí thư Tỉnh ủy Quảng Ngãi Hồ Văn niên cho rằng cần phát huy."
        m4 = [m for m in analyse_sentence(s4, lk, ctx) if m.kind == "PER"]
        self.assertTrue(any(m.id == "per:ho_van_nien" for m in m4))

        # 5. Incomplete 2-syllable name ending in 'Thị' should be rejected
        s5 = "Bí thư Bùi Thị phát biểu khai mạc."
        m5 = [m for m in analyse_sentence(s5, lk, ctx) if m.kind == "PER"]
        self.assertEqual(len(m5), 0)

    def test_empty_relations_still_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interim, processed, evaluation = (root / x for x in ("interim", "processed", "eval"))
            for directory in (interim, processed, evaluation):
                directory.mkdir()
            (interim / "news_docs.jsonl").write_text(json.dumps({
                "doc_id": "one", "url": "https://example.com/one", "date": "2026-11-10",
                "sents": ["Thứ trưởng Nguyễn Văn Ánh phát biểu tại hội nghị."],
            }, ensure_ascii=False) + "\n", encoding="utf-8")
            with patch.object(relations, "INTERIM", interim), patch.object(relations, "PROC", processed), patch.object(relations, "EVAL", evaluation):
                relations.main()
            self.assertTrue((processed / "nodes_person_news.csv").exists())
            self.assertTrue((processed / "person_mentions_news.csv").exists())
            self.assertTrue((processed / "edges_news.csv").exists())
            self.assertIn("Nguyễn Văn Ánh", (processed / "nodes_person_news.csv").read_text(encoding="utf-8"))
            self.assertIn("Nguyễn Văn Ánh", (processed / "person_mentions_news.csv").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
