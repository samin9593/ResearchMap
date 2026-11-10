import tempfile
import unittest
from pathlib import Path

import pandas as pd

from analyzer import analyze_papers, load_papers


class ResearchMapTests(unittest.TestCase):
    def read_csv(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "papers.csv"
            path.write_text(content, encoding="utf-8")
            return load_papers(path)

    def test_import_accepts_blank_abstract_and_year(self):
        papers = self.read_csv("\ufeff Title ,abstract,YEAR\n Urban shade ,,\n")
        self.assertEqual(papers.iloc[0].tolist(), ["Urban shade", "", ""])
        result = analyze_papers(papers)
        self.assertEqual(set(result.keywords["keyword"]), {"urban", "shade"})
        self.assertIsNone(result.average_similarity)
        self.assertTrue(result.related_papers(0).empty)

    def test_bad_csv_is_rejected(self):
        examples = [
            ("", "empty"),
            ("title,abstract,year\n", "no paper"),
            ("title,year\nShade,2024\n", "Missing"),
            ("title,abstract,year\n,An abstract,2024\n", "needs a title"),
            ("title,abstract,year\nShade,,unknown\n", "four-digit"),
            ('title,abstract,year\nShade,"unfinished\n', "parsed"),
            ("title,abstract,year\nShade,Text,2024,extra\n", "parsed"),
            ("title,abstract,year,TITLE\nShade,Text,2024,Shade\n", "unique"),
            ("title,abstract,year\nShade,Text,2024\nRain,,2025,extra\n", "parsed"),
        ]
        for content, message in examples:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.read_csv(content)

    def test_keyword_scores_and_cosine_similarity(self):
        papers = self.read_csv(
            "title,abstract,year\nUrban shade,canopy,2024\n"
            "Urban shade,canopy,2023\nWetland birds,habitat,2022\n"
        )
        result = analyze_papers(papers)
        self.assertEqual(result.keywords.iloc[0]["keyword"], "canopy")
        self.assertAlmostEqual(result.keywords.iloc[0]["mean_tfidf"], 2 / (3 * 3**0.5))
        self.assertAlmostEqual(result.similarity.iat[0, 1], 1)
        self.assertAlmostEqual(result.similarity.iat[0, 2], 0)
        self.assertAlmostEqual(result.average_similarity, 1 / 3)
        self.assertEqual(result.related_papers(0).index.tolist(), [1, 2])

    def test_empty_vocabulary_returns_unavailable_analysis(self):
        papers = self.read_csv("title,abstract,year\nThe and of,,\n")
        result = analyze_papers(papers)
        self.assertTrue(result.keywords.empty)
        self.assertIsNone(result.similarity)
        self.assertIsNone(result.average_similarity)

    def test_papers_with_no_terms_are_excluded_from_comparisons(self):
        papers = self.read_csv("title,abstract,year\nThe,,\nCanopy,,\nCanopy,,\n")
        result = analyze_papers(papers)
        self.assertTrue(pd.isna(result.similarity.iat[0, 1]))
        self.assertAlmostEqual(result.average_similarity, 1)
        self.assertTrue(result.related_papers(0).empty)
        self.assertEqual(result.related_papers(1).index.tolist(), [2])

    def test_bundled_sample_loads(self):
        sample = Path(__file__).with_name("data") / "sample_papers.csv"
        papers = load_papers(sample)
        self.assertEqual(len(papers), 16)
        self.assertGreater(len(analyze_papers(papers).keywords), 10)


if __name__ == "__main__":
    unittest.main()
