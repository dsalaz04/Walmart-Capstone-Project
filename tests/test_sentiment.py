"""Offline tests for the sentiment pipeline. Run: python -m unittest discover -s tests"""

import tempfile
import unittest
from pathlib import Path

import reddit_sentiment as rs
from common_word_finder import count_words
from data import CATALYSTS, LEXICON

REPO = Path(__file__).resolve().parent.parent


class FindTopicsTest(unittest.TestCase):
    def test_counts_catalyst_mentions(self):
        comments = [(None, "My manager cut my hours"),
                    (None, "The pay is too low and my manager knows it"),
                    (None, "Nothing topical here")]
        counts, by_topic = rs.find_topics(comments)
        self.assertEqual(counts["manager"], 2)
        self.assertEqual(counts["pay"], 1)
        self.assertEqual(len(by_topic["manager"]), 2)

    def test_matching_ignores_case_and_punctuation(self):
        counts, _ = rs.find_topics([(None, "PAY! Pay, pay...")])
        self.assertEqual(counts["pay"], 1)  # once per comment, however many mentions

    def test_author_counted_once_per_topic(self):
        comments = [("alice", "the pay here"), ("alice", "pay pay pay"),
                    ("bob", "pay is fine")]
        counts, _ = rs.find_topics(comments)
        self.assertEqual(counts["pay"], 2)  # alice once + bob once

    def test_token_variants_merge_into_canonical_topic(self):
        comments = [(None, "the wage is low"), (None, "wages went up"),
                    (None, "pay day"), (None, "we should unionize")]
        counts, by_topic = rs.find_topics(comments)
        self.assertEqual(counts["pay"], 3)        # wage + wages + pay, one topic
        self.assertEqual(len(by_topic["pay"]), 3)
        self.assertNotIn("wage", counts)
        self.assertNotIn("wages", counts)
        self.assertEqual(counts["union"], 1)      # unionize -> union
        self.assertNotIn("unionize", counts)

    def test_variant_and_canonical_in_one_comment_count_once(self):
        counts, _ = rs.find_topics([(None, "the wage... what a pay cut")])
        self.assertEqual(counts["pay"], 1)

    def test_anonymous_comments_all_count(self):
        comments = [(None, "the pay"), (None, "the pay")]
        counts, _ = rs.find_topics(comments)
        self.assertEqual(counts["pay"], 2)


class ScoreTopicsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = rs.make_analyzer()

    def score(self, by_topic, topics):
        return rs.score_topics(by_topic, topics, analyzer=self.analyzer)

    def test_positive_vs_negative_comments(self):
        by_topic = {
            "pay": ["I love the new raise, it's wonderful and generous!"],
            "manager": ["My manager is awful, I hate this, it's terrible."],
        }
        scores = self.score(by_topic, ["pay", "manager"])
        self.assertGreater(scores.loc["pay", "Positive"],
                           scores.loc["pay", "Negative"])
        self.assertGreater(scores.loc["manager", "Negative"],
                           scores.loc["manager", "Positive"])

    def test_walmart_lexicon_overrides_apply(self):
        # "coached" is neutral English but a disciplinary action at Walmart.
        self.assertIn("coached", LEXICON)
        scores = self.score({"coach": ["I got coached today"]}, ["coach"])
        self.assertGreater(scores.loc["coach", "Negative"], 0.2)

    def test_negation_is_understood(self):
        # The original scored word-by-word, which loses negation entirely.
        good = self.score({"pay": ["The pay is good"]}, ["pay"])
        negated = self.score({"pay": ["The pay is not good at all"]}, ["pay"])
        self.assertGreater(good.loc["pay", "Positive"],
                           negated.loc["pay", "Positive"])

    def test_emoji_do_not_crash_scoring(self):
        scores = self.score({"pay": ["pay day 🤑🤑🤑 finally"]}, ["pay"])
        self.assertFalse(scores.isnull().values.any())

    def test_rows_sum_to_roughly_one(self):
        scores = self.score({"pay": ["The pay is good", "pay is bad"]}, ["pay"])
        proportions = scores.loc["pay", ["Negative", "Neutral", "Positive"]]
        self.assertAlmostEqual(float(proportions.sum()), 1.0, places=2)

    def test_compound_column_summarizes_net_sentiment(self):
        by_topic = {
            "pay": ["I love the new raise, it's wonderful and generous!"],
            "manager": ["My manager is awful, I hate this, it's terrible."],
        }
        scores = self.score(by_topic, ["pay", "manager"])
        self.assertIn("Compound", scores.columns)
        self.assertGreater(scores.loc["pay", "Compound"], 0)
        self.assertLess(scores.loc["manager", "Compound"], 0)


class CsvAndEndToEndTest(unittest.TestCase):
    def test_load_sample_csv(self):
        comments = rs.load_csv(REPO / "sample_comments.csv")
        self.assertGreater(len(comments), 10)
        self.assertTrue(all(body for _, body in comments))

    def test_count_words_respects_blacklist(self):
        counts = count_words([(None, "the the the manager manager pay")])
        self.assertNotIn("the", counts)
        self.assertEqual(counts["manager"], 2)

    def test_cli_offline_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = rs.main(["--input", str(REPO / "sample_comments.csv"),
                            "--save", tmp, "--analyze", "3"])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "topics.png").exists())
            self.assertTrue((Path(tmp) / "sentiment.png").exists())

    def test_catalysts_are_unique_lowercase_matchable(self):
        lowered = [c.lower() for c in CATALYSTS]
        self.assertEqual(len(lowered), len(set(lowered)))


if __name__ == "__main__":
    unittest.main()
